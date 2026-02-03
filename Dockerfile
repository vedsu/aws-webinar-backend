FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY app.py .

# App Runner provides PORT at runtime
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} app:app"]
