#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y --no-install-recommends \
  curl wget jq vim tmux git ncat \
  python3 python3-pip python3-venv

apt-get install -y --no-install-recommends \
  ffuf gobuster sqlmap nikto || echo "[WARN] web tools: some failed"

apt-get install -y --no-install-recommends \
  hashcat hashid || echo "[WARN] hash tools: some failed"

apt-get install -y --no-install-recommends \
  seclists wordlists || echo "[WARN] wordlists: some failed"

apt-get install -y --no-install-recommends \
  nodejs npm || echo "[WARN] node tools: some failed"

pip3 install --break-system-packages pyjwt requests || echo "[WARN] pip: some failed"

exec tail -f /dev/null
