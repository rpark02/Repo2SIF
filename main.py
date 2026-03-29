#!/usr/bin/env python3
"""Repo2SIF: convert repo to Docker image, save as tar, optionally convert to SIF.

This tool is typically invoked from within a Docker container. The wrapper script (repo2sif)
uses docker create/cp/start to:
- Clone Git URLs (GitHub, GitLab, etc.) on the host, then copy to /work in the container
- Copy local repos to /work in the container
- Copy output files from /out back to the host
"""

from __future__ import annotations

from pathlib import Path
import argparse
import logging
import subprocess
import sys
import re
import time


DEFAULT_OUTDIR = Path("/out")
DEFAULT_IMAGE_TAG = "repo2sif-image:latest"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("repo2sif")


def _is_url(path: str) -> bool:
    """Check if the path is a URL (http/https/git)."""
    return bool(re.match(r'^(https?|git)://', path)) or path.startswith('git@')


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    log.info("Running: %s", " ".join(cmd))
    try:
        subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)
    except subprocess.CalledProcessError as e:
        log.error("Command failed (exit code %d): %s", e.returncode, " ".join(cmd))
        raise
    except FileNotFoundError:
        log.error("Command not found: %s", cmd[0])
        raise


def _fmt_elapsed(seconds: float) -> str:
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


def main():
    parser = argparse.ArgumentParser(
        description="Convert a repository to a Docker image, save as tar, optionally convert to SIF"
    )
    parser.add_argument("repo_path", help="Path to the repository to convert (local path or URL)")
    parser.add_argument(
        "--output", "-o", type=Path, default=DEFAULT_OUTDIR,
        help="Output directory for tar and sif files"
    )
    parser.add_argument(
        "--tag", "-t", default=DEFAULT_IMAGE_TAG,
        help="Docker image tag to use"
    )
    parser.add_argument(
        "--name", "-n",
        help="Name for output files (without extension). If not specified, uses image tag"
    )
    parser.add_argument(
        "--sif", action="store_true",
        help="Also produce a .sif file (requires running container with --privileged)"
    )
    
    args = parser.parse_args()
    repo_path_str = args.repo_path
    
    # Validate repository path/URL
    # Note: When invoked by the wrapper script, URLs are cloned on the host first,
    # then copied to /work. This URL handling is mainly for direct invocations.
    if _is_url(repo_path_str):
        # URL - repo2sif will handle cloning (for direct invocations)
        repo_path = repo_path_str
    else:
        # Local path - validate it exists (could be /work if copied by wrapper, or a direct path)
        repo_path = Path(repo_path_str)
        if not repo_path.exists():
            log.error("Repository path does not exist: %s", repo_path)
            sys.exit(1)
        if not repo_path.is_dir():
            log.error("Repository path is not a directory: %s", repo_path)
            sys.exit(1)
        repo_path = str(repo_path)
    
    args.output.mkdir(parents=True, exist_ok=True)

    # Generate unique name from repository if not provided
    if args.name:
        output_name = args.name
        image_tag = f"repo2sif-{output_name.lower()}:latest"
    else:
        if _is_url(repo_path_str):
            match = re.search(r'/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_path_str)
            if match:
                output_name = f"{match.group(1)}-{match.group(2)}"
            else:
                output_name = re.sub(r'[^a-zA-Z0-9-]', '-', repo_path_str).strip('-')[:50]
        else:
            repo_path_obj = Path(repo_path_str)
            output_name = repo_path_obj.name or "repo"
        
        output_name = re.sub(r'[^a-zA-Z0-9._-]', '-', output_name).strip('-')
        if not output_name:
            output_name = "repo"
        
        image_tag = f"repo2sif-{output_name.lower()}:latest"

    total_start = time.monotonic()
    
    # Build image using jupyter-repo2docker CLI
    log.info("Building Docker image from %s...", repo_path)
    step_start = time.monotonic()
    _run([
        "jupyter-repo2docker",
        "--no-run",
        "--image-name", image_tag,
        "--user-name", "r2d",
        "--user-id", "1000",
        "--target-repo-dir", "/repo2sif_dir",
        repo_path,
    ])
    log.info("Docker image built in %s", _fmt_elapsed(time.monotonic() - step_start))
    
    # Save Docker image to tar
    tar_path = args.output / f"{output_name}.tar"
    log.info("Saving Docker image to %s...", tar_path)
    step_start = time.monotonic()
    _run(["docker", "save", image_tag, "-o", str(tar_path)])
    log.info("Tar saved in %s: %s", _fmt_elapsed(time.monotonic() - step_start), tar_path)

    # Optionally convert to SIF
    if args.sif:
        sif_path = args.output / f"{output_name}.sif"
        log.info("Converting to SIF format: %s...", sif_path)
        step_start = time.monotonic()
        try:
            _run(["apptainer", "build", str(sif_path), f"docker-daemon://{image_tag}"])
        except (subprocess.CalledProcessError, FileNotFoundError):
            log.warning("docker-daemon transport failed, falling back to docker-archive")
            _run(["apptainer", "build", str(sif_path), f"docker-archive://{tar_path}"])
        log.info("SIF converted in %s: %s", _fmt_elapsed(time.monotonic() - step_start), sif_path)

    total_elapsed = time.monotonic() - total_start
    log.info("Done. Total time: %s", _fmt_elapsed(total_elapsed))


if __name__ == "__main__":
    main()
