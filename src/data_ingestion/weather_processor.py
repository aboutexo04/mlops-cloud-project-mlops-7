"""S3 기반 기상 데이터 파싱 및 전처리기"""
from __future__ import annotations

import sys
import os
import pandas as pd
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

# 프로젝트 루트 경로 세팅
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.logger_config import configure_logger
from src.data_ingestion.kma_client import KMAApiClient
from src.utils.config import KMAApiConfig, S3Config
from src.storage.s3_client import S3StorageClient
from src.storage.s3_client import WeatherDataS3Handler
from src.features.feature_builder import create_ml_dataset

# ✅ WeatherParser → parsers 로 변경
from src.data_ingestion import parsers  

_logger = configure_logger(__name__)


class WeatherDataProcessor:
    """S3 기반 기상 데이터 파싱 및 전처리기"""

    def __init__(self, kma_config: KMAApiConfig = None, s3_config: S3Config = None):
        self._logger = configure_logger(self.__class__.__name__)

        if kma_config is None:
            kma_config = KMAApiConfig.from_env()
        if s3_config is None:
            s3_config = S3Config.from_env()

        # KMA API 클라이언트 초기화
        self.kma_client = KMAApiClient(kma_config)

        # S3 클라이언트 초기화
        self.s3_client = S3StorageClient(
            bucket_name=s3_config.bucket_name,
            aws_access_key_id=s3_config.aws_access_key_id,
            aws_secret_access_key=s3_config.aws_secret_access_key,
            region_name=s3_config.region_name,
            endpoint_url=s3_config.endpoint_url,  # LocalStack 사용 가능
        )
        self.weather_handler = WeatherDataS3Handler(self.s3_client)

    def process_and_store_weather_data(
        self,
        asos_raw: str = None,
        pm10_raw: str = None,
        uv_raw: str = None,
        timestamp: datetime = None,
    ) -> Dict[str, str]:
        """원시 기상 데이터를 파싱하고 S3에 저장"""

        if timestamp is None:
            timestamp = datetime.now(tz=timezone.utc)

        self._logger.info("Starting weather data processing and S3 storage")

        try:
            stored_keys = {}

            # 1. 원시 데이터 S3 저장
            if asos_raw:
                stored_keys["asos_raw"] = self.weather_handler.save_raw_weather_data("asos", asos_raw, timestamp)
            if pm10_raw:
                stored_keys["pm10_raw"] = self.weather_handler.save_raw_weather_data("pm10", pm10_raw, timestamp)
            if uv_raw:
                stored_keys["uv_raw"] = self.weather_handler.save_raw_weather_data("uv", uv_raw, timestamp)

            # 2. 데이터 파싱 (✅ parsers 모듈 함수 사용)
            parsed_asos = parsers.parse_asos_raw(asos_raw) if asos_raw else []
            parsed_pm10 = parsers.parse_pm10_raw(pm10_raw) if pm10_raw else []
            parsed_uv = parsers.parse_uv_raw(uv_raw) if uv_raw else []

            # 3. 파싱된 데이터 S3 저장
            if parsed_asos:
                stored_keys["asos_parsed"] = self.weather_handler.save_parsed_weather_data("asos", parsed_asos, timestamp)
            if parsed_pm10:
                stored_keys["pm10_parsed"] = self.weather_handler.save_parsed_weather_data("pm10", parsed_pm10, timestamp)
            if parsed_uv:
                stored_keys["uv_parsed"] = self.weather_handler.save_parsed_weather_data("uv", parsed_uv, timestamp)

            # 4. ML용 데이터셋 생성 및 저장
            if parsed_asos or parsed_pm10 or parsed_uv:
                raw_data = {"asos": parsed_asos, "pm10": parsed_pm10, "uv": parsed_uv}
                ml_dataset = create_ml_dataset(raw_data)

                if not ml_dataset.empty:
                    ml_key = self.weather_handler.save_ml_dataset(ml_dataset, timestamp)
                    stored_keys["ml_dataset"] = ml_key
                    self._logger.info(f"ML 데이터셋 저장 완료: {ml_dataset.shape}")
                else:
                    self._logger.warning("ML 데이터셋이 비어있습니다.")

            return stored_keys

        except Exception as e:
            self._logger.error(f"Error in weather data processing: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def load_latest_ml_dataset(self, days_back: int = 7) -> Optional[pd.DataFrame]:
        """최신 ML 데이터셋 로드"""
        return self.weather_handler.load_latest_ml_dataset(days_back=days_back)

    def get_data_inventory(self) -> Dict[str, Any]:
        """S3 데이터 인벤토리 조회"""
        return self.weather_handler.get_data_inventory()

    def fetch_weather_data(self, data_type: str) -> str:
        """KMA API에서 특정 타입의 기상 데이터 수집"""
        target_time = datetime.now() - timedelta(hours=1)

        try:
            if data_type == 'asos':
                return self.kma_client.fetch_asos(target_time)
            elif data_type == 'pm10':
                return self.kma_client.fetch_pm10(target_time, target_time)
            elif data_type == 'uv':
                return self.kma_client.fetch_uv(target_time)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            self._logger.error(f"Error fetching {data_type} data: {e}")
            return ""

    def parse_weather_data(self, data_type: str, raw_data: str) -> list:
        """원시 기상 데이터 파싱"""
        try:
            if data_type == 'asos':
                return parsers.parse_asos_raw(raw_data)
            elif data_type == 'pm10':
                return parsers.parse_pm10_raw(raw_data)
            elif data_type == 'uv':
                return parsers.parse_uv_raw(raw_data)
            else:
                raise ValueError(f"Unsupported data type: {data_type}")
        except Exception as e:
            self._logger.error(f"Error parsing {data_type} data: {e}")
            return []


def main():
    print("S3 기반 기상 데이터 처리기")
    print("=" * 50)

    try:
        kma_config = KMAApiConfig.from_env()
        s3_config = S3Config.from_env()

        client = KMAApiClient(kma_config)
        target_time = datetime.now() - timedelta(hours=1)

        asos_raw = client.fetch_asos(target_time)
        pm10_raw = client.fetch_pm10(target_time, target_time)
        uv_raw = client.fetch_uv(target_time)

        processor = WeatherDataProcessor(s3_config)
        stored_keys = processor.process_and_store_weather_data(
            asos_raw=asos_raw, pm10_raw=pm10_raw, uv_raw=uv_raw, timestamp=target_time
        )

        if stored_keys:
            print(f"\n처리 완료! 저장된 객체 수: {len(stored_keys)}")
        else:
            print("처리된 데이터가 없습니다.")

        return stored_keys
    except Exception as e:
        print(f"오류 발생: {e}")
        return {}


if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)


__all__ = ["WeatherDataProcessor"]
