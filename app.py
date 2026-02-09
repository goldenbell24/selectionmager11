import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("여러분의 가치관을 반영한 상대적 비교를 시작합니다.")

# --- 세션 상태 초기화 (동적 입력 칸 관리) ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2  # 기본 2개 칸

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    notion_key = st.text_input("Notion API Key (Optional)", type="password", placeholder="secret_...")
    
    st.markdown("---")
    
    st.header("🎯 의사결정 기준")
    user_values = st.text_area(
        "중요하게 고려할 가치 (쉼표로 구분)", 
        value="경제적 수익성, 시간적 효율성, 미래 커리어 확장성, 개인적 행복도",
        help="본인이 결정에서 가장 중요하게 생각하는 키워드들을 적어주세요."
    )
    st.info("설정된 가치관을 바탕으로 선택지 간의 상대적 우위를 분석합니다.")

# 2. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 대학원 진학 vs 취업")

st.markdown("### 📋 비교 선택지 입력")
st.caption("각 선택지의 이름과 상세 상황(비용, 시간, 기대효과 등)을 입력해주세요.")

# 동적 입력 칸 생성
option_data = []
for i in range(st.session_state.options_count):
    col1, col2 = st.columns([1, 2])
    with col1:
        name = st.text_input(f"선택지 {i+1} 이름", key=f"opt_name_{i}", placeholder="예: 의대 재수")
    with col2:
        detail = st.text_input(f"선택지 {i+1} 세부사항", key=f"opt_det_{i}", placeholder="예: 1년 휴학 필요, 학원비 2천만원...")
    option_data.append({"name": name, "detail": detail})

# 선택지 추가 버튼
if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 3. AI 분석 실행
if st.button("🚀 AI 상대 비교 분석 시작"):
    # 유효성 검사: 이름이 입력된 선택지만 필터링
    valid_options = [f"{o['name']} ({o['detail']})" for o in option_data if o['name'].strip()]
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지 이름을 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            
            with st.spinner("가치 기준에 따라 상대적 장단점을 분석 중입니다..."):
                options_str = "\n".join(valid_options)
                
                prompt = f"""
                [분석 주제]: {topic}
                [비교 선택지 및 세부사항]:
                {options_str}
                
                [사용자 우선 가치]: {user_values}
                
                위 내용을 바탕으로 다음 지침에 따라 분석해줘:
                1. 각 선택지를 사용자가 제시한 '우선 가치' 관점에서 상대적으로 비교해줘. 
                2. 단순히 점수를 매기기보다, "A는 B에 비해 ~한 점이 유리하지만, ~한 기회비용이 발생한다"는 식의 상대적 분석을 수행해줘.
                3. 사용자가 40세까지 20억을 모으고 싶어 하는 등의 장기적 목표를 가지고 있다면 그 관점도 녹여줘.
                4. 최종적으로 가치관에 따른 최적의 시나리오 순위를 제안해줘.
                5. 결과는 Markdown 표와 리스트를 활용해 가독성 있게 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 상대적 비교 분석이 완료되었습니다!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
