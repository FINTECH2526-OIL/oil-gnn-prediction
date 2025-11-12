import functions_framework
from datetime import datetime, timedelta
import os

from daily_data_pipeline_standalone import DailyDataPipeline

@functions_framework.http
def daily_data_update(request):
    try:
        target_date_str = request.args.get('date')
        
        if target_date_str:
            target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        else:
            target_date = datetime.now() - timedelta(days=1)
        
        pipeline = DailyDataPipeline()
        
        output_path = pipeline.run_daily_update(target_date)
        
        return {
            'status': 'success',
            'message': f'Data pipeline completed for {target_date.date()}',
            'output_path': output_path,
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
        target_date = datetime.now() - timedelta(days=1)
        
        pipeline = DailyDataPipeline()
        output_path = pipeline.run_daily_update(target_date)
        
        print(f"Scheduled update completed: {output_path}")
        
    except Exception as e:
        print(f"Error in scheduled update: {e}")
        raise
