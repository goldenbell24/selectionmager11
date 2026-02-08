import streamlit as st
from openai import OpenAI
from notion_client import Client # pip install notion-client 필요

# 페이지 설정
st.set_page_config(page_title="AI 의사결정 도우미 PRO", page_icon="⚖️")

st.title("⚖️ AI 의사결정 도우미 (Notion 연동)")

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password")
    
    st.markdown("---")
    st.header("📓 Notion 연동 (선택)")
    notion_token = st.text_input("Notion API Token", type="password", help="노션 통합(Integration) 토큰을 입력하세요.")
    notion_db_id = st.text_input("Database ID", placeholder="데이터베이스 ID를 입력하세요.")
    
    st.markdown("---")
    analysis_mode = st.selectbox("분석 모드", ["가중치 채점 방식", "SWOT 분석", "장단점 비교"])

# 2. 노션 데이터 가져오기 함수
def get_notion_context(token, db_id):
    try:
        notion = Client(auth=token)
        results = notion.databases.query(database_id=db_id).get("results")
        
        context_text = ""
        for page in results:
            # '이름' 또는 '제목' 속성을 추출 (설정에 따라 'Name' 등으로 변경 필요)
            properties = page.get("properties", {})
            title_list = properties.get("이름", {}).get("title", []) or properties.get("Name", {}).get("title", [])
            if title_list:
                title = title_list[0].get("plain_text")
                context_text += f"- 과거 사례/디테일: {title}\n"
        return context_text
    except Exception as e:
        st.error(f"노션 데이터를 가져오는 데 실패했습니다: {e}")
        return None

# 3. 사용자 입력
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 다음 학기 휴학 여부")
options = st.text_area("비교할 선택지들을 적어주세요", placeholder="쉼표로 구분")

# 4. 실행 버튼
if st.button("AI 분석 시작"):
    if not openai_key:
        st.error("OpenAI API Key가 필요합니다.")
    elif not topic or not options:
        st.warning("주제와 선택지를 입력해주세요.")
    else:
        # 노션 컨텍스트 확보
        additional_context = ""
        if notion_token and notion_db_id:
            with st.spinner("노션에서 결정 이력을 불러오는 중..."):
                additional_context = get_notion_context(notion_token, notion_db_id)
        
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("데이터 기반 분석 중..."):
                # 노션 데이터를 프롬프트에 결합
                full_prompt = f"""
                [사용자 주제]: {topic}
                [선택지]: {options}
                [분석 모드]: {analysis_mode}
                
                [참고할 과거 결정 이력 및 디테일]:
                {additional_context if additional_context else "제공된 노션 데이터 없음"}
                
                위 정보를 바탕으로 사용자의 가치관과 과거 성향을 고려하여 최적의 선택을 분석해줘. 
                결과는 Markdown 형식을 사용해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": full_prompt}]
                )
                
                st.markdown("---")
                st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"오류 발생: {e}")
