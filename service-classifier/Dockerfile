FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

COPY shared-schema /shared-schema

COPY service-classifier/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY service-classifier/app ./app
# Bake trained model artifacts into the image
COPY service-classifier/model ./model
COPY service-classifier/model_v2 ./model_v2

EXPOSE 8004
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
