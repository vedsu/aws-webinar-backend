FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ENV PORT=8080
EXPOSE 8080

# App Runner expects your container to listen on $PORT
CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} app:app"]
