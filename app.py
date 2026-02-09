import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("심층적인 가치관 설정을 통해 최적의 결정을 제안합니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 

# 1. 사이드바 설정 (API 키)
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    
    st.markdown("---")
    st.info("💡 **Tip**: 가치관 설정 버튼을 눌러 본인만의 분석 기준을 세밀하게 조정해보세요.")

# 2. 가치관 상세 설정 (팝업창 업그레이드)
with st.popover("🎯 의사결정 가치관 상세 설정 (심층 분석용)", use_container_width=True):
    st.markdown("### 📊 가치 항목별 가중치 설정")
    st.write("이번 결정에서 각 요소가 얼마나 중요한지 0~100 사이로 설정해주세요.")
    
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        v_economy = st.slider("💰 경제적 효율성 (가성비, 비용)", 0, 100, 50)
        v_time = st.slider("⏰ 시간적 효율성 (소요 시간, 이동 거리)", 0, 100, 50)
    with col_v2:
        v_experience = st.slider("✨ 개인적 즐거움 (문화 경험, 휴식의 질)", 0, 100, 50)
        v_future = st.slider("📈 미래 커리어/성장 (자기계발, 포트폴리오)", 0, 100, 30)

    st.markdown("---")
    st.markdown("### 🛡️ 의사결정 성향")
    risk_tolerance = st.select_slider(
        "안정성 vs 도전성",
        options=["매우 보수적", "신중함", "균형 잡힌", "도전적", "매우 실험적"],
        value="균형 잡힌"
    )
    
    # 설정값 요약 (AI 전달용)
    user_context = f"""
    - 가중치: 경제성({v_economy}), 시간({v_time}), 경험({v_experience}), 미래성({v_future})
    - 성향: {risk_tolerance} (실패 가능성 대비 보상 선호도)
    """

# 3. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 방학 기간 유럽 배낭여행 vs IT 자격증 취득")

st.markdown("### 📋 비교 선택지 입력")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            name = st.text_input("이름", key=f"opt_name_{i}", placeholder="예: 스페인 여행")
        with c2:
            detail = st.text_input("기본 설명", key=f"opt_det_{i}", placeholder="예: 2주 일정, 예상 경비 400만원")
        
        c3, c4 = st.columns(2)
        with c3:
            pros = st.text_area("장점 (Pros)", key=f"opt_pros_{i}", placeholder="새로운 문화 체험, 어학 자신감 상승", height=80)
        with c4:
            cons = st.text_area("단점 (Cons)", key=f"opt_cons_{i}", placeholder="높은 비용 부담, 학기 중 복습 시간 부족", height=80)
        
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. AI 분석 실행
if st.button("🚀 심층 분석 시작"):
    valid_options = [f"[{o['name']}]\n- 상세: {o['detail']}\n- 장점: {o['pros']}\n- 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지 정보를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("사용자의 가치관 점수를 반영하여 최적의 경로를 시뮬레이션 중입니다..."):
                options_str = "\n\n".join(valid_options)
                
                prompt = f"""
                [분석 주제]: {topic}
                
                [사용자 의사결정 설정]:
                {user_context}
                
                [비교 선택지]:
                {options_str}
                
                위 데이터를 바탕으로 다음 지침에 따라 심층 분석을 수행해줘:
                1. 사용자가 설정한 4가지 가치 가중치(경제, 시간, 경험, 미래)를 기준으로 각 선택지를 정밀하게 점수화해서 비교해줘.
                2. '안정성 vs 도전성' 성향을 반영하여, 사용자의 성향에 가장 부합하는 선택지가 무엇인지 논리적으로 설명해줘.
                3. 단순 나열이 아닌, "경제성을 80만큼 중시하는 사용자에게 A는 비용 면에서 최적이지만, 경험 점수가 낮아 만족도가 떨어질 수 있다"는 식의 입체적 분석을 수행해줘.
                4. 대학생의 현실적인 제약조건을 고려한 최종 순위와 각 선택지별 한 줄 평을 작성해줘.
                5. 결과는 깔끔한 Markdown 표와 시각적인 리스트를 활용해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 심층 분석이 완료되었습니다!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
