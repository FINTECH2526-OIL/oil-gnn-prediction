#!/usr/bin/env python3
"""Utility to backfill prediction history records for historical feature dates."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence

import pandas as pd
from google.cloud import storage

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.append(CURRENT_DIR)
APP_DIR = os.path.join(CURRENT_DIR, "app")
if APP_DIR not in sys.path:
    sys.path.append(APP_DIR)
CONTAINER_APP_DIR = os.path.join(os.path.dirname(CURRENT_DIR), "app")
if os.path.isdir(CONTAINER_APP_DIR) and CONTAINER_APP_DIR not in sys.path:
    sys.path.append(CONTAINER_APP_DIR)

from app.config import config
from app.data_loader import DataLoader
from app.inference import ModelInference
from prediction_pipeline import (
    HISTORY_BLOB_PATH,
    _generate_record,
    _load_history,
    _save_history,
)


def _select_target_dates(
    available_dates: Sequence[pd.Timestamp],
    days: Optional[int],
    start_date: Optional[pd.Timestamp],
) -> List[pd.Timestamp]:
    ordered = [pd.Timestamp(ts).normalize() for ts in pd.to_datetime(available_dates)]
    ordered.sort()
    if not ordered:
        return []

    if start_date is not None:
        start_ts = pd.Timestamp(start_date).normalize()
        ordered = [d for d in ordered if d >= start_ts]

    if days is not None and days > 0:
        ordered = ordered[-days:]

    return ordered


def _update_actuals(history: List[Dict], new_record: Dict) -> int:
    updates = 0
    for past_record in history:
        if past_record.get("prediction_for_date") == new_record["feature_date"] and past_record.get("actual_close") is None:
            reference_close = past_record.get("reference_close", new_record["reference_close"])
            past_record["actual_close"] = new_record["reference_close"]
            past_record["actual_delta"] = past_record["actual_close"] - reference_close
            past_record["error_delta"] = past_record.get("predicted_delta") - past_record["actual_delta"]
            past_record["error_price"] = past_record.get("predicted_close") - new_record["reference_close"]
            past_record["actual_recorded_at"] = new_record["prediction_generated_at"]
            updates += 1
    return updates


def backfill_predictions(days: Optional[int] = None, start_date: Optional[str] = None, dry_run: bool = False) -> Dict:
    loader = DataLoader()
    df = loader.get_latest_data()
    if df.empty:
        raise ValueError("No engineered data available for backfill")

    df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    available_dates = df["date"].unique()

    start_ts = pd.Timestamp(start_date).normalize() if start_date else None
    target_dates = _select_target_dates(available_dates, days, start_ts)
    if not target_dates:
        return {"processed_records": [], "history_length": 0, "updated_outcomes": 0, "dry_run": dry_run}

    model_inf = ModelInference()
    model_inf.load_models()

    client = storage.Client()
    bucket = client.bucket(config.GCS_BUCKET_NAME)
    history = _load_history(bucket)

    processed: List[Dict] = []
    updated_outcomes = 0

    for target_ts in target_dates:
        record = _generate_record(df, model_inf, target_ts)
        updated_outcomes += _update_actuals(history, record)

        existing = next((item for item in history if item.get("feature_date") == record["feature_date"]), None)
        if existing:
            existing.update(record)
        else:
            history.append(record)
        processed.append(record)

    if not dry_run:
        _save_history(bucket, history)

    processed_dates = [record["feature_date"] for record in processed]

    return {
        "processed_records": processed,
        "processed_dates": processed_dates,
        "history_length": len(history),
        "updated_outcomes": updated_outcomes,
        "history_blob": HISTORY_BLOB_PATH,
        "dry_run": dry_run,
    }


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill prediction history records")
    parser.add_argument("--days", type=int, default=30, help="Number of most recent feature dates to backfill")
    parser.add_argument(
        "--start-date",
        type=str,
        default=None,
        help="ISO date (YYYY-MM-DD) to begin backfill; overrides days when later than the implied window",
    )
    parser.add_argument("--dry-run", action="store_true", help="Run without writing results to storage")
    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    try:
        summary = backfill_predictions(days=args.days, start_date=args.start_date, dry_run=args.dry_run)
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        return 1

    summary.update({
        "success": True,
        "records_created": len(summary.get("processed_records", [])),
    })
    print(json.dumps(summary, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
