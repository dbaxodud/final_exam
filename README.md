# ⏱️ FocusFlow

> **데이터 기반 집중도 분석 및 루틴 재배치 추천 서비스**

FocusFlow는 사용자의 일과와 집중도 데이터를 기록하고, 이를 분석하여 **가장 집중이 잘 되는 시간대와 요일을 찾아 최적의 루틴을 추천하는 데이터 기반 추천 웹 애플리케이션**입니다.

---

## 📌 프로젝트 소개

기존의 일정 관리 서비스는 사용자의 활동을 단순히 기록하는 기능에 초점을 맞추고 있습니다.

FocusFlow는 사용자가 입력한 활동 데이터를 **Pandas 기반으로 다차원 분석**하여,

* 가장 집중이 잘 되는 시간대(Golden Time)
* 가장 집중이 잘 되는 요일
* 최근 집중도 변화
* 활동별 최적 수행 시간

등을 분석하고, 이를 기반으로 **개인 맞춤형 루틴 재배치 가이드**를 제공합니다.

---

## ✨ 주요 기능

### 📝 일과 기록

* 날짜 입력
* 시간대 선택
* 활동 입력
* 집중도(1~5점) 기록
* 기간 유형(평시 / 시험기간 / 방학) 선택

모든 데이터는 JSON 파일에 저장되어 Docker 컨테이너 재시작 후에도 유지됩니다.

---

### 📊 시간대별 집중도 분석

Pandas를 이용하여 시간대별 평균 집중도를 계산합니다.

* Golden Time 탐색
* 시간대별 막대그래프 제공

---

### 📅 요일별 집중도 분석

입력된 날짜를 이용하여 요일을 자동 계산합니다.

이를 기반으로

* 요일별 평균 집중도
* 가장 효율적인 요일 추천

을 제공합니다.

---

### 🚨 이상 패턴 감지

최근 기록과 전체 평균 집중도를 비교하여

* 집중도 감소
* 집중도 증가
* 정상 상태

를 판단하고 사용자에게 피드백을 제공합니다.

---

### 🔄 활동별 일정 재배치 추천

활동별 평균 집중도를 시간대별로 분석하여

예를 들어

* 공부 → 오전 추천
* 운동 → 저녁 추천

과 같이 가장 효율적인 시간대로 루틴 재배치를 제안합니다.

---

### 📋 자동 분석 리포트

분석 결과를 종합하여

* 핵심 분석 결과
* 주요 활동 분석
* 이상 패턴
* 최종 추천

을 하나의 리포트 형태로 제공합니다.

---

## 🛠️ 기술 스택

### Frontend

* Streamlit

### Backend

* FastAPI

### Data Analysis

* Pandas
* NumPy

### Deployment

* Docker
* Docker Compose
* AWS EC2

### Storage

* JSON File

---

## 🏗️ 시스템 구조

```text
사용자

↓

Streamlit (Frontend)

↓

HTTP Request

↓

FastAPI (Backend)

↓

Pandas 데이터 분석

↓

추천 결과(JSON)

↓

Streamlit 시각화
```

---

## 📂 프로젝트 구조

```text
FocusFlow/

├── front/
│   ├── app.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── back/
│   ├── main.py
│   ├── data/
│   │   └── daily_logs.json
│   ├── Dockerfile
│   └── requirements.txt
│
├── docker-compose.yml
├── .gitignore
└── README.md
```

---

## 🚀 실행 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd FocusFlow
```

### 2. Docker 실행

```bash
docker compose up --build
```

### 3. 접속

Frontend

```
http://localhost:8501
```

Backend

```
http://localhost:8000/docs
```

---

## 📈 데이터 분석 흐름

```text
사용자 입력

↓

JSON 저장

↓

Pandas 데이터 분석

↓

시간대 분석

요일 분석

활동 분석

이상 패턴 감지

↓

추천 결과 생성

↓

Streamlit 시각화
```

---

## 🎯 프로젝트 특징

* Streamlit과 FastAPI를 분리한 구조
* REST API 기반 프론트엔드-백엔드 통신
* Pandas를 활용한 데이터 기반 추천
* Docker Compose 기반 멀티 컨테이너 환경
* JSON 파일을 이용한 데이터 영속성
* AWS EC2 환경에서 서비스 배포
* 개인 맞춤형 루틴 재배치 추천 기능 제공

---

## 👨‍💻 개발 환경

* Python 3.x
* Streamlit
* FastAPI
* Pandas
* NumPy
* Docker
* Docker Compose
* AWS EC2
