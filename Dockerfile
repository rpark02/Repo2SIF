ARG BUILDPLATFORM=linux/amd64
FROM --platform=${BUILDPLATFORM} ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    git \
    software-properties-common \
    curl \
    squashfs-tools \
    wget \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    docker.io \
    docker-buildx \
  && rm -rf /var/lib/apt/lists/* \
  && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
  && curl -sS https://bootstrap.pypa.io/get-pip.py | python3.11

# Install Apptainer
RUN cd /tmp && \
    wget https://github.com/apptainer/apptainer/releases/download/v1.4.5/apptainer_1.4.5_amd64.deb && \
    apt-get update && \
    apt-get install -y ./apptainer_1.4.5_amd64.deb && \
    rm -f ./apptainer_1.4.5_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY . /app
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -e /app

WORKDIR /work
ENTRYPOINT ["python3", "/app/main.py"]
