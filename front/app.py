import streamlit as st
import requests
import pandas as pd
from datetime import date

# 페이지 기본 설정 (와이드 레이아웃)
st.set_page_config(page_title="FocusFlow Pro", page_icon="⏱️", layout="wide")

BACKEND_URL = "http://backend:8000"

st.title("⏱️ FocusFlow: 고도화된 몰입 분석 및 루틴 최적화 엔진")
st.markdown("입력된 행동 로그를 정밀 교차 분석하여 개인 맞춤형 타임라인 최적화 솔루션을 제공합니다.")

# 데이터 불러오기 공통 처리
try:
    logs_res = requests.get(f"{BACKEND_URL}/logs")
    raw_logs = logs_res.json() if logs_res.status_code == 200 else []
except:
    raw_logs = []

df_all = pd.DataFrame(raw_logs)

tab1, tab2 = st.tabs(["📝 일과 기록하기", "📊 고도화 분석 대시보드"])

# ==========================================
# --- 탭 1: 기록 입력 폼 (UX 대대적 고도화) ---
# ==========================================
with tab1:
    st.subheader("📝 새로운 일과 데이터 입력")
    
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            log_date = st.date_input("날짜(Date)", date.today())
            granular_time_slots = [f"{i:02d}:00-{i+1:02d}:00" for i in range(24)]
            time_slot = st.selectbox("⏰ 시간대 지정", granular_time_slots, index=9) # 기본 09:00 타깃
            period_type = st.radio("기간 유형", ["평시", "시험기간", "방학"], horizontal=True)
            
        with col2:
            # [요구사항 1] 자주 쓰는 최근 활동 추출 및 단축 칩(Pill) UI 제공
            recent_activities = []
            if not df_all.empty:
                recent_activities = df_all['activity'].value_counts().index.tolist()[:4]
            
            clicked_activity = None
            
            if recent_activities:
                st.markdown("**💡 최근 자주 기록한 활동 클릭 시 자동 입력:**")
                # 헬퍼 버튼 정렬
                p_cols = st.columns(len(recent_activities))
                for idx, act in enumerate(recent_activities):
                    if p_cols[idx].button(f"➕ {act}", key=f"pill_{idx}", use_container_width=True):
                        clicked_activity = act
            
            # 기본 정형 데이터 제공 및 선택 UI
            base_options = ["공부", "과제", "독서", "운동", "프로그래밍", "회의", "휴식", "언어", "기타"]
            
            # 최근 칩을 클릭했다면 셀렉트박스 자동 동기화용 기본 인덱스 처리
            default_idx = 0
            if clicked_activity in base_options:
                default_idx = base_options.index(clicked_activity)
            elif clicked_activity:
                default_idx = base_options.index("기타")

            selected_activity = st.selectbox("🎯 활동 종류 선택", base_options, index=default_idx)
            
            # '기타' 선택 시 혹은 칩 클릭 데이터가 기본 옵션에 없는 커스텀 데이터일 때
            custom_activity_val = ""
            if clicked_activity and (clicked_activity not in base_options):
                custom_activity_val = clicked_activity
                
            if selected_activity == "기타" or custom_activity_val != "":
                custom_activity = st.text_input("📝 활동명 직접 입력", value=custom_activity_val, placeholder="예: 알고리즘 문제풀이")
                final_activity = custom_activity
            else:
                final_activity = selected_activity
                
            focus_score = st.slider("🧠 집중도 레벨 (1: 매우 산만함 ~ 5: 완전 몰입)", 1, 5, 3)
            
        st.write("")
        submit = st.button("🚀 실시간 기록 저장하기", type="primary", use_container_width=True)

        # [요구사항 2] 입력값 검증 로직 구현
        if submit:
            if not final_activity.strip():
                st.error("🚨 활동명이 비어 있습니다. 활동을 선택하거나 직접 입력해주세요.")
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
                        st.success(f"🎯 '{final_activity}' 일과 로그가 데이터셋에 안전하게 동기화되었습니다!")
                        st.rerun()
                except Exception as e:
                    st.error("백엔드 분석 서버와의 통신에 실패했습니다.")

