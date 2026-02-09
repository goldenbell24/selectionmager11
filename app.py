import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기 (Notion 연동)")
st.subheader("노션의 기록과 나의 가치관을 결합하여 최적의 결정을 내립니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 
if 'value_settings' not in st.session_state:
    st.session_state.value_settings = [
        {"label": "예산 효율성", "weight": 50},
        {"label": "시간적 효율성", "weight": 50},
        {"label": "개인적 즐거움", "weight": 50}
    ]
if 'notion_data' not in st.session_state:
    st.session_state.notion_data = ""

# --- 유틸리티 함수 ---
def get_weight_description(score):
    if score <= 20: return "⚪ 무시 가능"
    elif score <= 40: return "🔵 참고 사항"
    elif score <= 60: return "🟢 주요 고려"
    elif score <= 80: return "🟠 매우 중요"
    else: return "🔴 절대적 기준"

def fetch_notion_data(api_key, database_id):
    """노션 데이터베이스의 내용을 텍스트로 가져옵니다."""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            # 간단한 텍스트 추출 로직 (데이터베이스 구조에 따라 커스텀 필요)
            pages = data.get("results", [])
            extracted_text = ""
            for page in pages:
                # 'Name' 혹은 첫 번째 타이틀 속성 추출
                properties = page.get("properties", {})
                for prop in properties.values():
                    if prop['type'] == 'title':
                        title = prop['title'][0]['plain_text'] if prop['title'] else "제목 없음"
                        extracted_text += f"• {title}\n"
            return extracted_text
        else:
            return f"오류 발생: {response.status_code}"
    except Exception as e:
        return f"연결 실패: {str(e)}"

# 1. 사이드바 설정 (API 및 노션 설정)
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    
    st.markdown("---")
    st.header("📓 Notion 연동 (선택)")
    notion_key = st.text_input("Notion API Key", type="password", placeholder="secret_...")
    notion_db_id = st.text_input("Database ID", placeholder="노션 DB 주소에서 추출")
    
    if st.button("🔌 노션 데이터 불러오기"):
        if notion_key and notion_db_id:
            with st.spinner("노션 데이터를 동기화 중..."):
                st.session_state.notion_data = fetch_notion_data(notion_key, notion_db_id)
                st.success("데이터를 성공적으로 가져왔습니다!")
        else:
            st.warning("노션 API 키와 DB ID를 입력해주세요.")

# 2. 가치관 상세 설정 (팝업)
with st.popover("🎯 의사결정 가치관 & 가중치 편집", use_container_width=True):
    st.markdown("### 🛠️ 분석 가치 항목 설정")
    new_settings = []
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            col_name, col_del = st.columns([4, 1])
            with col_name:
                label = st.text_input(f"가치 항목 {idx+1}", value=item["label"], key=f"label_{idx}")
            with col_del:
                st.write("")
                if st.button("🗑️", key=f"del_{idx}") and len(st.session_state.value_settings) > 1:
                    st.session_state.value_settings.pop(idx)
                    st.rerun()
            weight = st.slider(f"{label} 중요도", 0, 100, item["weight"], key=f"weight_{idx}")
            st.caption(get_weight_description(weight))
            new_settings.append({"label": label, "weight": weight})
    st.session_state.value_settings = new_settings
    if st.button("➕ 새로운 가치 항목 추가", use_container_width=True):
        st.session_state.value_settings.append({"label": "새 가치 항목", "weight": 50})
        st.rerun()

# 3. 사용자 입력 및 노션 데이터 확인
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 여행지 최종 결정")

if st.session_state.notion_data:
    with st.expander("📂 참조된 노션 데이터", expanded=False):
        st.info("아래 내용은 분석 시 '과거 데이터' 및 '참조 정보'로 활용됩니다.")
        st.text(st.session_state.notion_data)

st.markdown("### 📋 현재 고려 중인 선택지")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            name = st.text_input("이름", key=f"opt_name_{i}", placeholder="예: 스페인 여행")
        with c2:
            detail = st.text_input("기본 설명", key=f"opt_det_{i}", placeholder="예: 2주 일정, 400만원")
        c3, c4 = st.columns(2)
        with c3:
            pros = st.text_area("장점", key=f"opt_pros_{i}", placeholder="상세 장점 입력", height=70)
        with c4:
            cons = st.text_area("단점", key=f"opt_cons_{i}", placeholder="상세 단점 입력", height=70)
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. AI 분석 실행
if st.button("🚀 노션 데이터 기반 심층 분석 시작"):
    valid_options = [f"[{o['name']}]\n- 상세: {o['detail']}\n- 장점: {o['pros']}\n- 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("노션 데이터와 현재 선택지를 비교 분석 중..."):
                value_context = "\n".join([f"- {item['label']}: {item['weight']}/100" for item in st.session_state.value_settings])
                
                # 노션 데이터가 있을 경우 프롬프트에 추가
                notion_context = f"\n[참조된 노션 데이터 (과거 이력 및 정보)]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""
                [분석 주제]: {topic}
                {notion_context}
                
                [사용자 정의 가치관 및 가중치]:
                {value_context}
                
                [현재 비교 선택지]:
                {"\n\n".join(valid_options)}
                
                위 정보를 바탕으로 분석해줘:
                1. 노션에 기록된 과거 데이터나 정보가 있다면, 현재 선택지들과 어떤 상관관계가 있는지 분석해줘.
                2. 설정된 가치 가중치를 바탕으로 가장 '합리적인' 선택을 제안해줘.
                3. 노션의 정보를 통해 얻을 수 있는 통찰(Insight)이 있다면 함께 언급해줘.
                4. 결과는 Markdown 표와 리스트로 가독성 있게 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 노션 데이터 통합 분석 완료!")
                st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"오류 발생: {e}")
