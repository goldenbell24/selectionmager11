import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("여러분의 가치관을 반영한 상대적 비교를 시작합니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 
if 'user_values' not in st.session_state:
    st.session_state.user_values = "예산 효율성, 이동 편의성, 문화적 경험, 휴식의 질"

# 1. 사이드바 설정 (API 키 전용)
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    notion_key = st.text_input("Notion API Key (Optional)", type="password", placeholder="secret_...")
    st.info("API 키는 본인의 브라우저 세션에만 안전하게 사용됩니다.")

# 2. 가치관 설정 섹션 (버튼 및 팝업)
# 제목 아래에 가치관을 설정할 수 있는 팝업 버튼 추가
with st.popover("🎯 의사결정 가치관 상세 설정"):
    st.markdown("### 나의 우선순위 가이드")
    st.write("분석 시 가장 중요하게 고려할 키워드들을 수정하세요.")
    
    # 세션 상태를 활용하여 팝업 내에서 값 변경
    updated_values = st.text_area(
        "중요하게 고려할 가치 (쉼표로 구분)", 
        value=st.session_state.user_values,
        help="예: 가성비, 로컬 맛집, 액티비티, 인스타 감성 등"
    )
    st.session_state.user_values = updated_values
    
    st.caption(f"현재 설정된 기준: {st.session_state.user_values}")

# 3. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 해외 여행지 결정")

st.markdown("### 📋 비교 선택지 입력")

# 동적 입력 칸 생성
option_data = []
for i in range(st.session_state.options_count):
    with st.container():
        st.markdown(f"#### 선택지 {i+1}")
        
        # 첫 번째 줄: 이름과 기본 세부사항
        col1, col2 = st.columns([1, 2])
        with col1:
            name = st.text_input(f"이름", key=f"opt_name_{i}", placeholder="예: 일본 오사카")
        with col2:
            detail = st.text_input(f"기본 설명", key=f"opt_det_{i}", placeholder="예: 3박 4일, 예산 100만원")
        
        # 두 번째 줄: 장점과 단점
        col3, col4 = st.columns(2)
        with col3:
            pros = st.text_input(f"장점 (Pros)", key=f"opt_pros_{i}", placeholder="예: 가까운 거리, 다양한 먹거리")
        with col4:
            cons = st.text_input(f"단점 (Cons)", key=f"opt_cons_{i}", placeholder="예: 여름철 높은 습도와 인파")
        
        st.markdown("---")
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

# 선택지 추가 버튼
if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. AI 분석 실행
if st.button("🚀 AI 상대 비교 분석 시작"):
    valid_options = []
    for o in option_data:
        if o['name'].strip():
            info = f"- {o['name']}: {o['detail']} (장점: {o['pros']} / 단점: {o['cons']})"
            valid_options.append(info)
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지 정보를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            
            with st.spinner("가치관을 바탕으로 최적의 선택을 분석 중입니다..."):
                options_str = "\n".join(valid_options)
                
                prompt = f"""
                [분석 주제]: {topic}
                [비교 선택지 리스트]:
                {options_str}
                
                [사용자 우선 가치]: {st.session_state.user_values}
                
                위 내용을 바탕으로 다음 지침에 따라 분석해줘:
                1. 각 선택지를 사용자가 설정한 '{st.session_state.user_values}' 관점에서 상대적으로 비교해줘.
                2. 장점과 단점이 가치관에 미치는 영향을 심도 있게 분석해줘.
                3. 대학생 사용자에게 가장 합리적인 제안이 무엇인지 우선순위를 매겨줘.
                4. 결과는 Markdown 표와 리스트를 활용해 가독성 있게 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
