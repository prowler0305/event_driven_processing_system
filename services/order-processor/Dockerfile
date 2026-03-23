FROM python:3.11-slim

WORKDIR /app

COPY services/order-processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared /app/shared
COPY services/order-processor/src ./src

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "order_processor.main"]