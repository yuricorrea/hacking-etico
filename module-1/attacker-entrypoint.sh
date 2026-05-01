#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

apt-get update

apt-get install -y --no-install-recommends \
  nmap masscan dnsutils iputils-ping iproute2 \
  curl wget vim tmux git \
  python3 python3-pip python3-venv \
  openssh-client

apt-get install -y --no-install-recommends \
  responder impacket-scripts mitm6 bettercap || echo "[WARN] AD/MITM tools: some failed"

apt-get install -y --no-install-recommends \
  proxychains4 hydra || echo "[WARN] pivot/brute tools: some failed"

apt-get install -y --no-install-recommends \
  smbclient cifs-utils enum4linux netexec || echo "[WARN] SMB/AD recon: some failed"

apt-get install -y --no-install-recommends \
  wordlists seclists || echo "[WARN] wordlists: some failed"

# chisel não está nos repos Kali — baixa o release oficial
ARCH="$(dpkg --print-architecture)"
case "$ARCH" in
  amd64) CHISEL_ARCH=linux_amd64 ;;
  arm64) CHISEL_ARCH=linux_arm64 ;;
  *)     CHISEL_ARCH="" ;;
esac
if [ -n "$CHISEL_ARCH" ]; then
  curl -fsSL "https://github.com/jpillora/chisel/releases/latest/download/chisel_${CHISEL_ARCH}.gz" \
    | gunzip > /usr/local/bin/chisel \
    && chmod +x /usr/local/bin/chisel \
    || echo "[WARN] chisel download failed"
fi

exec tail -f /dev/null
