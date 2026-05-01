FROM debian:12-slim

RUN apt update && apt install -y --no-install-recommends \
        samba smbclient cifs-utils iproute2 iputils-ping procps \
    && rm -rf /var/lib/apt/lists/*

# Usuário SMB "alice" + share com a flag do CTF "Acme Pivot"
RUN useradd -m alice && echo "alice:Spring2026!" | chpasswd \
    && (echo "Spring2026!"; echo "Spring2026!") | smbpasswd -a alice \
    && mkdir -p /share \
    && echo 'flag{ntlm_relay_to_smb_owns_workstations}' > /share/secret.txt \
    && chmod 770 /share \
    && chown root:users /share \
    && usermod -aG users alice

# SMB signing DESABILITADO de propósito (vulnerável a NTLM Relay)
RUN { \
      echo ""; \
      echo "[global]"; \
      echo "  server min protocol = SMB2"; \
      echo "  server signing = no"; \
      echo "  smb signing = disabled"; \
      echo "  client signing = no"; \
      echo ""; \
      echo "[share]"; \
      echo "  path = /share"; \
      echo "  valid users = alice"; \
      echo "  read only = no"; \
      echo "  browseable = yes"; \
    } >> /etc/samba/smb.conf

EXPOSE 139 445

CMD ["smbd", "--foreground", "--no-process-group", "--debug-stdout"]
