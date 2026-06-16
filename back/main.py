from fastapi import FastAPI
from pydantic import BaseModel
import json
import os
import pandas as pd
import numpy as np

app = FastAPI(title="FocusFlow Advanced API")
DATA_FILE = "data/daily_logs.json"

# 초기 데이터 파일 안전장치
if not os.path.exists("data"):
    os.makedirs("data")
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)

class LogEntry(BaseModel):
    date: str
    time_slot: str
    activity: str
    focus_score: int
    period_type: str

class AnalyzeRequest(BaseModel):
    period_type: str = "전체"

@app.post("/log")
def add_log(entry: LogEntry):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)
    logs.append(entry.model_dump())
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)
    return {"status": "success", "message": "기록이 저장되었습니다."}

@app.get("/logs")
def get_logs():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@app.post("/reset")
def reset_logs():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f)
    return {"status": "success", "message": "모든 데이터가 초기화되었습니다."}


@app.post("/analyze")
def analyze_logs(req: AnalyzeRequest):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    if not logs or len(logs) < 1:
        return {"error": "분석할 데이터가 부족합니다. 먼저 일과를 기록해주세요."}

    df = pd.DataFrame(logs)

    # 기본 필터링 (평시/시험기간/방학)
    if req.period_type != "전체":
        df = df[df["period_type"] == req.period_type]
    
    if df.empty:
        return {"error": f"'{req.period_type}' 기간에 해당하는 데이터가 없습니다."}

    # 기존 로직: 시간대별 평균 집중도 계산
    avg_time_scores = df.groupby("time_slot")["focus_score"].mean().reset_index()
    golden_time_row = avg_time_scores.loc[avg_time_scores["focus_score"].idxmax()]
    golden_time = str(golden_time_row["time_slot"])
    golden_time_score = round(float(golden_time_row["focus_score"]), 2)

    # ----------------------------------------------------
    # [추가 기능 1] 요일별 집중도 분석 (자동 계산)
    # ----------------------------------------------------
    df["date_dt"] = pd.to_datetime(df["date"])
    # 0=월요일, 1=화요일 ... 형태로 매핑
    weekday_map = {0: "월요일", 1: "화요일", 2: "수요일", 3: "목요일", 4: "금요일", 5: "토요일", 6: "일요일"}
    df["weekday"] = df["date_dt"].dt.weekday.map(weekday_map)
    
    # 요일 순서 고정을 위해 reindex 처리
    weekday_order = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
    avg_weekday_scores = df.groupby("weekday")["focus_score"].mean().reindex(weekday_order).dropna().reset_index()
    
    golden_weekday_row = avg_weekday_scores.loc[avg_weekday_scores["focus_score"].idxmax()]
    golden_weekday = str(golden_weekday_row["weekday"])
    golden_weekday_score = round(float(golden_weekday_row["focus_score"]), 2)
    
    weekday_recommendation = f"{golden_weekday}의 집중도가 가장 높습니다. 중요한 공부나 과제는 {golden_weekday}에 배치하는 것을 추천합니다."
    
    # ----------------------------------------------------
    # [추가 기능 2] 이상 패턴 감지 (전체 vs 최근 7개 비교)
    # ----------------------------------------------------
    overall_mean = round(float(df["focus_score"].mean()), 2)
    recent_logs = df.tail(7)
    recent_mean = round(float(recent_logs["focus_score"].mean()), 2)
    
    # 임계값(0.3점) 기준으로 상태 판정
    if overall_mean - recent_mean >= 0.3:
        anomaly_msg = f"최근 7개 기록의 평균 집중도({recent_mean}점)가 전체 평균({overall_mean}점)보다 크게 감소했습니다. 충분한 휴식이나 루틴 점검을 권장합니다."
        anomaly_status = "warning"
    elif recent_mean - overall_mean >= 0.3:
        anomaly_msg = f"최근 7개 기록의 평균 집중도({recent_mean}점)가 전체 평균({overall_mean}점)보다 향상되고 있습니다. 아주 훌륭한 리듬입니다. 현재 루틴을 유지해보세요!"
        anomaly_status = "success"
    else:
        anomaly_msg = f"최근 집중도({recent_mean}점)가 평소 균형({overall_mean}점)을 안정적으로 유지하고 있습니다."
        anomaly_status = "info"

    # ----------------------------------------------------
    # [추가 기능 3] 일정 재배치 추천 (활동별 최적 시간대)
    # ----------------------------------------------------
