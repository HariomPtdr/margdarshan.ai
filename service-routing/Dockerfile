FROM python:3.11-slim

WORKDIR /app

COPY shared-schema /shared-schema

COPY service-routing/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY service-routing/app ./app
COPY service-routing/data ./data

EXPOSE 8005
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
