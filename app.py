import streamlit as st
from openai import OpenAI
import docx2txt  # pip install docx2txt
import PyPDF2    # pip install PyPDF2
from io import StringIO

# 파일에서 텍스트를 추출하는 함수
def extract_text_from_file(uploaded_file):
    if uploaded_file.type == "text/plain":
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        return stringio.read()
    elif uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(uploaded_file)
    return ""

st.set_page_config(page_title="AI 의사결정 도우미", page_icon="⚖️")

# --- 사이드바: API 설정 및 파일 업로드 ---
with st.sidebar:
    st.header("⚙️ 설정 및 배경 지식")
    
    # 1. API 키 입력 기능
    api_key = st.text_input("OpenAI API Key를 입력하세요", type="password")
    st.caption("키는 서버에 저장되지 않고 현재 세션에서만 사용됩니다.")
    
    st.divider()
    
    # 2. 배경 문서 업로드 기능
    st.subheader("📁 배경 문서 업로드")
    uploaded_files = st.file_uploader(
        "이전 결정이나 관련 문서를 업로드하세요 (PDF, TXT, DOCX)", 
        type=["pdf", "txt", "docx"], 
        accept_multiple_files=True
    )
    
    context_text = ""
    if uploaded_files:
        for file in uploaded_files:
            context_text += f"\n--- 문서명: {file.name} ---\n"
            context_text += extract_text_from_file(file)
        st.success(f"{len(uploaded_files)}개의 문서를 읽어왔습니다.")

# --- 메인 화면 ---
st.title("⚖️ AI 의사결정 도우미")

if not api_key:
    st.info("왼쪽 사이드바에 OpenAI API Key를 입력하여 시작하세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 대학원 진학 vs 취업")
options = st.text_area("비교할 선택지들을 적어주세요 (쉼표로 구분)", placeholder="예: 생명공학 박사 진학, 제약회사 취업")
analysis_mode = st.selectbox("분석 모드", ["가중치 채점 방식", "SWOT 분석", "장단점 비교", "재무적 가치 분석"])

if st.button("AI 분석 시작"):
    if topic and options:
        with st.spinner("배경 지식을 검토하고 분석을 진행 중입니다..."):
            # 프롬프트 구성: 업로드된 문서가 있다면 배경 지식으로 포함
            prompt = f"""
            주제: {topic}
            선택지: {options}
            분석 모드: {analysis_mode}
            
            [배경 정보]
            아래 내용은 사용자가 업로드한 문서에서 추출한 배경 지식이야. 
            이 내용을 참고해서 사용자의 성향, 과거 이력, 상황에 맞는 객관적인 조언을 해줘.
            {context_text if context_text else "제공된 배경 문서 없음"}
            
            [지시사항]
            1. 각 선택지별로 객관적인 점수나 특징을 분석해줘.
            2. 배경 정보를 바탕으로 사용자의 목표(예: 장기적 자산 형성, 커리어 목표 등)에 가장 부합하는 선택지를 추천해줘.
            3. Markdown 형식을 사용하여 시각적으로 깔끔하게 출력해줘.
            """
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": "너는 사용자의 과거 기록과 현재 상황을 종합하여 최선의 결정을 돕는 전략 컨설턴트야."},
                        {"role": "user", "content": prompt}
                    ]
                )
                
                st.markdown("---")
                st.subheader("📋 분석 결과")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")
    else:
        st.warning("주제와 선택지를 모두 입력해주세요.")
