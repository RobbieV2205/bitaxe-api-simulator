FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py device.py models.py ./

EXPOSE 80

ENV PORT=80
ENV BIND_HOST=0.0.0.0

CMD ["gunicorn", "--bind", "0.0.0.0:80", "--workers", "1", "--threads", "4", "app:app"]
