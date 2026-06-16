import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="FocusFlow Pro", page_icon="⏱️", layout="wide")

BACKEND_URL = "http://backend:8000"

# [핵심] 리포트 고정을 위한 세션 기억장치
if 'show_report' not in st.session_state:
    st.session_state.show_report = False

st.title("⏱️ FocusFlow: 고도화된 몰입 분석 및 루틴 최적화 엔진")
st.markdown("입력된 행동 로그를 정밀 교차 분석하여 개인 맞춤형 타임라인 최적화 솔루션을 제공합니다.")

try:
    logs_res = requests.get(f"{BACKEND_URL}/logs")
    raw_logs = logs_res.json() if logs_res.status_code == 200 else []
except:
    raw_logs = []

df_all = pd.DataFrame(raw_logs)

tab1, tab2 = st.tabs(["📝 일과 기록하기", "📊 고도화 분석 대시보드"])

# ==========================================
# --- 탭 1: 기록 입력 폼 ---
# ==========================================
with tab1:
    st.subheader("📝 새로운 일과 데이터 입력")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            log_date = st.date_input("날짜(Date)", date.today())
            granular_time_slots = [f"{i:02d}:00-{i+1:02d}:00" for i in range(24)]
            time_slot = st.selectbox("⏰ 시간대 지정", granular_time_slots, index=9)
            period_type = st.radio("기간 유형", ["평시", "시험기간", "방학"], horizontal=True)
            
        with col2:
            recent_activities = []
            if not df_all.empty:
                recent_activities = df_all['activity'].value_counts().index.tolist()[:4]
            
            clicked_activity = None 
            if recent_activities:
                st.markdown("**💡 최근 자주 기록한 활동 클릭 시 자동 입력:**")
                p_cols = st.columns(len(recent_activities))
                for idx, act in enumerate(recent_activities):
                    if p_cols[idx].button(f"➕ {act}", key=f"pill_{idx}", use_container_width=True):
                        clicked_activity = act
            
            base_options = ["공부", "과제", "독서", "운동", "프로그래밍", "데이터베이스", "회의", "휴식", "기타"]
            default_idx = base_options.index(clicked_activity) if clicked_activity in base_options else (base_options.index("기타") if clicked_activity else 0)
            selected_activity = st.selectbox("🎯 활동 종류 선택", base_options, index=default_idx)
            
            custom_activity_val = clicked_activity if clicked_activity and (clicked_activity not in base_options) else ""
            if selected_activity == "기타" or custom_activity_val != "":
                final_activity = st.text_input("📝 활동명 직접 입력", value=custom_activity_val, placeholder="예: 알고리즘 문제풀이")
            else:
                final_activity = selected_activity
                
            focus_score = st.slider("🧠 집중도 레벨 (1: 매우 산만함 ~ 5: 완전 몰입)", 1, 5, 3)
            
        st.write("")
        submit = st.button("🚀 실시간 기록 저장하기", type="primary", use_container_width=True)

        if submit:
            if not final_activity.strip():
                st.error("🚨 활동명이 비어 있습니다. 입력해주세요.")
            else:
                payload = {
                    "date": str(log_date),
                    "time_slot": time_slot,
                    "activity": final_activity.strip(),
                    "focus_score": focus_score,
                    "period_type": period_type
                }
                try:
                    res = requests.post(f"{BACKEND_URL}/log", json=payload)
                    if res.status_code == 200:
                        st.success(f"🎯 '{final_activity}' 기록이 저장되었습니다!")
                        st.session_state.show_report = False # 새 데이터 입력 시 리포트 갱신 유도
                        st.rerun()
                except Exception as e:
                    st.error("백엔드 분석 서버와의 통신에 실패했습니다.")

