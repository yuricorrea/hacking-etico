#!/bin/bash

export DEBIAN_FRONTEND=noninteractive

# Pré-responde o prompt do wireshark
echo "wireshark-common wireshark-common/install-setuid boolean false" | debconf-set-selections

apt-get update

apt-get install -y --no-install-recommends \
  nmap ncat netcat-openbsd net-tools iputils-ping bind9-dnsutils \
  curl wget git vim tmux jq \
  python3 python3-pip python3-venv \
  tcpdump tshark openssh-client openssl

apt-get install -y --no-install-recommends \
  hashid hash-identifier john hashcat || echo "[WARN] hash tools: some failed"

apt-get install -y --no-install-recommends \
  gobuster ffuf nikto sqlmap || echo "[WARN] web tools: some failed"

apt-get install -y --no-install-recommends \
  seclists wordlists || echo "[WARN] wordlists: some failed"

apt-get install -y --no-install-recommends \
  impacket-scripts responder bloodhound || echo "[WARN] AD tools: some failed"

exec tail -f /dev/null
