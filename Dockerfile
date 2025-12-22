FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY gnn-backend/app /app/app
COPY gnn-backend/prediction_pipeline.py /app/prediction_pipeline.py
COPY gnn-backend/backfill_predictions.py /workspace/backfill_predictions.py
COPY run_data_pipeline.py /workspace/run_data_pipeline.py
COPY multi_step_forecast.py /workspace/multi_step_forecast.py
COPY incremental_update.py /workspace/incremental_update.py
COPY gnn-backend /app/gnn-backend

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --timeout 300 app.main:app
