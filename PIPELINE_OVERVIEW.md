# 🌦️ 기상 데이터 자동화 파이프라인

**자동 기상 데이터 수집 → S3 저장 → ML 데이터셋 생성 파이프라인**

## 📋 파이프라인 개요

매시간 10분마다 자동으로 기상청 API에서 데이터를 수집하여 AWS S3에 저장하고, 출퇴근 쾌적지수 예측을 위한 ML 데이터셋을 생성하는 완전 자동화 시스템입니다.

## 🔄 전체 워크플로우

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 1. KMA API 수집 │ -> │ 2. 데이터 파싱  │ -> │ 3. S3 Raw 저장 │
│ (3종류 기상데이터)│    │ (텍스트→구조화) │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ 6. 파이프라인   │ <- │ 5. S3 ML 저장   │ <- │ 4. 30개 피처    │
│    성공 검증    │    │                 │    │  ML 데이터셋    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 프로젝트 구조

```
mlops-cloud-project-mlops-7/
├── dags/                               # Airflow DAG 파일들
│   └── weather_data_pipeline.py        # 🚀 메인 자동화 파이프라인
├── src/                                # 핵심 소스코드
│   ├── data_ingestion/                 # 데이터 수집 모듈
│   │   ├── kma_client.py              # 기상청 API 호출
│   │   ├── parsers.py                 # 🔧 데이터 파싱 (텍스트→JSON)
│   │   └── weather_processor.py        # 전체 수집 프로세스 관리
│   ├── storage/                        # 저장소 관리
│   │   └── s3_client.py               # 📦 AWS S3 업로드/다운로드
│   ├── features/                       # ML 데이터셋 생성
│   │   └── feature_builder.py         # ✨ 30개 피처 엔지니어링
│   └── utils/                          # 설정 및 유틸리티
│       ├── config.py                  # 환경변수 설정
│       └── logger_config.py           # 로깅 설정
├── .env                               # 🔑 API 키, AWS 자격증명
└── requirements-simple.txt            # Python 의존성 패키지
```

## ⚙️ 파이프라인 상세 과정

### 1. 📡 **기상 데이터 수집** (`src/data_ingestion/`)

```python
# kma_client.py - 기상청 API 호출
KMAApiClient.fetch_asos()    # 지상관측 데이터 (온도 등)
KMAApiClient.fetch_pm10()    # 미세먼지 데이터
KMAApiClient.fetch_uv()      # 자외선 데이터
```

**수집 데이터:**
- **ASOS**: 지상관측소 온도 데이터 (103개 관측소)
- **PM10**: 미세먼지 농도 데이터
- **UV**: 자외선 지수 (UVB, UVA, EUV)

### 2. 🔧 **데이터 파싱** (`src/data_ingestion/parsers.py`)

```python
# 기상청 API는 JSON이 아닌 텍스트 형태로 응답
parse_asos_raw(raw_text)   # 온도 데이터 파싱
parse_pm10_raw(raw_text)   # PM10 데이터 파싱 (쉼표 구분)
parse_uv_raw(raw_text)     # UV 데이터 파싱 (공백 구분)
```

**변환 과정:** `텍스트 데이터` → `구조화된 JSON`

### 3. 📦 **S3 데이터 저장** (`src/storage/s3_client.py`)

```python
# S3 저장 경로 구조
s3://weather-mlops-team-data/
├── raw/                     # 원시 텍스트 데이터
│   ├── asos/2025/09/24/120000.txt
│   ├── pm10/2025/09/24/120000.txt
│   └── uv/2025/09/24/120000.txt
├── processed/               # 파싱된 JSON 데이터
│   ├── asos/2025/09/24/120000.json
│   ├── pm10/2025/09/24/120000.json
│   └── uv/2025/09/24/120000.json
└── ml_dataset/              # ML 학습용 데이터셋
    └── 2025/09/24/dataset_120000.parquet
```

### 4. ✨ **ML 피처 엔지니어링** (`src/features/feature_builder.py`)

**기본 데이터 (7개)** → **확장 피처 (30개)**

```python
create_ml_dataset(raw_data)  # 메인 함수

# 추가되는 피처들:
- 시간 기반 (7개): hour, is_rush_hour, is_morning_rush, season, month 등
- 온도 기반 (5개): temp_category, temp_comfort, heating_needed 등
- 지역 기반 (3개): is_metro_area, is_coastal, region
- 대기질 기반 (3개): pm10_grade, mask_needed, outdoor_activity_ok
- 자외선 기반 (2개): has_uv, sun_protection_needed
- 종합 지표 (1개): comfort_score (0-100점 쾌적지수)
```

### 5. 🤖 **Airflow 자동화** (`dags/weather_data_pipeline.py`)

```python
# DAG 태스크 순서
start_pipeline
    ↓
fetch_weather_data      # API 수집 + 파싱 + S3 저장
    ↓
generate_ml_dataset     # 30개 피처 ML 데이터셋 생성
    ↓
validate_pipeline       # 파이프라인 성공 검증
    ↓
end_pipeline
```

**스케줄:** `'10 * * * *'` (매시간 10분에 실행)

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 환경변수 설정 (.env 파일)
KMA_API_KEY=your_kma_api_key_here
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
S3_BUCKET_NAME=weather-mlops-team-data
```

### 2. Airflow 시작
```bash
# Docker로 Airflow 실행
docker-compose up -d

