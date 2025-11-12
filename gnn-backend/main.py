import functions_framework
from datetime import datetime

from daily_data_pipeline_standalone import DailyDataPipeline
from prediction_pipeline import run_daily_inference

@functions_framework.http
def daily_data_update(request):
    try:
        target_date = None
        target_date_str = request.args.get('date')
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')

        pipeline = DailyDataPipeline()
        output_path = pipeline.run_daily_update(target_date)
        prediction_summary = run_daily_inference()

        record = prediction_summary.get('record', {})
        feature_date = record.get('feature_date')
        return {
            'status': 'success',
            'message': f'Data pipeline completed for {feature_date}' if feature_date else 'Data pipeline completed',
            'output_path': output_path,
            'prediction': record,
            'history_blob': prediction_summary.get('history_blob'),
            'history_length': prediction_summary.get('history_length'),
            'updated_outcomes': prediction_summary.get('updated_outcomes'),
            'timestamp': datetime.now().isoformat()
        }, 200
        
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e),
            'timestamp': datetime.now().isoformat()
        }, 500

@functions_framework.cloud_event
def scheduled_daily_update(cloud_event):
    try:
        pipeline = DailyDataPipeline()
        output_path = pipeline.run_daily_update()
        prediction_summary = run_daily_inference()
        record = prediction_summary.get('record', {})
        feature_date = record.get('feature_date')
        print(
            "Scheduled update completed",
            output_path,
            feature_date,
            prediction_summary.get('updated_outcomes', 0),
        )
        
    except Exception as e:
        print(f"Error in scheduled update: {e}")
        raise
