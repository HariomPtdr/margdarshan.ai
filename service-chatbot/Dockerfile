FROM python:3.11-slim

WORKDIR /app

# Build context is project root. Copy shared-schema first.
COPY shared-schema /shared-schema

COPY service-chatbot/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY service-chatbot/app ./app

EXPOSE 8001
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
