"""Client utilities for interacting with the KMA API."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional, Union

import requests

from src.utils.config import KMAApiConfig
from src.utils.logger_config import configure_logger


class KMAApiClient:
    """Client wrapper for the KMA API (ASOS, PM10, UV)."""

    def __init__(self, config: KMAApiConfig) -> None:
        self._config = config
        self._logger = configure_logger(self.__class__.__name__)

    def _normalize_time(self, target_time: Optional[Union[str, datetime]]) -> datetime:
        """Convert input to datetime (accepts str or datetime).
        - 항상 UTC
        - ASOS 요청 시에는 minute=0으로 강제 (정시 데이터만 제공됨)
        """
        if target_time is None:
            target = datetime.now(tz=timezone.utc)
        elif isinstance(target_time, str):
            target = datetime.strptime(target_time, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        else:
            target = target_time

        # ✅ KMA API는 분단위 지원 안됨 → 정시(00분)으로 강제
        target = target.replace(minute=0, second=0, microsecond=0)
        return target

    def fetch_asos(self, target_time: Optional[Union[str, datetime]] = None) -> str:
        """지상 관측 (ASOS)"""
        target = self._normalize_time(target_time)
        params = {
            "tm": target.strftime("%Y%m%d%H%M"),
            "stn": self._config.station_id,   # 0 = 전국
            "authKey": self._config.api_key,
        }
        url = f"{self._config.base_url}/kma_sfctm2.php"
        self._logger.info(f"Requesting KMA ASOS data: {url}", extra={"params": params})
        response = requests.get(url, params=params, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.text

    def fetch_pm10(self, start_time: Optional[Union[str, datetime]], end_time: Optional[Union[str, datetime]]) -> str:
        """황사 (PM10)"""
        start = self._normalize_time(start_time)
        end = self._normalize_time(end_time)
        params = {
            "tm1": start.strftime("%Y%m%d%H%M"),
            "tm2": end.strftime("%Y%m%d%H%M"),
            "stn": self._config.station_id,
            "authKey": self._config.api_key,
        }
        url = f"{self._config.base_url}/kma_pm10.php"
        self._logger.info(f"Requesting KMA PM10 data: {url}", extra={"params": params})
        response = requests.get(url, params=params, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.text

    def fetch_uv(self, target_time: Optional[Union[str, datetime]] = None) -> str:
        """자외선 (UV)"""
        target = self._normalize_time(target_time)
        params = {
            "tm": target.strftime("%Y%m%d%H%M"),
            "stn": self._config.station_id,
            "authKey": self._config.api_key,
        }
        url = f"{self._config.base_url}/kma_sfctm_uv.php"
        self._logger.info(f"Requesting KMA UV data: {url}", extra={"params": params})
        response = requests.get(url, params=params, timeout=self._config.timeout_seconds)
        response.raise_for_status()
        return response.text


__all__ = ["KMAApiClient"]
