# Repo2SIF

Barebones tool to convert repositories to Docker images and save as tar/SIF files.

## Prerequisites

- [Docker](https://www.docker.com/) installed and running
- Git (for cloning remote repositories)

## Quick Start

The repo2sif Docker image is built automatically on first run — no setup needed. Just run:

```bash
./repo2sif --input /path/to/repo --output ./out
```

This will:
1. Build the repo2sif Docker image (first run only)
2. Convert the repository into a Docker image using [repo2docker](https://repo2docker.readthedocs.io/)
3. Save the image as a `.tar` file in the output directory

To also generate a `.sif` file (Apptainer/Singularity format):

```bash
./repo2sif --input /path/to/repo --output ./out --sif
```

## CLI Usage

```bash
./repo2sif --input <repo_path> --output <output_dir> [OPTIONS]
```

### Required Arguments

- `-i, --input PATH` - Path to the repository to convert (local path or Git URL)
- `-o, --output DIR` - Output directory for generated files

### Options

- `--sif` - Also produce a `.sif` file (runs container with `--privileged`)
- `--image-tag-name NAME` - Custom Docker image tag (default: `repo2sif-<repo-name>:latest`)
- `--build` - Force rebuild of the repo2sif Docker image
- `-h, --help` - Show help message

When run with `--build` alone (no `--input`/`--output`), only the repo2sif Docker image is built:

```bash
./repo2sif --build
```

### Examples

```bash
# Local repository
./repo2sif --input /path/to/repo --output ./out

# GitHub URL
./repo2sif --input https://github.com/user/repo --output ./out

# Generate both tar and SIF files
./repo2sif --input https://github.com/user/repo --output ./out --sif

# Custom Docker image tag
./repo2sif --input /path/to/repo --output ./out --image-tag-name my-tag:v1

# Force rebuild of the repo2sif Docker image
./repo2sif --input /path/to/repo --output ./out --build

# Build (or rebuild) the repo2sif Docker image only
./repo2sif --build
```

## Output

The tool generates the following files in the output directory:

- `<repo-name>.tar` - Docker image saved as a tar archive
- `<repo-name>.sif` - Apptainer/Singularity image (only when `--sif` is used)

Timing information is logged for each step and at the end of the conversion.

## Manual Docker Usage

If you prefer to use Docker directly:

```bash
docker build --load -t repo2sif:latest --platform=linux/amd64 .

docker run --rm -it \
  -v /var/run/docker.sock:/var/run/docker.sock \
  repo2sif:latest /work --name my-image
```

Note: When running manually, you need to copy the repository into the container at `/work` and retrieve output from `/out`. The `./repo2sif` wrapper handles this automatically.