# ==========================================
# --- 탭 2: 종합 분석 대시보드 (UX 전면 개편) ---
# ==========================================
with tab2:
    # [요구사항 6] 데이터가 없을 때 우아한 Empty State 레이아웃 처리
    if df_all.empty:
        st.write("")
        with st.container(border=True):
            st.markdown("<h3 style='text-align: center; color: #555;'>📋 아직 저장된 몰입 데이터가 없습니다.</h3>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-size: 16px; color: #777;'>오늘의 활동과 집중도를 기록하시면 다차원 시간대 분석 및 맞춤형 대시보드 피드백을 실시간으로 받아보실 수 있습니다.</p>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; font-weight: bold; color: #29b6f6;'>👇 아래 가이드를 따라 첫 발걸음을 떼어보세요!</p>", unsafe_allow_html=True)
            st.info("💡 **시작 가이드:** 상단의 **'📝 일과 기록하기'** 탭으로 이동하신 뒤 활동 종류, 시간대, 집중 점수를 설정하고 저장 버튼을 누르면 즉시 분석 엔진이 가동됩니다.")
    else:
        # 상단 제어 필터 바
        filter_type = st.selectbox("🔍 분석 데이터 범위 필터 선택", ["전체", "평시", "시험기간", "방학"])
        
        try:
            analyze_res = requests.post(f"{BACKEND_URL}/analyze", json={"period_type": filter_type})
            if analyze_res.status_code == 200:
                data = analyze_res.json()
                
                if "error" in data:
                    st.warning(data["error"])
                else:
                    # 데이터 현황 메타 계산
                    df_filtered = df_all if filter_type == "전체" else df_all[df_all["period_type"] == filter_type]
                    latest_date = df_filtered["date"].max() if not df_filtered.empty else "-"
                    
                    # 데이터 현황 표시 상단 노출
                    st.caption(f"📌 데이터 필터링 기준: **{filter_type}** | 누적 데이터: **{data['total_logs']}건** | 최종 기록일: **{latest_date}**")
                    
                    # ========================================
                    # 📊 [섹션 1] 핵심 분석 결과 및 신뢰도 지표
                    # ========================================
                    st.markdown("### 📊 핵심 분석 결과")
                    with st.container(border=True):
                        m1, m2, m3, m4 = st.columns(4)
                        m1.metric("🔥 최적 집중 요일", data["golden_weekday"])
                        m2.metric("🎯 피크 몰입 시간", data["golden_time"])
                        
                        avg_f = df_filtered["focus_score"].mean() if not df_filtered.empty else 0
                        m3.metric("🧠 평균 집중도", f"{avg_f:.2f} / 5.0")
                        m4.metric("📂 누적 데이터 총량", f"{data['total_logs']} 건")
                        
                        # [요구사항 4] 데이터 샘플 수 기준 분석 신뢰도 판정 UI
                        total_cnt = data["total_logs"]
                        st.markdown("---")
                        if total_cnt < 10:
                            st.warning(f"⚠️ **분석 신뢰도: 낮음 ({total_cnt}/10건)** - 현재 데이터 수가 부족하여 통계적 신뢰도가 다소 낮습니다. 데이터가 10건 이상 모이면 정밀 신뢰도로 전환됩니다.")
                        elif 10 <= total_cnt < 30:
                            st.info(f"ℹ️ **분석 신뢰도: 보통 ({total_cnt}/30건)** - 데이터 기반 루틴 설계의 유효성이 증명되기 시작했습니다. 기록을 꾸준히 늘려가세요.")
                        else:
                            st.success(f"✅ **분석 신뢰도: 매우 높음 ({total_cnt}건 누적 완료)** - 충분한 데이터가 누적되어 공학적으로 매우 높은 통계 신뢰도를 가진 분석 리포트입니다.")

                    st.write("")
                    
                    # ========================================
                    # 📈 [섹션 2] 데이터 다차원 시각화 그래프 레이아웃
                    # ========================================
                    st.markdown("### 📈 데이터 심층 분석 그래프")
                    
                    # 2x2 격자 배치 구성
                    g_row1_col1, g_row1_col2 = st.columns(2)
                    with g_row1_col1:
                        st.markdown("**⏰ 시간대별 평균 집중도**")
                        chart_df = pd.DataFrame(data["chart_data"])
                        st.bar_chart(chart_df.set_index("time_slot"), color="#29b6f6")
                        
                    with g_row1_col2:
                        st.markdown("**📅 요일별 평균 집중도 추이**")
                        wk_chart_df = pd.DataFrame(data["weekday_chart_data"])
                        st.bar_chart(wk_chart_df.set_index("weekday"), color="#ab47bc")

                    g_row2_col1, g_row2_col2 = st.columns(2)
                    with g_row2_col1:
                        # [요구사항 5] 최근 집중도 변화 추세 선그래프 UI 추가
                        st.markdown("**📈 최근 집중도 흐름 추세선 (최신 15개 기록 기준)**")
                        trend_raw = data.get("trend_data", [])
                        if trend_raw:
                            df_trend = pd.DataFrame(trend_raw)
                            st.line_chart(df_trend.set_index("date")["focus_score"], color="#ff9800")
                        else:
                            st.caption("추세 그래프를 그릴 충분한 시계열 기록이 없습니다.")
                            
                    with g_row2_col2:
                        # [요구사항 3] 활동별 집중도 순위 카드형 막대그래프 구현
                        st.markdown("**🏆 활동별 평균 집중도 명예의 전당**")
                        rank_raw = data.get("activity_ranking", [])
                        if rank_raw:
                            df_rank = pd.DataFrame(rank_raw)
                            
                            # 순위 텍스트 데코레이션 가공 표현
                            medals = ["🥇", "🥈", "🥉"]
                            decorations = []
                            for i, row in df_rank.iterrows():
                                prefix = medals[i] if i < 3 else "🔹"
                                decorations.append(f"{prefix} {row['activity']}")
                            df_rank["활동순위"] = decorations
                            
                            st.bar_chart(df_rank.set_index("활동순위")["focus_score"], color="#4caf50")
                        else:
                            st.caption("활동 순위를 매길 데이터 데이터셋이 비어 있습니다.")

                    st.write("")

                    # ========================================
                    # 🎯 [섹션 3] 몰입 추천 및 스케줄 재배치 의사결정 결과
                    # ========================================
                    st.markdown("### 🎯 데이터 행동 추천 결과")
                    
                    # 이상 패턴 경고 카드
                    st.markdown("##### 🚨 실시간 생체 리듬 및 이상 패턴 진단")
                    status = data["anomaly_status"]
                    if status == "warning":
                        st.warning(data["anomaly_msg"])
                    elif status == "success":
                        st.success(data["anomaly_msg"])
                    else:
                        st.info(data["anomaly_msg"])
                    
                    # [요구사항 5] 활동별 일정 재배치 추천 UI 고도화 (2열 확장형 카드 배치)
                    st.markdown("##### 🔄 활동별 최적화 가이드라인 (Re-allocation)")
                    recs = data["reschedule_recommendations"]
                    if recs:
                        rec_cols = st.columns(2)
                        for idx, rec_text in enumerate(recs):
                            with rec_cols[idx % 2]:
                                with st.container(border=True):
                                    # 이모지에 따라 아이콘과 가독성을 깔끔하게 분류 표현
                                    if "🚨" in rec_text:
                                        st.markdown(f"<div style='border-left: 5px solid red; padding-left: 10px;'>{rec_text}</div>", unsafe_allow_html=True)
                                    elif "⚠️" in rec_text:
                                        st.markdown(f"<div style='border-left: 5px solid orange; padding-left: 10px;'>{rec_text}</div>", unsafe_allow_html=True)
                                    else:
                                        st.markdown(f"<div style='border-left: 5px solid green; padding-left: 10px;'>{rec_text}</div>", unsafe_allow_html=True)
                    else:
                        st.caption("일정 재배치 가이드 생성을 위한 충분한 원본 활동 데이터가 누적되지 않았습니다.")

                    st.write("")

                    # ========================================
                    # 📋 [섹션 4] 종합 분석 리포트 (요구사항 4번 카드화)
                    # ========================================
                    st.markdown("### 📋 FocusFlow AI 자동 종합 보고서")
                    with st.container(border=True):
                        col_rep1, col_rep2 = st.columns(2)
                        with col_rep1:
                            st.markdown("#### 📋 이번 분석 요약")
                            st.markdown(f"✅ **가장 집중이 잘 되는 시간** : `{data['golden_time']}`")
                            st.markdown(f"✅ **가장 집중이 잘 되는 요일** : `{data['golden_weekday']}`")
                            
                            # 최근 트렌드 언어 진단
                            trend_status = "데이터 분석 중"
                            if trend_raw:
                                last_score = trend_raw[-1]["focus_score"]
                                trend_status = "안정적" if last_score >= 3 else "집중도 저하 관리 필요"
                            st.markdown(f"✅ **최근 집중도 변화 추세** : `{trend_status}`")
                            
                        with col_rep2:
                            st.markdown("#### 🎯 행동 조언 액션 플랜")
                            st.info(data["report"]["summary"])
                            
                        st.markdown("---")
                        st.markdown("**📊 진단 세부 스냅샷:**")
                        for bullet in data["report"]["bullets"]:
                            st.markdown(f"- {bullet}")

                    st.write("")

                    # ========================================
                    # 📜 [섹션 5] 원본 기록 관리 로그 및 행별 삭제 기능 구현
                    # ========================================
                    st.markdown("### 📜 원본 행동 기록 상세 로그 데이터")
                    
                    # [요구사항 2] 행별 ❌ 삭제 매커니즘 구현
                    # 단순 데이터프레임 출력을 넘어 개별 버튼 컨트롤 배치
                    if not df_filtered.empty:
                        with st.expander("🔍 상세 로그 데이터 테이블 편집 및 조회", expanded=True):
                            # 테이블 헤더 컬럼 구조화
                            h_cols = st.columns([1.5, 1.5, 2.5, 1.5, 1.5, 1])
                            h_cols[0].markdown("**날짜**")
                            h_cols[1].markdown("**시간대**")
                            h_cols[2].markdown("**수행 활동**")
                            h_cols[3].markdown("**집중도**")
                            h_cols[4].markdown("**유형**")
                            h_cols[5].markdown("**삭제**")
                            st.markdown("---")
                            
                            # 데이터 역순으로 출력 (최신 입력 내역이 위로 오게 처리)
                            for idx in reversed(range(len(df_filtered))):
                                row = df_filtered.iloc[idx]
                                r_cols = st.columns([1.5, 1.5, 2.5, 1.5, 1.5, 1])
                                
                                r_cols[0].write(row['date'])
                                r_cols[1].write(row['time_slot'])
                                r_cols[2].write(row['activity'])
                                r_cols[3].write(f"⭐ {row['focus_score']}.0")
                                r_cols[4].write(row['period_type'])
                                
                                # 행 개별 고유 삭제 제어 처리
                                if r_cols[5].button("❌", key=f"del_btn_{idx}"):
                                    try:
                                        # 백엔드의 해당 인덱스 삭제 API 트리거 호출
                                        del_res = requests.delete(f"{BACKEND_URL}/log/{idx}")
                                        if del_res.status_code == 200:
                                            st.toast(f"✅ 해당 로그가 안전하게 삭제되었습니다.")
                                            st.rerun()
                                    except:
                                        st.error("삭제 요청 도중 백엔드와 연결이 해제되었습니다.")
                    else:
                        st.caption("해당 분석 범위 내역의 로우 데이터가 부재합니다.")

        except Exception as e:
            st.error(f"통신 에러 발생: 백엔드 상태를 점검하세요. 상세 내용: {str(e)}")

# ==========================================
# 사이드바 (글로벌 제어 및 대형 리셋 보존)
# ==========================================
with st.sidebar:
    st.header("⚙️ 글로벌 시스템 설정")
    st.markdown("앱 데이터셋 초기화 세팅 마스터 허브")
    
    if st.button("🗑️ DB 전체 로그 파괴 초기화", type="primary", use_container_width=True):
        try:
            res = requests.post(f"{BACKEND_URL}/reset")
            if res.status_code == 200:
                st.sidebar.success("💥 전체 리셋 성공! 초기 청정 상태로 복구되었습니다.")
                st.rerun()
        except Exception:
            st.sidebar.error("초기화 실패")