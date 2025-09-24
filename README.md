# 프로젝트 이름

<br>

## 💻 프로젝트 소개
### <프로젝트 소개>
- _이번 프로젝트에 대해 소개를 작성해주세요_

### <작품 소개>
- _만드신 작품에 대해 간단한 소개를 작성해주세요_

<br>

## 👨‍👩‍👦‍👦 팀 구성원

| ![박패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![이패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![최패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![김패캠](https://avatars.githubusercontent.com/u/156163982?v=4) | ![오패캠](https://avatars.githubusercontent.com/u/156163982?v=4) |
| :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: | :--------------------------------------------------------------: |
|            [박패캠](https://github.com/UpstageAILab)             |            [이패캠](https://github.com/UpstageAILab)             |            [최패캠](https://github.com/UpstageAILab)             |            [김패캠](https://github.com/UpstageAILab)             |            [오패캠](https://github.com/UpstageAILab)             |
|                            팀장, 담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |                            담당 역할                             |

<br>

## 🔨 개발 환경 및 기술 스택
- 주 언어 : _ex) python_
- 버전 및 이슈관리 : _ex) github_
- 협업 툴 : _ex) github, notion_

<br>

## 📁 프로젝트 구조
```
weather-mlops/
├─ data/                          # 데이터 저장소
│  ├─ raw/                        # API 원천 데이터 그대로
│  ├─ interim/                    # 정제/전처리된 중간 데이터
│  └─ processed/                  # 최종 피처/지수 결과 테이블
│
├─ src/                           # 실제 코드
│  ├─ data/                       # 데이터 수집 및 전처리
│  │   ├─ kma_client.py           # 기상청 API 호출 (ASOS/UV/PM 등) (구현 예정)
│  │   ├─ fetch.py                # 여러 API 모듈 통합 호출 (구현 예정)
│  │   └─ preprocess.py           # 결측/타입 정리, 구간화 전 준비 (구현 예정)
│  │
│  ├─ features/                   # 피처 엔지니어링
│  │   ├─ penalty_rules.py        # 항목별 벌점(HeatPenalty, UVPenalty 등) (구현 예정)
│  │   └─ feature_builder.py      # 모든 피처/벌점 합쳐 DataFrame 생성 (구현 예정)
│  │
│  ├─ indices/                    # 지수 계산 로직
│  │   ├─ comfort_index.py        # 불쾌지수 → 쾌적지수 계산 함수 (구현 예정)
│  │   └─ weights.yaml            # 가중치 설정(Heat=0.45, UV=0.20 등) (구현 예정)
│  │
│  ├─ serving/                    # 서비스/배포
│  │   └─ app.py                  # FastAPI 엔드포인트 (/predict) (구현 예정)
│  │
│  └─ utils/                      # 공용 유틸
│      ├─ io.py                   # 데이터 저장/불러오기 (Parquet, CSV 등) (구현 예정)
│      ├─ config.py               # 설정 로더(pydantic/yaml) (구현 예정)
│      └─ logger.py               # 로깅 공통 (구현 예정)
│
├─ conf/
│  └─ config.yaml                 # API 키, 스테이션ID, 경로 등 공용 설정 (구현 예정)
│
├─ tests/                         # 테스트
│  ├─ test_penalty_rules.py       # 구간화/벌점 함수 단위 테스트 (구현 예정)
│  ├─ test_comfort_index.py       # 최종 지수 계산 검증 (구현 예정)
│  └─ test_api.py                 # FastAPI 응답 검증 (구현 예정)
│
├─ notebooks/                     # EDA 및 실험용
│  ├─ eda.ipynb                   # 데이터 탐색 (구현 예정)
│  └─ index_experiment.ipynb      # 가중치 실험/시각화 (구현 예정)
│
├─ .env.example                   # 예시 환경변수(KMA_API_KEY=...)
├─ requirements.txt               # 의존성 
├─ README.md                      # 프로젝트 설명/실행법
├─ Makefile                       # 자주 쓰는 명령어 단축 (fetch, build, serve 등) (구현 예정)
├─ .gitignore                     
├─ Dockerfile                     # 배포용
├─ Dockerfile.dev                 # 개발용
│
└─ .github
    └─ISSUE_TEMPLATE              # ISSYE 템플릿 작성 예시
       ├─ bug-data.yml            # 데이터 수집/정합성
       ├─ bug-feature.yml         # 피처 로직
       ├─ bug-infra.yml           # 학습 평가
       ├─ bug-pipeline.yml        # 서빙/API
       ├─ bug-serve.yml           # Airflow/오케스트레이션
       ├─ bug-train.yml           # CI/CD/도커/권한
       └─ bug.yml                 # 기본 

```

<br>
# 1. main 브랜치로 전환
git checkout main
git pull

# 2. 프로덕션 이미지 빌드 (소스코드 포함)
docker build \
  --target collector \
  -t weather-collector:v1.0.0 \
  -f Dockerfile.multi .

# 3. 테스트
docker run --env-file .env weather-collector:v1.0.0

# 4. 이미지 레지스트리에 푸시
docker tag weather-collector:v1.0.0 your-registry/weather-collector:v1.0.0
docker push your-registry/weather-collector:v1.0.0
<br>

<br>

## 💻​ 구현 기능
### 기능1
- _작품에 대한 주요 기능을 작성해주세요_
### 기능2
- _작품에 대한 주요 기능을 작성해주세요_
### 기능3
- _작품에 대한 주요 기능을 작성해주세요_

<br>

## 🛠️ 작품 아키텍처(필수X)
- #### _아래 이미지는 예시입니다_
![이미지 설명](https://miro.medium.com/v2/resize:fit:4800/format:webp/1*ub_u88a4MB5Uj-9Eb60VNA.jpeg)

<br>

## 🚨​ 트러블 슈팅
### 1. OOO 에러 발견

#### 설명
- _프로젝트 진행 중 발생한 트러블에 대해 작성해주세요_

#### 해결
- _프로젝트 진행 중 발생한 트러블 해결방법 대해 작성해주세요_

<br>

## 📌 프로젝트 회고
### 박패캠
- _프로젝트 회고를 작성해주세요_

<br>

## 📰​ 참고자료
- _참고자료를 첨부해주세요_
