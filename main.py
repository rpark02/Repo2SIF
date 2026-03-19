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
import subprocess
import sys
import re


DEFAULT_OUTDIR = Path("/out")
DEFAULT_IMAGE_TAG = "repo2sif-image:latest"


def _is_url(path: str) -> bool:
    """Check if the path is a URL (http/https/git)."""
    return bool(re.match(r'^(https?|git)://', path)) or path.startswith('git@')


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


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
            print(f"ERROR: Repository path does not exist: {repo_path}", file=sys.stderr)
            sys.exit(1)
        if not repo_path.is_dir():
            print(f"ERROR: Repository path is not a directory: {repo_path}", file=sys.stderr)
            sys.exit(1)
        repo_path = str(repo_path)
    
    args.output.mkdir(parents=True, exist_ok=True)

    # Generate unique name from repository if not provided
    if args.name:
        output_name = args.name
        # Use output name for image tag to ensure uniqueness
        image_tag = f"repo2sif-{output_name}:latest"
    else:
        # Auto-generate name from repository path
        if _is_url(repo_path_str):
            # Extract repo name from URL (e.g., github.com/user/repo -> user-repo)
            match = re.search(r'/([^/]+)/([^/]+?)(?:\.git)?/?$', repo_path_str)
            if match:
                output_name = f"{match.group(1)}-{match.group(2)}"
            else:
                # Fallback: sanitize URL
                output_name = re.sub(r'[^a-zA-Z0-9-]', '-', repo_path_str).strip('-')[:50]
        else:
            # Local path - use repository directory name
            # Note: If path is /work, it was copied by the wrapper script which should
            # have passed --name, so this branch is mainly for direct invocations
            repo_path_obj = Path(repo_path_str)
            output_name = repo_path_obj.name or "repo"
        
        # Sanitize the name
        output_name = re.sub(r'[^a-zA-Z0-9._-]', '-', output_name).strip('-')
        if not output_name:
            output_name = "repo"
        
        # Use generated name for image tag to ensure uniqueness
        image_tag = f"repo2sif-{output_name}:latest"
    
    # Build image using jupyter-repo2docker CLI
    print(f"Building Docker image from {repo_path}...")
    _run([
        "jupyter-repo2docker",
        "--no-run",
        "--image-name", image_tag,
        "--user-name", "r2d",
        "--user-id", "1000",
        "--target-repo-dir", "/repo2sif_dir",
        repo_path,
    ])
    
    # Save Docker image to tar
    tar_path = args.output / f"{output_name}.tar"
    print(f"Saving Docker image to {tar_path}...")
    _run(["docker", "save", image_tag, "-o", str(tar_path)])
    print(f"Wrote: {tar_path}")

    # Optionally convert to SIF
    if args.sif:
        sif_path = args.output / f"{output_name}.sif"
        print(f"Converting to SIF format: {sif_path}...")
        try:
            _run(["apptainer", "build", str(sif_path), f"docker-daemon://{image_tag}"])
        except subprocess.CalledProcessError:
            print(f"Error converting to SIF: {e}", file=sys.stderr)
            # Fallback to using tar file if docker-daemon doesn't work
            _run(["apptainer", "build", str(sif_path), f"docker-archive://{tar_path}"])
        print(f"Wrote: {sif_path}")


if __name__ == "__main__":
    main()
