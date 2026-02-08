import streamlit as st
from openai import OpenAI

# 1. API 클라이언트 설정
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

st.title("⚖️ AI 의사결정 도우미")
st.subheader("여러분의 고민을 객관적으로 분석해 드립니다.")

# 2. 사용자 입력 섹션
with st.sidebar:
    st.header("설정")
    analysis_mode = st.selectbox("분석 모드", ["가중치 채점 방식", "SWOT 분석", "장단점 비교"])

topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 다음 학기 휴학 여부")
options = st.text_area("비교할 선택지들을 적어주세요 (쉼표로 구분)", placeholder="예: 휴학 후 인턴, 바로 복학, 어학 연수")

# 3. AI 분석 실행
if st.button("AI 분석 시작"):
    if topic and options:
        with st.spinner("AI가 객관적인 지표를 바탕으로 분석 중입니다..."):
            # 프롬프트 설계가 핵심입니다.
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
            st.markdown(response.choices[0].message.content)
    else:
        st.warning("주제와 선택지를 모두 입력해주세요.")