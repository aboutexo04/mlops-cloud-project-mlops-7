"""Parsing utilities for normalising KMA API responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping

from src.utils.logger_config import configure_logger


_logger = configure_logger(__name__)


def _parse_datetime(base_date: str, base_time: str) -> datetime:
    naive = datetime.strptime(f"{base_date}{base_time}", "%Y%m%d%H%M")
    return naive.replace(tzinfo=timezone.utc)


def extract_measurements(payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Transform the raw KMA payload into a flat list of rows."""

    response_body = payload.get("response", {}).get("body", {})
    items: Iterable[Mapping[str, Any]] = response_body.get("items", [])
    base_date = response_body.get("baseDate")
    base_time = response_body.get("baseTime")

    if not base_date or not base_time:
        raise ValueError("KMA payload missing base date/time metadata")

    observed_at = _parse_datetime(base_date, base_time)

    rows: List[Dict[str, Any]] = []
    for item in items:
        row = {
            "station_id": item.get("stationId"),
            "observed_at": observed_at,
            "category": item.get("category"),
            "value": item.get("obsrValue"),
            "unit": item.get("unit", ""),
            "created_at": datetime.now(tz=timezone.utc),
        }
        rows.append(row)

    _logger.info("Parsed KMA payload", extra={"rows": len(rows)})
    return rows


def parse_asos_raw(raw_data: str) -> List[Dict[str, Any]]:
    """Parse ASOS (지상관측) raw data from KMA API"""
    try:
        lines = raw_data.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

        parsed_data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 3:
                # 기본 파싱 (실제 포맷에 맞게 조정 필요)
                parsed_data.append({
                    "station_id": parts[1] if len(parts) > 1 else "unknown",
                    "observed_at": _parse_datetime_from_line(parts[0]) if parts[0] else datetime.now(tz=timezone.utc),
                    "category": "asos",
                    "value": parts[2] if len(parts) > 2 else None,
                    "unit": "",
                    "created_at": datetime.now(tz=timezone.utc),
                    "raw_line": line
                })

        _logger.info(f"Parsed ASOS data: {len(parsed_data)} records")
        return parsed_data
    except Exception as e:
        _logger.error(f"Failed to parse ASOS data: {e}")
        return []


def parse_pm10_raw(raw_data: str) -> List[Dict[str, Any]]:
    """Parse PM10 (황사) raw data from KMA API"""
    try:
        lines = raw_data.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

        parsed_data = []
        for line in data_lines:
            # PM10 데이터는 쉼표로 구분됨
            parts = line.split(',')
            if len(parts) >= 3:
                # 시간과 관측소 ID 추출
                datetime_str = parts[0].strip() if parts[0] else ""
                station_id = parts[1].strip() if len(parts) > 1 else "unknown"
                pm10_value = parts[2].strip() if len(parts) > 2 else None

                # 숫자가 아닌 값 필터링
                try:
                    if pm10_value and pm10_value.isdigit():
                        pm10_value = int(pm10_value)
                    else:
                        pm10_value = None
                except:
                    pm10_value = None

                parsed_data.append({
                    "station_id": station_id,
                    "observed_at": _parse_datetime_from_line(datetime_str) if datetime_str else datetime.now(tz=timezone.utc),
                    "category": "pm10",
                    "value": pm10_value,
                    "unit": "μg/m³",
                    "created_at": datetime.now(tz=timezone.utc),
                    "raw_line": line
                })

        _logger.info(f"Parsed PM10 data: {len(parsed_data)} records")
        return parsed_data
    except Exception as e:
        _logger.error(f"Failed to parse PM10 data: {e}")
        return []


def parse_uv_raw(raw_data: str) -> List[Dict[str, Any]]:
    """Parse UV (자외선) raw data from KMA API"""
    try:
        lines = raw_data.strip().split('\n')
        data_lines = [line for line in lines if not line.startswith('#') and line.strip()]

        parsed_data = []
        for line in data_lines:
            parts = line.split()
            if len(parts) >= 5:  # UV 데이터는 더 많은 컬럼이 있음
                parsed_data.append({
                    "station_id": parts[1] if len(parts) > 1 else "unknown",
                    "observed_at": _parse_datetime_from_line(parts[0]) if parts[0] else datetime.now(tz=timezone.utc),
                    "category": "uv",
                    "value": parts[2] if len(parts) > 2 else None,  # UVB
                    "uva_value": parts[3] if len(parts) > 3 else None,
                    "euv_value": parts[4] if len(parts) > 4 else None,
                    "unit": "W/m²",
                    "created_at": datetime.now(tz=timezone.utc),
                    "raw_line": line
                })

        _logger.info(f"Parsed UV data: {len(parsed_data)} records")
        return parsed_data
    except Exception as e:
        _logger.error(f"Failed to parse UV data: {e}")
        return []


def _parse_datetime_from_line(datetime_str: str) -> datetime:
    """Parse datetime from KMA API line format (YYYYMMDDHHMM)"""
    try:
        if len(datetime_str) == 12:  # YYYYMMDDHHMM
            return datetime.strptime(datetime_str, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        elif len(datetime_str) == 10:  # YYMMDDHHMM
            return datetime.strptime(f"20{datetime_str}", "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
        else:
            return datetime.now(tz=timezone.utc)
    except ValueError:
        return datetime.now(tz=timezone.utc)


__all__ = ["extract_measurements", "parse_asos_raw", "parse_pm10_raw", "parse_uv_raw"]
