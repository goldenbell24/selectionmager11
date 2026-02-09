import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("여러분의 가치관을 반영한 상대적 비교를 시작합니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    notion_key = st.text_input("Notion API Key (Optional)", type="password", placeholder="secret_...")
    
    st.markdown("---")
    
    st.header("🎯 의사결정 기준")
    user_values = st.text_area(
        "중요하게 고려할 가치 (쉼표로 구분)", 
        value="예산 효율성, 이동 편의성, 문화적 경험, 휴식의 질",
        help="본인이 결정에서 가장 중요하게 생각하는 키워드들을 적어주세요."
    )

# 2. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 해외 여행지 결정")

st.markdown("### 📋 비교 선택지 입력")

# 동적 입력 칸 생성
option_data = []
for i in range(st.session_state.options_count):
    # 각 선택지 구분을 위한 컨테이너와 구분선
    with st.container():
        st.markdown(f"#### 선택지 {i+1}")
        
        # 첫 번째 줄: 이름과 기본 세부사항
        col1, col2 = st.columns([1, 2])
        with col1:
            name = st.text_input(f"이름", key=f"opt_name_{i}", placeholder="예: 일본 오사카")
        with col2:
            detail = st.text_input(f"기본 설명", key=f"opt_det_{i}", placeholder="예: 3박 4일, 예산 100만원")
        
        # 두 번째 줄: 장점과 단점 (추가된 칸)
        col3, col4 = st.columns(2)
        with col3:
            pros = st.text_input(f"장점 (Pros)", key=f"opt_pros_{i}", placeholder="예: 가까운 거리, 다양한 먹거리")
        with col4:
            cons = st.text_input(f"단점 (Cons)", key=f"opt_cons_{i}", placeholder="예: 여름철 높은 습도와 인파")
        
        st.markdown("---") # 시각적 구분선
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

# 선택지 추가 버튼
if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 3. AI 분석 실행
if st.button("🚀 AI 상대 비교 분석 시작"):
    # 유효한 데이터만 정리
    valid_options = []
    for o in option_data:
        if o['name'].strip():
            info = f"- {o['name']}: {o['detail']} (장점: {o['pros']} / 단점: {o['cons']})"
            valid_options.append(info)
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지 이름을 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            
            with st.spinner("입력하신 장단점을 포함하여 분석 중입니다..."):
                options_str = "\n".join(valid_options)
                
                prompt = f"""
                [분석 주제]: {topic}
                [비교 선택지 리스트]:
                {options_str}
                
                [사용자 우선 가치]: {user_values}
                
                위 내용을 바탕으로 다음 지침에 따라 분석해줘:
                1. 각 선택지의 '장점'과 '단점'을 사용자가 제시한 '우선 가치'와 연결하여 상대적으로 비교해줘.
                2. 단순히 정보를 나열하지 말고, "A의 장점인 ~는 가치관 ~에 부합하지만, B에 비해 ~한 단점이 치명적일 수 있다"는 식으로 교차 분석해줘.
                3. 대학생의 관점에서 현실적인 기회비용을 언급해줘.
                4. 최종적으로 가치관에 따른 최적의 시나리오 순위를 제안해줘.
                5. 결과는 Markdown 표와 리스트를 활용해 가독성 있게 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
