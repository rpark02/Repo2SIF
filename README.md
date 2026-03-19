# Repo2SIF

Barebones tool to convert repositories to Docker images and save as tar/SIF files.

## Quick Start

```bash
# Build the Docker image (first time only, or use --build flag)
./repo2sif /path/to/repo

# Convert with custom output name
./repo2sif /path/to/repo --name my-image

# Convert and also create SIF file
./repo2sif /path/to/repo --name my-image --sif

# Specify custom output directory
./repo2sif /path/to/repo --name my-image --output /custom/path
```

## CLI Wrapper Usage

The `./repo2sif` script is a convenience wrapper that handles Docker operations:

```bash
./repo2sif <repo_path> [OPTIONS]
```

### Options

- `-n, --name NAME` - Name for output files (without extension)
- `-o, --output DIR` - Output directory (default: `./out` next to repo)
- `-t, --tag TAG` - Docker image tag (default: `repo2sif-image:latest`)
- `--sif` - Also produce a .sif file (requires --privileged)
- `--build` - Force rebuild Docker image
- `-h, --help` - Show help message

### Examples

```bash
# Basic usage with local path
./repo2sif /path/to/repo

# With GitHub URL
./repo2sif https://github.com/user/repo --name my-image

# With custom name
./repo2sif /path/to/repo --name my-custom-image

# With SIF output
./repo2sif /path/to/repo --name my-image --sif

# GitHub URL with SIF output
./repo2sif https://github.com/user/repo --name my-image --sif

# Custom output directory
./repo2sif /path/to/repo --name my-image --output ~/outputs
```

## Manual Docker Usage

If you prefer to use Docker directly:

```bash
docker build -t repo2sif:latest --platform=linux/amd64 .

docker run --rm -it \
  -v /path/to/repo:/work \
  -v /path/to/output:/out \
  -v /var/run/docker.sock:/var/run/docker.sock \
  repo2sif:latest /work --name my-image
```
