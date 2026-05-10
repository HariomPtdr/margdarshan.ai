FROM python:3.11-slim

WORKDIR /app

COPY shared-schema /shared-schema

COPY service-submission/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY service-submission/app ./app

EXPOSE 8006
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
