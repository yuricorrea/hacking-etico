FROM python:3.11-slim

# Pacotes para enumeração + SSH server (alvo do foothold) + ferramentas de pivoting
RUN apt update && apt install -y --no-install-recommends \
        iproute2 iputils-ping curl openssh-server sudo nano \
        bettercap procps net-tools \
    && rm -rf /var/lib/apt/lists/*

# Usuário "www" com senha fraca (presente em rockyou) + flag do exercício 1.2.2
RUN useradd -m -s /bin/bash www && echo "www:Welcome2025" | chpasswd \
    && mkdir /var/run/sshd \
    && echo "PermitRootLogin no" >> /etc/ssh/sshd_config \
    && echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config \
    && echo 'flag{dmz_foothold_via_weak_creds}' > /home/www/.first_flag \
    && chown www:www /home/www/.first_flag \
    && chmod 600 /home/www/.first_flag \
    && echo "www ALL=(ALL) NOPASSWD: /usr/bin/bettercap" >> /etc/sudoers

# Mini app Flask para parecer um portal
WORKDIR /app
RUN pip install --no-cache-dir flask
RUN echo 'from flask import Flask\n\
app = Flask(__name__)\n\
@app.route("/")\n\
def index():\n\
    return "<h1>ACME Corp Portal</h1><p>Login at /login</p>"\n\
' > app.py

EXPOSE 22 5000

CMD bash -c "service ssh start && python3 app.py --host=0.0.0.0 --port=5000"
