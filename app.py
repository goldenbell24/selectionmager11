import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 의사결정 도우미", page_icon="⚖️")

st.title("⚖️ AI 의사결정 도우미")
st.subheader("여러분의 고민을 객관적으로 분석해 드립니다.")

# 1. 사이드바 설정 (API 키 입력 포함)
with st.sidebar:
    st.header("⚙️ 설정")
    
    # API 키 입력창 (type="password"로 설정하여 보안 강화)
    api_key_input = st.text_input(
        "OpenAI API Key를 입력하세요", 
        type="password", 
        placeholder="sk-..."
    )
    
    st.markdown("---")
    analysis_mode = st.selectbox("분석 모드", ["가중치 채점 방식", "SWOT 분석", "장단점 비교"])
    
    st.info("API 키는 서버에 저장되지 않고 브라우저 세션 동안만 사용됩니다.")

# 2. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 다음 학기 휴학 여부")
options = st.text_area("비교할 선택지들을 적어주세요 (쉼표로 구분)", placeholder="예: 휴학 후 인턴, 바로 복학, 어학 연수")

# 3. AI 분석 실행
if st.button("AI 분석 시작"):
    # API 키 확인 로직
    if not api_key_input:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or not options:
        st.warning("주제와 선택지를 모두 입력해주세요.")
    else:
        try:
            # 클라이언트 초기화
            client = OpenAI(api_key=api_key_input)
            
            with st.spinner("AI가 객관적인 지표를 바탕으로 분석 중입니다..."):
                prompt = f"""
                주제: {topic}
                선택지: {options}
                모드: {analysis_mode}
                
                위 사항에 대해 사용자가 객관적인 결정을 내릴 수 있도록 분석해줘.
                각 선택지별로 점수를 매기고, 마지막에 가장 추천하는 선택지를 이유와 함께 제시해줘.
                결과는 Markdown 형식을 사용하여 가독성 있게 출력해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                # 결과 출력
                st.markdown("---")
                st.success("✅ 분석이 완료되었습니다!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
