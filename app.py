import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기 (Notion 본문 통합)")
st.subheader("노션의 상세 기록과 나의 가치관을 결합하여 분석합니다.")

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

def get_page_content(api_key, page_id):
    """특정 페이지의 블록(본문) 내용들을 가져옵니다."""
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28"
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            blocks = response.json().get("results", [])
            content_list = []
            for block in blocks:
                block_type = block.get("type")
                # 다양한 텍스트 블록 지원
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote", "callout", "to_do"]:
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text:
                        content_list.append(text)
            return "\n".join(content_list)
        return ""
    except:
        return ""

def fetch_notion_full_data(api_key, database_id):
    """노션 DB의 모든 페이지 제목과 상세 본문을 가져옵니다."""
    clean_db_id = database_id.replace("-", "").strip()
    url = f"https://api.notion.com/v1/databases/{clean_db_id}/query"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200:
            data = response.json()
            pages = data.get("results", [])
            if not pages:
                return "노션 데이터베이스가 비어 있습니다."
            
            full_results = []
            for page in pages:
                # 1. 제목 추출
                properties = page.get("properties", {})
                title = "제목 없음"
                for prop in properties.values():
                    if prop.get('type') == 'title':
                        title_list = prop.get('title', [])
                        title = title_list[0]['plain_text'] if title_list else "제목 없음"
                
                # 2. 본문 상세 내용 추출
                page_id = page.get("id")
                body_content = get_page_content(api_key, page_id)
                
                full_results.append(f"📄 [페이지: {title}]\n{body_content}\n")
            
            return "\n".join(full_results)
        else:
            error_msg = response.json().get("message", "알 수 없는 오류")
            return f"❌ 오류 발생 ({response.status_code}): {error_msg}"
    except Exception as e:
        return f"⚠️ 연결 실패: {str(e)}"

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    
    st.markdown("---")
    st.header("📓 Notion 연동")
    notion_key = st.text_input("Notion API Key", type="password", placeholder="ntn_...")
    notion_db_id = st.text_input("Database ID", placeholder="32자리 ID 입력")
    
    if st.button("🔌 노션 전체 데이터 불러오기"):
        if notion_key and notion_db_id:
            with st.spinner("본문 내용까지 심층 수집 중..."):
                st.session_state.notion_data = fetch_notion_full_data(notion_key, notion_db_id)
                st.success("노션 데이터 동기화 완료!")
        else:
            st.warning("API 키와 DB ID를 확인해주세요.")

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

# 3. 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 방학 프로젝트 주제 선정")

if st.session_state.notion_data:
    with st.expander("📂 참조된 노션 심층 데이터", expanded=False):
        st.info("각 페이지의 본문 텍스트까지 모두 수집되었습니다.")
        st.text_area("수집된 내용 미리보기", value=st.session_state.notion_data, height=200)

st.markdown("### 📋 현재 고려 중인 선택지")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            name = st.text_input("이름", key=f"opt_name_{i}", placeholder="예: A 프로젝트")
        with c2:
            detail = st.text_input("기본 설명", key=f"opt_det_{i}", placeholder="기간, 비용 등")
        c3, c4 = st.columns(2)
        with c3:
            pros = st.text_area("장점", key=f"opt_pros_{i}", height=70)
        with c4:
            cons = st.text_area("단점", key=f"opt_cons_{i}", height=70)
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. 분석 실행
if st.button("🚀 전체 데이터 기반 정밀 분석 시작"):
    valid_options = [f"[{o['name']}]\n- 상세: {o['detail']}\n- 장점: {o['pros']}\n- 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    
    if not openai_key:
        st.error("OpenAI API 키를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 2개 이상의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("노션의 상세 맥락과 현재 가치관을 대조 분석 중..."):
                value_context = "\n".join([f"- {item['label']}: {item['weight']}/100" for item in st.session_state.value_settings])
                notion_context = f"\n[노션 상세 참조 데이터]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""
                [분석 주제]: {topic}
                {notion_context}
                
                [사용자 가치관 가중치]:
                {value_context}
                
                [고려 중인 선택지]:
                {"\n\n".join(valid_options)}
                
                지침:
                1. 노션의 상세 본문 내용을 꼼꼼히 반영하여 현재 선택지와의 연관성을 분석해줘.
                2. 사용자가 설정한 가치관 수치를 바탕으로 각 선택지의 기대 효과를 상대 분석해줘.
                3. 노션 데이터에 기반해 사용자가 놓치고 있을 수 있는 리스크나 기회 비용을 언급해줘.
                4. 최종적인 추천 순위와 상세 논거를 Markdown으로 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 심층 분석 완료!")
                st.markdown(response.choices[0].message.content)
        except Exception as e:
            st.error(f"오류 발생: {e}")