# ----------------------------------------------------
    # [추가 기능 3] 일정 재배치 추천 (활동별 최적 시간대)
    # ----------------------------------------------------
    act_time_avg = df.groupby(["activity", "time_slot"])["focus_score"].mean().reset_index()
    reschedule_recommendations = []
    
    best_slots = act_time_avg.loc[act_time_avg.groupby("activity")["focus_score"].idxmax()]
    
    for _, row in best_slots.iterrows():
        act = str(row["activity"])
        b_slot = str(row["time_slot"])
        b_score = round(float(row["focus_score"]), 2)
        
        act_df = df[df["activity"] == act]
        most_frequent_slot = str(act_df["time_slot"].mode()[0]) if not act_df.empty else b_slot
        
        # 점수 및 시간대 일치 여부에 따른 자연스러운 문장 생성
        if b_score < 2.0:
            if most_frequent_slot != b_slot:
                rec_text = f"🚨 '{act}' 활동을 주로 {most_frequent_slot}에 하시지만, 가장 나은 {b_slot}의 집중도조차 {b_score}점으로 치명적으로 낮습니다. 시간대 전면 재배치와 휴식이 시급합니다."
            else:
                rec_text = f"🚨 '{act}'의 최고 집중도가 {b_score}점({b_slot})으로 매우 심각합니다. 당장 다른 시간대로 변경하거나 학습 방식을 전면 수정하세요!"
        elif b_score < 3.5:
            if most_frequent_slot != b_slot:
                rec_text = f"⚠️ '{act}'를 {most_frequent_slot} 대신 {b_slot}로 옮기면 나아지겠지만, 최고 점수({b_score}점)가 여전히 낮습니다. 전반적인 루틴 점검이 필요합니다."
            else:
                rec_text = f"⚠️ '{act}'를 {b_slot}에 계속 하고 계시나, 최고 집중도({b_score}점)가 저조합니다. 환경 개선이나 환기가 필요합니다."
        else:
            if most_frequent_slot != b_slot:
                rec_text = f"💡 '{act}'를 주로 {most_frequent_slot}에 하시는데, {b_slot}로 옮기면 최고 효율({b_score}점)을 낼 수 있습니다. 시간표 조정을 강력 추천합니다!"
            else:
                rec_text = f"✅ '{act}' 활동은 현재 시간대({b_slot})에서 완벽한 효율({b_score}점)을 내고 있습니다. 지금의 좋은 리듬을 계속 유지하세요!"

        reschedule_recommendations.append(rec_text)
    # ----------------------------------------------------
    # [추가 기능 4] 자동 분석 리포트 요약 생성
    # ----------------------------------------------------
    # 주요 활동 하나의 데이터 예시 추출
    top_activity = "없음"
    top_activity_score = 0.0
    if not df.empty:
        act_counts = df["activity"].value_counts()
        if not act_counts.empty:
            main_act = act_counts.index[0]
            main_act_df = df[df["activity"] == main_act]
            top_activity = str(main_act)
            top_activity_score = round(float(main_act_df["focus_score"].mean()), 2)

    report_bullets = [
        f"피크 타임라인: 하루 중 {golden_time} 시간대에 평균 {golden_time_score}점으로 가장 몰입했습니다.",
        f"요일별 패턴: 일주일 중 {golden_weekday}에 평균 {golden_weekday_score}점으로 가장 높은 능률을 보였습니다.",
        f"주요 활동 분석: 가장 자주 기록된 '{top_activity}' 활동의 평균 집중도는 {top_activity_score}점입니다.",
        f"추이 분석: {anomaly_msg}"
    ]
    
    report_summary = f"핵심 제안: 최상의 효율을 내기 위해 가장 중요한 과제나 심화 학습은 {golden_weekday} 또는 하루 일과 중 {golden_time}에 우선 배치하는 배정 전략을 권장합니다."

    return {
        # 기존 응답 포맷 유지
        "golden_time": golden_time,
        "average_score": golden_time_score,
        "total_logs": int(len(df)),
        "chart_data": avg_time_scores.to_dict(orient="records"),
        
        # 신규 기능 응답 데이터 추가
        "weekday_chart_data": avg_weekday_scores.to_dict(orient="records"),
        "golden_weekday": golden_weekday,
        "golden_weekday_score": golden_weekday_score,
        "weekday_recommendation": weekday_recommendation,
        
        "anomaly_msg": anomaly_msg,
        "anomaly_status": anomaly_status,
        
        "reschedule_recommendations": reschedule_recommendations,
        
        "report": {
            "bullets": report_bullets,
            "summary": report_summary
        }
    }