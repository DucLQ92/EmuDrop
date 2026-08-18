# Uses monkeyx/retro_builder:arm64 as base image
FROM monkeyx/retro_builder:arm64

# Remove expired Kitware repo key and install python3-pip & QEMU
RUN rm -f /etc/apt/sources.list.d/kitware.list \
    && apt-get update && apt-get install -y --no-install-recommends \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    qemu-user-static \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip3 install --upgrade pip && pip3 install -r requirements.txt

VOLUME /root/workspace
WORKDIR /root/workspace

# Starting the container with Bash
CMD ["/bin/bash"]