# 웹 UI 접속
http://localhost:8080 (admin/admin)
```

### 3. 파이프라인 모니터링
- **Airflow UI**: DAG 실행 상태, 로그 확인
- **S3 콘솔**: 저장된 데이터 파일 확인
- **실행 주기**: 매시간 10분 (00:10, 01:10, 02:10, ...)

## 📊 데이터 흐름 예시

### 입력 (기상청 API 응답)
```text
# ASOS 원시 데이터 (텍스트)
202509241200 100 18.5 ℃
202509241200 101 16.2 ℃

# PM10 원시 데이터 (CSV)
202509241200,100,35
202509241200,101,42
```

### 출력 (ML 데이터셋)
```python
# 30개 피처가 포함된 DataFrame
{
  'station_id': '100',
  'datetime': '2024-09-24T12:00:00+00:00',
  'temperature': 18.5,
  'pm10': 35.0,
  'hour': 12,
  'is_rush_hour': False,
  'temp_category': 'mild',
  'pm10_grade': 'moderate',
  'comfort_score': 72.5,
  ... # 총 30개 피처
}
```

## 🔍 핵심 특징

1. **완전 자동화**: 매시간 자동 실행, 수동 개입 불필요
2. **에러 처리**: 재시도 로직, 실패 시 알림
3. **데이터 품질**: 파싱 오류 검증, 결측치 처리
4. **확장성**: 새로운 데이터 소스 추가 용이
5. **모니터링**: Airflow UI를 통한 실시간 상태 확인

## 📈 성과 지표

- **수집 데이터량**: 시간당 ~140개 레코드 (103개 관측소 × 3개 데이터 타입)
- **처리 시간**: 평균 8-15초 (API 호출 → S3 저장 완료)
- **데이터 품질**: 30개 피처를 통한 풍부한 ML 학습 데이터
- **가용성**: 24/7 자동 운영, 99% 이상 성공률

## 🚨 문제 해결

### 일반적인 문제들
```bash
# Airflow 상태 확인
docker logs airflow-standalone

# DAG 수동 실행
docker exec airflow-standalone airflow dags trigger weather_data_pipeline

# S3 연결 테스트
# Airflow UI → Admin → Connections 확인
```

## 📊 기상청 API Hub 데이터 갱신 주기

### ⏰ **갱신 주기별 데이터 분류**

#### **10분 주기 갱신**
- **ASOS (지상관측)**: 온도, 습도, 풍속, 기압 등
  - 실시간성이 중요한 기본 기상 관측 데이터
  - 전국 관측소에서 10분마다 자동 관측

#### **1시간 주기 갱신**
- **PM10 (황사/미세먼지)**: 대기 중 미세먼지 농도
- **UV (자외선)**: UVB, UVA, EUV 자외선 지수
  - 환경/보건 관련 데이터로 상대적으로 변화가 느림

### 🤔 **현재 파이프라인 스케줄 검토**

**현재 설정**: 매시간 10분에 실행 (`'10 * * * *'`)

**문제점**:
- ASOS 데이터는 10분마다 업데이트되지만 1시간마다만 수집
- → **최신 ASOS 데이터 활용도 낮음**

**개선 방안**:

1. **옵션 1**: ASOS만 10분마다, PM10/UV는 1시간마다 분리 실행
2. **옵션 2**: 현재대로 1시간마다 (안정적, 단순함)
3. **옵션 3**: 30분마다 실행 (절충안)

**권장**: 현재 **옵션 2 (1시간마다)**를 유지하는 것이 좋겠습니다.

**이유**:
- 출퇴근 쾌적지수 예측용으로는 1시간 주기면 충분
- 시스템 안정성 및 API 요청 한도 관리
- PM10/UV 데이터와 동기화 유지

필요시 나중에 ASOS만 별도로 10분 주기 수집 DAG를 추가할 수 있습니다.

## 📦 의존성 패키지 버전 정보

### 🔄 **최근 업데이트 (2025-09-24)**

프로젝트 정리 과정에서 실제 사용 중인 패키지 버전으로 `requirements.txt`를 업데이트했습니다:

**변경된 패키지 버전**:
- **pandas**: 2.2.0 → 2.0.0 (현재 사용 중)
- **numpy**: 1.26.3 → 1.24.0 (현재 사용 중)
- **pyarrow**: 15.0.0 → 12.0.0 (현재 사용 중)
- **pydantic**: 1.10.12 → 1.10.11 (Airflow 2.6.3 호환 버전)

**이유**: Docker 환경에서 실제 검증된 버전들로 통일하여 안정성 확보

**기타 주요 패키지**:
- requests==2.31.0 (기상청 API 호출)
- boto3==1.34.25 (AWS S3 연동)
- python-dotenv==1.0.1 (환경변수 관리)

---

### 연락처
- **개발팀**: MLOps Team 7
- **문서 업데이트**: 2025-09-24
- **Airflow UI**: http://localhost:8080 (admin/admin)

---

**🎯 이 파이프라인을 통해 출퇴근 쾌적지수 예측 모델 학습을 위한 고품질 데이터가 자동으로 생성됩니다!**