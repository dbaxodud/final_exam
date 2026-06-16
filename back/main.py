from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import pandas as pd
import numpy as np

app = FastAPI(title="FocusFlow Backend Engine")

DB_FILE = "logs.json"

class LogEntry(BaseModel):
    date: str
    time_slot: str
    activity: str
    focus_score: int
    period_type: str

class AnalysisRequest(BaseModel):
    period_type: str

def load_logs():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_logs(logs):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

@app.get("/logs")
def get_logs():
    return load_logs()

@app.post("/log")
def add_log(entry: LogEntry):
    logs = load_logs()
    logs.append(entry.dict())
    save_logs(logs)
    return {"status": "success", "message": "Log saved successfully"}

@app.delete("/log/{index}")
def delete_log(index: int):
    logs = load_logs()
    if index < 0 or index >= len(logs):
        raise HTTPException(status_code=404, detail="Log not found")
    removed = logs.pop(index)
    save_logs(logs)
    return {"status": "success", "deleted": removed}

@app.post("/reset")
def reset_logs():
    save_logs([])
    return {"status": "success", "message": "All data reset"}

@app.post("/analyze")
def analyze_data(req: AnalysisRequest):
    logs = load_logs()
    if not logs:
        return {"error": "No data available"}
    
    df = pd.DataFrame(logs)
    
    if req.period_type != "전체":
        df = df[df["period_type"] == req.period_type]
        if df.empty:
            return {"error": f"'{req.period_type}' 기간에 해당하는 데이터가 없습니다."}
            
    total_logs = len(df)
    
    time_grouped = df.groupby("time_slot")["focus_score"].mean().reset_index()
    chart_data = time_grouped.to_dict(orient="records")
    golden_time = time_grouped.sort_values(by="focus_score", ascending=False).iloc[0]["time_slot"]
    
    df['date_parsed'] = pd.to_datetime(df['date'])
    df['weekday'] = df['date_parsed'].dt.day_name()
    weekday_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df['weekday'] = pd.Categorical(df['weekday'], categories=weekday_order, ordered=True)
    
    weekday_grouped = df.groupby("weekday", observed=False)["focus_score"].mean().reset_index()
    ko_weekdays = {'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일', 
                   'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'}
    weekday_grouped['weekday'] = weekday_grouped['weekday'].map(ko_weekdays)
    weekday_chart_data = weekday_grouped.to_dict(orient="records")
    
    best_weekday_eng = df.groupby("weekday", observed=False)["focus_score"].mean().idxmax()
    golden_weekday = ko_weekdays[best_weekday_eng]

    activity_grouped = df.groupby("activity")["focus_score"].mean().sort_values(ascending=False).reset_index()
    activity_ranking = activity_grouped.to_dict(orient="records")

    trend_df = df.sort_values(by="date_parsed").tail(15)
    trend_data = trend_df[["date", "activity", "focus_score"]].to_dict(orient="records")

    recent_focus = df.sort_values(by="date_parsed").tail(3)["focus_score"].mean()
    if recent_focus <= 2.5:
        anomaly_status = "warning"
        anomaly_msg = f"⚠️ 경고: 최근 3회 평균 몰입도가 {recent_focus:,.1f}로 급감했습니다. 번아웃 위험이 감지되니 휴식을 권장합니다."
    elif recent_focus >= 4.5:
        anomaly_status = "success"
        anomaly_msg = f"🔥 최고조: 최근 몰입 성과가 {recent_focus:,.1f}로 최상위권입니다. 러너스 하이 상태를 활용해 까다로운 과제에 도전하세요."
    else:
        anomaly_status = "info"
        anomaly_msg = "✅ 안정적: 바이오리듬이 평온한 상태를 유지하고 있습니다. 현재 루틴을 신뢰하세요."

    reschedule_recs = []
    for act, group in df.groupby("activity"):
        avg_score = group["focus_score"].mean()
        if avg_score < 2.5:
            reschedule_recs.append(f"🚨 **{act}**: 현재 평균 몰입도({avg_score:.1f}점)가 매우 낮습니다. 다른 요일이나 다른 피크 몰입 시간대로 배치를 전면 수정하세요.")
        elif avg_score < 3.8:
            reschedule_recs.append(f"⚠️ **{act}**: 몰입도({avg_score:.1f}점)가 다소 애매합니다. 중요도가 높은 작업이라면 다른 일정과 스와프(Swap)해보세요.")
        else:
            reschedule_recs.append(f"✅ **{act}**: 현재 아주 이상적인 몰입 효율({avg_score:.1f}점)을 보이고 있습니다. 고정 루틴으로 잠금하셔도 좋습니다.")

    bullets = [
        f"현재 분석 데이터셋의 총 누적 기록 수는 {total_logs}건입니다.",
        f"가장 높은 몰입도를 기록한 황금 시간대는 [{golden_time}] 코어 타임입니다.",
        f"통계적으로 평일/주말 통틀어 [{golden_weekday}]에 뇌의 활성도가 가장 높습니다."
    ]
    report_summary = f"종합 결과, 귀하는 현재 {golden_weekday} {golden_time}에 최고의 성과를 내고 있습니다. 창의적이거나 고도의 두뇌 회전이 필요한 전공 공부나 코딩 테스트 준비는 이 윈도우 시간대에 우선 배치하십시오."

    return {
        "total_logs": total_logs,
        "golden_time": golden_time,
        "golden_weekday": golden_weekday,
        "chart_data": chart_data,
        "weekday_chart_data": weekday_chart_data,
        "activity_ranking": activity_ranking,
        "trend_data": trend_data,
        "anomaly_status": anomaly_status,
        "anomaly_msg": anomaly_msg,
        "reschedule_recommendations": reschedule_recs,
        "report": {
            "bullets": bullets,
            "summary": report_summary
        }
    }