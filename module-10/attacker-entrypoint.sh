#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y --no-install-recommends \
  curl wget jq vim tmux git ncat \
  python3 python3-pip python3-venv

pip3 install --break-system-packages requests garak promptmap || echo "[WARN] pip: some failed"

exec tail -f /dev/null
