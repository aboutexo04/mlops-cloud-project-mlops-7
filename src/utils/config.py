"""Configuration utilities for the commute comfort ingestion pipeline."""
from __future__ import annotations

from dataclasses import dataclass
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()  # .env 파일 로드


@dataclass
class KMAApiConfig:
    """Configuration for accessing the KMA API."""

    base_url: str
    api_key: str
    station_id: str
    timeout_seconds: int = 10

    @classmethod
    def from_env(cls, prefix: str = "KMA") -> "KMAApiConfig":
        base_url = os.getenv(f"{prefix}_BASE_URL")
        api_key = os.getenv(f"{prefix}_API_KEY")
        station_id = os.getenv(f"{prefix}_STATION_ID")

        if not base_url:
            raise ValueError("Missing KMA base URL environment variable")
        if not api_key:
            raise ValueError("Missing KMA API key environment variable")
        if not station_id:
            raise ValueError("Missing KMA station id environment variable")

        timeout = int(os.getenv(f"{prefix}_TIMEOUT_SECONDS", "10"))
        return cls(base_url=base_url, api_key=api_key, station_id=station_id, timeout_seconds=timeout)

@dataclass
class S3Config:
    bucket_name: str
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    endpoint_url: Optional[str] = None   # 기본값 있는 필드는 항상 마지막!

    @classmethod
    def from_env(cls) -> "S3Config":
        endpoint_url = os.getenv("S3_ENDPOINT_URL", "http://localhost:4566")
        # 빈 문자열이면 None으로 설정 (실제 AWS S3 사용)
        if endpoint_url == "":
            endpoint_url = None

        return cls(
            bucket_name=os.getenv("S3_BUCKET_NAME", "weather-mlops-team-data"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            endpoint_url=endpoint_url,
        )

@dataclass
class MySQLConfig:
    """Connection configuration for the MySQL warehouse."""

    host: str
    port: int
    user: str
    password: str
    database: str

    @classmethod
    def from_env(cls, prefix: str = "MYSQL") -> "MySQLConfig":
        host = os.getenv(f"{prefix}_HOST", "localhost")
        port = int(os.getenv(f"{prefix}_PORT", "3306"))
        user = os.getenv(f"{prefix}_USER")
        password = os.getenv(f"{prefix}_PASSWORD")
        database = os.getenv(f"{prefix}_DATABASE")

        missing: list[str] = [
            name for name, value in (
                (f"{prefix}_USER", user),
                (f"{prefix}_PASSWORD", password),
                (f"{prefix}_DATABASE", database),
            )
            if not value
        ]
        if missing:
            raise ValueError(f"Missing MySQL environment variables: {', '.join(missing)}")

        return cls(host=host, port=port, user=user, password=password, database=database)


@dataclass
class AirflowConfig:
    """Optional Airflow configuration, useful for DAG parameterization."""

    dag_id: str
    schedule: Optional[str] = None


__all__ = ["KMAApiConfig", "MySQLConfig", "AirflowConfig"]
