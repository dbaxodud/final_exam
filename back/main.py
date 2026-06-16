from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import pandas as pd

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
    return {"status": "success"}

@app.delete("/log/{index}")
def delete_log(index: int):
    logs = load_logs()
    if index < 0 or index >= len(logs):
        raise HTTPException(status_code=404, detail="Log not found")
    logs.pop(index)
    save_logs(logs)
    return {"status": "success"}

@app.post("/reset")
def reset_logs():
    save_logs([])
    return {"status": "success"}

@app.post("/analyze")
def analyze_data(req: AnalysisRequest):
    logs = load_logs()
    if not logs:
        return {"error": "데이터가 없습니다."}
    
    df = pd.DataFrame(logs)
    
    if req.period_type != "전체":
        df = df[df["period_type"] == req.period_type]
        if df.empty:
            return {"error": f"'{req.period_type}' 기간에 해당하는 데이터가 없습니다."}
            
    total_logs = len(df)
    
    # 1. 시간대 분석
    time_grouped = df.groupby("time_slot")["focus_score"].mean().reset_index()
    chart_data = time_grouped.to_dict(orient="records")
    golden_time = time_grouped.sort_values(by="focus_score", ascending=False).iloc[0]["time_slot"]
    
    # 2. 요일 분석 (안전한 매핑 방식 적용)
    df['date_parsed'] = pd.to_datetime(df['date'])
    df['weekday_eng'] = df['date_parsed'].dt.day_name()
    
    ko_weekdays = {'Monday': '월요일', 'Tuesday': '화요일', 'Wednesday': '수요일', 'Thursday': '목요일', 'Friday': '금요일', 'Saturday': '토요일', 'Sunday': '일요일'}
    df['weekday'] = df['weekday_eng'].map(ko_weekdays)
    
    weekday_grouped = df.groupby("weekday")["focus_score"].mean().reset_index()
    weekday_chart_data = weekday_grouped.to_dict(orient="records")
    golden_weekday = weekday_grouped.sort_values(by="focus_score", ascending=False).iloc[0]["weekday"]

    # 3. 활동 순위
    activity_grouped = df.groupby("activity")["focus_score"].mean().sort_values(ascending=False).reset_index()
    activity_ranking = activity_grouped.to_dict(orient="records")

    # 4. 추세
    trend_df = df.sort_values(by="date_parsed").tail(15)
    trend_data = trend_df[["date", "activity", "focus_score"]].to_dict(orient="records")

    # 5. 이상 패턴 감지
    recent_focus = trend_df.tail(3)["focus_score"].mean()
    if recent_focus <= 2.5:
        anomaly_status = "warning"
        anomaly_msg = f"⚠️ 경고: 최근 평균 몰입도가 {recent_focus:.1f}로 급감했습니다."
    elif recent_focus >= 4.5:
        anomaly_status = "success"
        anomaly_msg = f"🔥 최고조: 최근 몰입 성과가 {recent_focus:.1f}로 최상위권입니다."
    else:
        anomaly_status = "info"
        anomaly_msg = "✅ 안정적: 바이오리듬이 평온한 상태를 유지하고 있습니다."

    # 6. 재배치 가이드
    reschedule_recs = []
    for act, group in df.groupby("activity"):
        avg_score = group["focus_score"].mean()
        if avg_score < 2.5:
            reschedule_recs.append(f"🚨 **{act}**: 현재 평균 몰입도({avg_score:.1f}점)가 매우 낮습니다. 재배치를 권장합니다.")
        elif avg_score < 3.8:
            reschedule_recs.append(f"⚠️ **{act}**: 몰입도({avg_score:.1f}점)가 애매합니다. 스와프(Swap)를 고려하세요.")
        else:
            reschedule_recs.append(f"✅ **{act}**: 현재 몰입 효율({avg_score:.1f}점)이 아주 이상적입니다.")

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
            "bullets": [f"누적 데이터: {total_logs}건", f"최고 몰입 시간: {golden_time}", f"최적 몰입 요일: {golden_weekday}"],
            "summary": f"종합 결과, 현재 {golden_weekday} {golden_time}에 최고의 성과를 내고 있습니다."
        }
    }