FROM python:3.11-slim

RUN apt update && apt install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir flask requests

COPY app.py /app/app.py

# Estrutura "permitida" para read_file
RUN mkdir -p /app/data && \
    echo "Bem-vindo ao Acme Agent. Diretório seguro: /app/data" > /app/data/welcome.txt && \
    echo "user=acme-svc\npassword=tr0ub4dor3" > /app/data/credentials.txt && \
    chmod 644 /app/data/*

# "Fora" do diretório permitido — alvo do CTF
RUN mkdir -p /etc/secrets && \
    echo 'flag{tool_hijack_via_path_traversal}' > /etc/secrets/flag.txt && \
    chmod 644 /etc/secrets/flag.txt

EXPOSE 5000
CMD ["python3", "app.py"]
