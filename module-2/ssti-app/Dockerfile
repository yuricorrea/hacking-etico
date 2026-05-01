FROM python:3.11-slim

RUN apt update && apt install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
RUN pip install --no-cache-dir flask requests

COPY app.py /app/app.py

# Flag para o desafio CTF "ACME Web Heist"
RUN echo 'flag{web_chain_owns_full_stack}' > /flag.txt && chmod 644 /flag.txt

EXPOSE 5000
CMD ["python3", "app.py"]