# ==========================================
# --- 탭 2: 종합 분석 대시보드 ---
# ==========================================
with tab2:
    if df_all.empty:
        st.write("")
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #555;'>📋 아직 저장된 몰입 데이터가 없습니다.</h3>", unsafe_allow_html=True)
            st.info("💡 **시작 가이드:** 상단의 **'📝 일과 기록하기'** 탭에서 데이터를 먼저 기록해주세요.")
    else:
        col_filter, col_btn = st.columns([3, 1])
        with col_filter:
            filter_type = st.selectbox("🔍 분석 데이터 범위 필터 선택", ["전체", "평시", "시험기간", "방학"])
            
            # 필터를 변경하면 리포트를 접고 다시 누르도록 유도
            if 'prev_filter' not in st.session_state:
                st.session_state.prev_filter = filter_type
            if st.session_state.prev_filter != filter_type:
                st.session_state.show_report = False
                st.session_state.prev_filter = filter_type

        with col_btn:
            st.write(""); st.write("") 
            # 버튼 클릭 시 상태를 True로 확정!
            if st.button("🔄 분석 및 리포트 생성", type="primary", use_container_width=True):
                st.session_state.show_report = True

        # 상태가 True일 때만 리포트 출력 영역 가동
        if st.session_state.show_report:
            with st.spinner("AI 엔진이 데이터를 실시간 분석 중입니다..."):
                try:
                    analyze_res = requests.post(f"{BACKEND_URL}/analyze", json={"period_type": filter_type})
                    
                    # 상태 코드가 200(정상)일 때만 화면 렌더링
                    if analyze_res.status_code == 200:
                        data = analyze_res.json()
                        if "error" in data:
                            st.warning(data["error"])
                        else:
                            df_filtered = df_all if filter_type == "전체" else df_all[df_all["period_type"] == filter_type]
                            latest_date = df_filtered["date"].max() if not df_filtered.empty else "-"
                            
                            st.caption(f"📌 필터: **{filter_type}** | 데이터: **{data['total_logs']}건** | 최근: **{latest_date}**")
                            
                            # 1. 핵심 분석
                            st.markdown("### 📊 핵심 분석 결과")
                            with st.container(border=True):
                                m1, m2, m3, m4 = st.columns(4)
                                m1.metric("🔥 최적 집중 요일", data["golden_weekday"])
                                m2.metric("🎯 피크 몰입 시간", data["golden_time"])
                                avg_f = df_filtered["focus_score"].mean() if not df_filtered.empty else 0
                                m3.metric("🧠 평균 집중도", f"{avg_f:.2f} / 5.0")
                                m4.metric("📂 데이터 총량", f"{data['total_logs']} 건")
                                
                                st.markdown("---")
                                if data['total_logs'] < 10:
                                    st.warning("⚠️ **분석 신뢰도: 낮음** - 데이터가 10건 미만입니다.")
                                else:
                                    st.success("✅ **분석 신뢰도: 높음** - 충분한 데이터가 누적되었습니다.")

                            # 2. 시각화
                            st.markdown("### 📈 데이터 심층 분석 그래프")
                            g1, g2 = st.columns(2)
                            with g1:
                                st.markdown("**⏰ 시간대별 평균 집중도**")
                                st.bar_chart(pd.DataFrame(data["chart_data"]).set_index("time_slot"), color="#29b6f6")
                            with g2:
                                st.markdown("**📅 요일별 평균 집중도**")
                                st.bar_chart(pd.DataFrame(data["weekday_chart_data"]).set_index("weekday"), color="#ab47bc")

                            g3, g4 = st.columns(2)
                            with g3:
                                st.markdown("**📈 최근 집중도 흐름 (최신 15개)**")
                                if data.get("trend_data"):
                                    st.line_chart(pd.DataFrame(data["trend_data"]).set_index("date")["focus_score"], color="#ff9800")
                            with g4:
                                st.markdown("**🏆 활동별 집중도 순위**")
                                if data.get("activity_ranking"):
                                    df_rank = pd.DataFrame(data["activity_ranking"])
                                    df_rank["활동명"] = ["🥇", "🥈", "🥉"][:len(df_rank)] + ["🔹"] * max(0, len(df_rank)-3)
                                    df_rank["활동명"] = df_rank["활동명"] + " " + df_rank["activity"]
                                    st.bar_chart(df_rank.set_index("활동명")["focus_score"], color="#4caf50")

                            # 3. 추천
                            st.markdown("### 🎯 행동 추천 가이드")
                            status = data["anomaly_status"]
                            if status == "warning": st.warning(data["anomaly_msg"])
                            elif status == "success": st.success(data["anomaly_msg"])
                            else: st.info(data["anomaly_msg"])
                            
                            recs = data["reschedule_recommendations"]
                            if recs:
                                rec_cols = st.columns(2)
                                for idx, rec_text in enumerate(recs):
                                    with rec_cols[idx % 2].container(border=True):
                                        st.write(rec_text)
                            
                            # 4. 리포트
                            st.markdown("### 📋 FocusFlow AI 자동 보고서")
                            with st.container(border=True):
                                col_r1, col_r2 = st.columns(2)
                                with col_r1:
                                    for b in data["report"]["bullets"]:
                                        st.write(f"- {b}")
                                with col_r2:
                                    st.info(data["report"]["summary"])

                            # 5. 원본 로그 및 삭제
                            st.markdown("### 📜 원본 데이터 조회 및 수정")
                            if not df_filtered.empty:
                                with st.expander("🔍 원본 테이블 열기", expanded=True):
                                    for idx in reversed(range(len(df_filtered))):
                                        row = df_filtered.iloc[idx]
                                        r_cols = st.columns([2, 2, 2, 1, 1, 1])
                                        r_cols[0].write(row['date'])
                                        r_cols[1].write(row['time_slot'])
                                        r_cols[2].write(row['activity'])
                                        r_cols[3].write(f"⭐ {row['focus_score']}")
                                        r_cols[4].write(row['period_type'])
                                        if r_cols[5].button("❌", key=f"del_{idx}"):
                                            requests.delete(f"{BACKEND_URL}/log/{idx}")
                                            st.rerun()

                    # 백엔드가 정상이 아닐 경우 에러 뿜어내기 (침묵 금지!)
                    else:
                        st.error(f"🚨 백엔드 서버에서 분석 중 충돌이 발생했습니다. (상태 코드: {analyze_res.status_code})")
                        st.code(analyze_res.text)
                
                except Exception as e:
                    st.error(f"🚨 FastAPI 서버와 연결할 수 없습니다. 에러 내용: {str(e)}")

# ==========================================
# 사이드바
# ==========================================
with st.sidebar:
    st.header("⚙️ 시스템 설정")
    if st.button("🗑️ 전체 데이터 초기화", type="primary", use_container_width=True):
        requests.post(f"{BACKEND_URL}/reset")
        st.session_state.show_report = False
        st.rerun()