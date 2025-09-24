"""
Airflow DAG for automated weather data collection and ML dataset generation.

This DAG runs every hour to:
1. Fetch weather data from KMA API (ASOS, PM10, UV)
2. Parse and store raw data to S3
3. Generate ML dataset with 30 engineered features
4. Store ML dataset to S3 for model training

Schedule: Every hour at 10 minutes past the hour
Author: MLOps Team
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
import sys
import os

# Add project source to Python path
sys.path.append('/opt/airflow/dags')
sys.path.append('/opt/airflow/src')
sys.path.append('/opt/airflow')

# Default arguments for all tasks
default_args = {
    'owner': 'mlops-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 9, 23),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False
}

# DAG definition
dag = DAG(
    'weather_data_pipeline',
    default_args=default_args,
    description='Hourly weather data collection and ML dataset generation',
    schedule_interval='10 * * * *',  # Every hour at 10 minutes past
    max_active_runs=1,
    tags=['weather', 'ml', 'kma-api', 's3']
)

def fetch_kma_weather_data(**context):
    """
    Fetch weather data from KMA API for all data types (ASOS, PM10, UV).
    """
    from src.data_ingestion.weather_processor import WeatherDataProcessor
    from src.utils.config import KMAApiConfig, S3Config
    from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
    from datetime import datetime

    print("=== Starting KMA API data fetch ===")

    # Initialize configurations
    kma_config = KMAApiConfig.from_env()
    s3_config = S3Config.from_env()

    # Initialize S3 handler
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Initialize weather processor
    processor = WeatherDataProcessor(kma_config)

    # Fetch data for all types
    data_types = ['asos', 'pm10', 'uv']
    fetched_data = {}

    for data_type in data_types:
        try:
            print(f"Fetching {data_type} data...")
            raw_data = processor.fetch_weather_data(data_type)

            # Save raw data to S3
            timestamp = datetime.now()
            s3_key = weather_handler.save_raw_weather_data(data_type, raw_data, timestamp)
            print(f"Raw {data_type} data saved: {s3_key}")

            # Parse data
            parsed_data = processor.parse_weather_data(data_type, raw_data)

            # Save parsed data to S3
            parsed_s3_key = weather_handler.save_parsed_weather_data(data_type, parsed_data, timestamp)
            print(f"Parsed {data_type} data saved: {parsed_s3_key}")

            fetched_data[data_type] = parsed_data

        except Exception as e:
            print(f"Error fetching {data_type} data: {e}")
            # Continue with other data types even if one fails
            fetched_data[data_type] = []

    # Store fetched data in XCom for next task
    return fetched_data

def generate_ml_dataset(**context):
    """
    Generate ML dataset with 30 engineered features from fetched weather data.
    """
    from src.features.feature_builder import create_ml_dataset
    from src.utils.config import S3Config
    from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler
    from datetime import datetime

    print("=== Starting ML dataset generation ===")

    # Get fetched data from previous task
    ti = context['ti']
    raw_data = ti.xcom_pull(task_ids='fetch_weather_data')

    if not raw_data:
        print("❌ No weather data available for ML dataset generation")
        return

    # Check if we have sufficient data
    total_records = sum(len(data) for data in raw_data.values())
    print(f"Total records available: {total_records}")

    if total_records == 0:
        print("❌ No valid weather records to process")
        return

    # Generate ML dataset with engineered features
    df = create_ml_dataset(raw_data)

    if df.empty:
        print("❌ Generated ML dataset is empty")
        return

    print(f"✅ ML dataset generated: {len(df)} records, {len(df.columns)} features")

    # Initialize S3 handler
    s3_config = S3Config.from_env()
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Save ML dataset to S3
    timestamp = datetime.now()
    s3_key = weather_handler.save_ml_dataset(df, timestamp)
    print(f"✅ ML dataset saved to S3: {s3_key}")

    # Log dataset summary
    print("=== Dataset Summary ===")
    print(f"Features: {list(df.columns)}")
    print(f"Sample comfort scores: {df['comfort_score'].tolist() if 'comfort_score' in df.columns else 'N/A'}")

    return s3_key

def validate_pipeline_success(**context):
    """
    Validate that the entire pipeline completed successfully.
    """
    from src.utils.config import S3Config
    from src.storage.s3_client import S3StorageClient, WeatherDataS3Handler

    print("=== Validating pipeline success ===")

    # Get ML dataset S3 key from previous task
    ti = context['ti']
    ml_dataset_key = ti.xcom_pull(task_ids='generate_ml_dataset')

    if not ml_dataset_key:
        raise ValueError("ML dataset generation failed - no S3 key returned")

    # Initialize S3 handler
    s3_config = S3Config.from_env()
    s3_client = S3StorageClient(
        bucket_name=s3_config.bucket_name,
        aws_access_key_id=s3_config.aws_access_key_id,
        aws_secret_access_key=s3_config.aws_secret_access_key,
        region_name=s3_config.region_name,
        endpoint_url=s3_config.endpoint_url
    )
    weather_handler = WeatherDataS3Handler(s3_client)

    # Get data inventory
    inventory = weather_handler.get_data_inventory()
    print(f"✅ S3 Data Inventory: {inventory}")

    # Verify latest ML dataset can be loaded
    df = weather_handler.load_latest_ml_dataset()
    if df is not None and len(df) > 0:
        print(f"✅ Latest ML dataset verified: {len(df)} records, {len(df.columns)} features")

        # Log key metrics
        if 'comfort_score' in df.columns:
            avg_comfort = df['comfort_score'].mean()
            print(f"✅ Average comfort score: {avg_comfort:.1f}")

        print("🎉 Weather data pipeline completed successfully!")
        return True
    else:
        raise ValueError("Failed to load latest ML dataset from S3")

# Task definitions
start_task = DummyOperator(
    task_id='start_pipeline',
    dag=dag
)

fetch_weather_task = PythonOperator(
    task_id='fetch_weather_data',
    python_callable=fetch_kma_weather_data,
    dag=dag
)

generate_ml_task = PythonOperator(
    task_id='generate_ml_dataset',
    python_callable=generate_ml_dataset,
    dag=dag
)

validate_task = PythonOperator(
    task_id='validate_pipeline',
    python_callable=validate_pipeline_success,
    dag=dag
)

end_task = DummyOperator(
    task_id='end_pipeline',
    dag=dag
)

# Task dependencies
start_task >> fetch_weather_task >> generate_ml_task >> validate_task >> end_task