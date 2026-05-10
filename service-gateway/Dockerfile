FROM python:3.11-slim

WORKDIR /app

COPY shared-schema /shared-schema

COPY service-gateway/requirements.txt ./
# Install CPU-only torch first so sentence-transformers doesn't pull CUDA (~10x smaller image).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir -r requirements.txt

COPY service-gateway/app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
