FROM python:3.11-slim

WORKDIR /app
RUN pip install --no-cache-dir flask requests

COPY app.py /app/app.py
COPY corpus /app/corpus

EXPOSE 5000
CMD ["python3", "app.py"]
