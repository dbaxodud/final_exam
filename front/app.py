import streamlit as st
import requests
import pandas as pd
from datetime import date

# 1. 페이지 기본 설정 (와이드 레이아웃 적용)
st.set_page_config(page_title="FocusFlow Pro", page_icon="⏱️", layout="wide")

BACKEND_URL = "http://backend:8000"

# 2. 메인 타이틀 및 서비스 소개 영역
st.title("⏱️ FocusFlow")
st.markdown("**개인 맞춤형 타임라인 최적화 솔루션** | 일과를 기록하고 AI 기반 루틴 분석 리포트를 받아보세요.")

tab1, tab2 = st.tabs(["📝 일과 기록하기", "📊 종합 분석 대시보드"])

# ==========================================
# --- 탭 1: 기록 입력 폼 (UX 개선 및 유효성 검사 추가) ---
# ==========================================
with tab1:
    st.subheader("새로운 일과 데이터 입력")
    
    # 카드 형태의 컨테이너를 사용하여 입력 폼을 감쌈
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            log_date = st.date_input("📅 날짜 (Date)", date.today())
            
            # 1시간 단위 세밀한 시간대 설정
            granular_time_slots = [f"{i:02d}:00-{i+1:02d}:00" for i in range(24)]
            time_slot = st.selectbox("⏰ 시간대", granular_time_slots)
            
            period_type = st.radio("⏳ 기간 유형", ["평시", "시험기간", "방학"], horizontal=True)
            
        with col2:
            # [요구사항 1] 활동 입력 UI 개선 (selectbox + 직접 입력)
            activity_options = ["공부", "과제", "독서", "운동", "회의", "프로그래밍", "기타(직접 입력)"]
            selected_activity = st.selectbox("🎯 활동 (Activity)", activity_options)
            
            # '기타(직접 입력)' 선택 시 텍스트 입력창 표시
            custom_activity = ""
            if selected_activity == "기타(직접 입력)":
                custom_activity = st.text_input("📝 직접 입력 (활동명을 적어주세요)")
                
            focus_score = st.slider("🧠 집중도 (1: 산만함 ~ 5: 완전 몰입)", 1, 5, 3)

        st.write("") # 간격 조절
        submit_btn = st.button("🚀 기록 저장하기", use_container_width=True, type="primary")

        # [요구사항 2] 입력값 검증 (Validation)
        if submit_btn:
            # 최종 활동명 결정
            final_activity = custom_activity.strip() if selected_activity == "기타(직접 입력)" else selected_activity

            if not final_activity:
                st.error("🚨 활동명을 정확히 입력해주세요.")
            else:
                payload = {
                    "date": str(log_date),
                    "time_slot": time_slot,
                    "activity": final_activity,
                    "focus_score": focus_score,
                    "period_type": period_type
                }
                try:
                    res = requests.post(f"{BACKEND_URL}/log", json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ '{final_activity}' 기록이 저장되었습니다!")
                except Exception as e:
                    st.error("백엔드 서버에 연결할 수 없습니다. 서버 상태를 확인해주세요.")

# ==========================================
# --- 탭 2: 고도화 분석 대시보드 (레이아웃 전면 개편) ---
# ==========================================
with tab2:
    col_filter, col_btn = st.columns([4, 1])
    with col_filter:
        filter_type = st.selectbox("🔍 분석 데이터 범위", ["전체", "평시", "시험기간", "방학"])
    with col_btn:
        st.write("")
        st.write("")
        run_analysis = st.button("🔄 리포트 생성", use_container_width=True)
    
    if run_analysis:
        try:
            with st.spinner("AI 엔진이 데이터를 분석하고 있습니다..."):
                analyze_res = requests.post(f"{BACKEND_URL}/analyze", json={"period_type": filter_type})
                logs_res = requests.get(f"{BACKEND_URL}/logs") # 원본 데이터 호출
            
            if analyze_res.status_code == 200 and logs_res.status_code == 200:
                data = analyze_res.json()
                
                if "error" in data:
                    st.warning("데이터가 충분하지 않습니다. 탭1에서 일과를 먼저 기록해주세요.")
                else:
                    # 원본 로그 데이터프레임화 (최근 기록 날짜 추출용)
                    logs_data = logs_res.json()
                    df_logs = pd.DataFrame(logs_data)
                    if filter_type != "전체" and not df_logs.empty:
                        df_logs = df_logs[df_logs["period_type"] == filter_type]
                    
                    latest_date = df_logs['date'].max() if not df_logs.empty else "기록 없음"

                    # [요구사항 6] 데이터 현황 상단 표시
                    st.caption(f"📊 현재 저장된 데이터: **{data['total_logs']}건** | 📅 최근 기록 날짜: **{latest_date}**")
                    st.divider()

                    # ========================================
                    # [요구사항 3] 핵심 분석 결과 (Metric 활용)
                    # ========================================
                    st.markdown("### 📊 핵심 분석 결과")
                    with st.container(border=True):
                        m1, m2, m3 = st.columns(3)
                        m1.metric("🔥 최적 집중 요일", data.get("golden_weekday", "-"))
                        m2.metric("🎯 피크 몰입 시간대", data.get("golden_time", "-"))
                        m3.metric("📂 누적 데이터 수", f"{data['total_logs']} 건")
                    
                    st.divider()

                    # ========================================
                    # 데이터 시각화 분석
                    # ========================================
                    st.markdown("### 📈 데이터 분석 그래프")
                    g1, g2 = st.columns(2)
                    with g1:
                        st.markdown("**⏰ 시간대별 평균 집중도**")
                        chart_df = pd.DataFrame(data["chart_data"])
                        st.bar_chart(chart_df.set_index("time_slot"), color="#29b6f6")
                        
                    with g2:
                        st.markdown("**📅 요일별 평균 집중도**")
                        wk_chart_df = pd.DataFrame(data["weekday_chart_data"])
                        st.bar_chart(wk_chart_df.set_index("weekday"), color="#ab47bc")

                    st.divider()

                    # ========================================
                    # [요구사항 3, 5] 추천 결과 (이상 패턴 + 카드 형태 재배치 제안)
                    # ========================================
                    st.markdown("### 🎯 맞춤형 추천 결과")
                    
                    # 1. 이상 패턴 감지
                    st.markdown("##### 🚨 이상 패턴 감지")
                    status = data["anomaly_status"]
                    if status == "warning":
                        st.warning(data["anomaly_msg"])
                    elif status == "success":
                        st.success(data["anomaly_msg"])
                    else:
                        st.info(data["anomaly_msg"])
                    
                    st.write("")
                    
                    # 2. 활동별 일정 재배치 추천 (카드형 레이아웃 적용)
                    st.markdown("##### 🔄 활동별 일정 재배치 가이드")
                    recs = data["reschedule_recommendations"]
                    if not recs:
                        st.info("충분한 데이터가 모이면 활동별 일정을 추천해 드립니다.")
                    else:
                        # 2열로 깔끔하게 배치
                        rec_cols = st.columns(2)
                        for i, rec in enumerate(recs):
                            with rec_cols[i % 2]:
                                # 백엔드 텍스트를 컨테이너 안에 깔끔하게 담음
                                with st.container(border=True):
                                    st.write(rec)

                    st.divider()

                    # ========================================
                    # [요구사항 4] 종합 리포트 UI 개선 (카드 느낌)
                    # ========================================
                    st.markdown("### 📋 이번 분석 요약 (Report)")
                    with st.container(border=True):
                        col_r1, col_r2 = st.columns([1, 1])
                        
                        with col_r1:
                            st.markdown("#### 🔍 주요 데이터 진단")
                            for bullet in data["report"]["bullets"]:
                                st.write(f"- {bullet}")
                                
                        with col_r2:
                            st.markdown("#### 🎯 최종 행동 조언")
                            st.info(data["report"]["summary"])

                    st.divider()

                    # ========================================
                    # 원본 로그 (테이블 숨김/펼침 기능으로 깔끔하게 처리)
                    # ========================================
                    st.markdown("### 📜 원본 기록 로그")
                    with st.expander("원본 데이터 테이블 보기"):
                        if not df_logs.empty:
                            st.dataframe(df_logs, use_container_width=True, hide_index=True)
                        else:
                            st.write("해당 데이터가 없습니다.")

        except Exception as e:
            st.error(f"데이터 처리 중 오류가 발생했습니다: {str(e)}")

# ==========================================
# 사이드바 (설정 및 데이터 초기화)
# ==========================================
with st.sidebar:
    st.header("⚙️ 서비스 설정")
    st.markdown("앱에 저장된 모든 기록을 삭제합니다.")
    if st.button("🗑️ 모든 데이터 초기화", type="primary", use_container_width=True):
        try:
            res = requests.post(f"{BACKEND_URL}/reset")
            if res.status_code == 200:
                st.success("데이터가 성공적으로 초기화되었습니다.")
                st.rerun()
        except Exception:
            st.error("초기화에 실패했습니다.")