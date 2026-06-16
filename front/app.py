import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="FocusFlow Pro", page_icon="⏱️", layout="wide")

BACKEND_URL = "http://backend:8000"

st.title("⏱️ FocusFlow: 고도화된 몰입 분석 및 루틴 최적화 엔진")
st.markdown("입력된 행동 로그를 다각도로 정밀 교차 분석하여 개인 맞춤형 타임라인 최적화 솔루션을 제공합니다.")

tab1, tab2 = st.tabs(["📝 일과 기록하기", "📊 고도화 분석 대시보드"])

# --- 탭 1: 기록 입력 폼 (기존 구조 유지) ---
with tab1:
    st.subheader("새로운 일과 데이터 입력")
    with st.form("log_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("날짜(Date)", date.today())
            granular_time_slots = [f"{i:02d}:00-{i+1:02d}:00" for i in range(24)]
            time_slot = st.sidebar.selectbox("⏰ 시간대", granular_time_slots)
            
            period_type = st.radio("기간 유형", ["평시", "시험기간", "방학"], horizontal=True)
        with col2:
            activity = st.text_input("활동(Activity) (예: 공부, 데이터베이스, 운동 등)")
            focus_score = st.slider("집중도 (1: 매우 산만함 ~ 5: 완전 몰입)", 1, 5, 3)
            
        st.write("")
        submit = st.form_submit_button("🚀 실시간 기록 저장하기")

        if submit:
            payload = {
                "date": str(log_date),
                "time_slot": time_slot,
                "activity": activity,
                "focus_score": focus_score,
                "period_type": period_type
            }
            try:
                res = requests.post(f"{BACKEND_URL}/log", json=payload)
                if res.status_code == 200:
                    st.success("🎯 행동 로그가 백엔드 JSON 파일 데이터셋에 안전하게 동기화되었습니다!")
            except Exception as e:
                st.error("백엔드 분석 서버에 연결할 수 없습니다.")

# --- 탭 2: 고도화 분석 대시보드 ---
with tab2:
    st.subheader("📊 다차원 행동 데이터 정밀 리포트")
    
    filter_type = st.selectbox("분석 데이터 범위 필터 선택", ["전체", "평시", "시험기간", "방학"])
    
    if st.button("🔄 실시간 다차원 교차 분석 수행"):
        try:
            with st.spinner("FastAPI 알고리즘 엔진이 Pandas 연산을 수행 중입니다..."):
                analyze_res = requests.post(f"{BACKEND_URL}/analyze", json={"period_type": filter_type})
            
            if analyze_res.status_code == 200:
                data = analyze_res.json()
                
                if "error" in data:
                    st.warning(data["error"])
                else:
                    # 상단 핵심 메트릭스 카드 
                    st.write("")
                    m1, m2, m3 = st.columns(3)
                    m1.metric("🔥 최적 집중 요일", data["golden_weekday"])
                    m2.metric("🎯 피크 몰입 시간대", data["golden_time"])
                    m3.metric("📂 누적 총 데이터 수", f"{data['total_logs']} 건")
                    
                    st.divider()

                    # [추가 기능 2] 이상 패턴 감지 알림 배너 출력
                    st.subheader("🚨 실시간 신체 바이오리듬 및 이상 패턴 감지")
                    status = data["anomaly_status"]
                    if status == "warning":
                        st.warning(data["anomaly_msg"])
                    elif status == "success":
                        st.success(data["anomaly_msg"])
                    else:
                        st.info(data["anomaly_msg"])

                    st.divider()

                    # 시각화 파트 (시간대별 + 요일별 나란히 배치)
                    g1, g2 = st.columns(2)
                    with g1:
                        st.subheader("📈 [기존] 시간대별 평균 집중도")
                        chart_df = pd.DataFrame(data["chart_data"])
                        st.bar_chart(chart_df.set_index("time_slot"), color="#29b6f6")
                        
                    with g2:
                        # [추가 기능 1] 요일별 집중도 분석 및 시각화
                        st.subheader("📅 [신규] 요일별 평균 집중도 추이")
                        wk_chart_df = pd.DataFrame(data["weekday_chart_data"])
                        st.bar_chart(wk_chart_df.set_index("weekday"), color="#ab47bc")
                        st.caption(f"💡 요일 추천 가이드: {data['weekday_recommendation']}")

                    st.divider()

                    # [추가 기능 3] 일정 재배치 최적화 제안
                    st.subheader("🔄 활동별 일과 재배치 가이드라인 (Re-allocation)")
                    for rec in data["reschedule_recommendations"]:
                        if rec.startswith("🚨"):
                            st.error(rec)    # 빨간색 배경 (2.0 미만 치명적 경고)
                        elif rec.startswith("⚠️"):
                            st.warning(rec)  # 노란색 배경 (3.5 미만 주의)
                        elif rec.startswith("💡"):
                            st.info(rec)     # 파란색 배경 (재배치 꿀팁)
                        elif rec.startswith("✅"):
                            st.success(rec)  # 초록색 배경 (현재 완벽함)
                        else:
                            st.write(rec)

                    # [추가 기능 4] 자동 분석 리포트 카드 디자인 렌더링
                    st.subheader("📋 FocusFlow AI 자동 분석 종합 보고서")
                    with st.container(border=True):
                        st.markdown("### 🔍 이번 주차 주요 데이터 진단")
                        for bullet in data["report"]["bullets"]:
                            st.markdown(f"- {bullet}")
                        st.markdown("---")
                        st.markdown(f"### 🎯 총평 및 행동 조언")
                        st.success(data["report"]["summary"])

            # 하단 테이블 뷰 복구
            logs_res = requests.get(f"{BACKEND_URL}/logs")
            if logs_res.status_code == 200:
                logs_data = logs_res.json()
                df_logs = pd.DataFrame(logs_data)
                if filter_type != "전체" and not df_logs.empty:
                    df_logs = df_logs[df_logs["period_type"] == filter_type]
                if not df_logs.empty:
                    st.divider()
                    st.subheader("📜 데이터 원본 상세 활동 로그")
                    st.dataframe(df_logs, use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"데이터 통신 처리 중 오류가 발생했습니다: {str(e)}")

    # 초기화 기능 유지
    st.write("")
    if st.sidebar.button("🗑️ 모든 데이터 초기화"):
        try:
            res = requests.post(f"{BACKEND_URL}/reset")
            if res.status_code == 200:
                st.sidebar.success("데이터 리셋 완료")
                st.rerun()
        except Exception:
            st.sidebar.error("초기화 실패")