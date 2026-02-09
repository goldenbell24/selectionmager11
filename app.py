import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("노션의 기록과 가치관을 결합하고, 분석 결과를 다시 노션에 기록합니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 
if 'value_settings' not in st.session_state:
    st.session_state.value_settings = [
        {"label": "경제적 효율성", "weight": 50},
        {"label": "시간적 효율성", "weight": 50},
        {"label": "개인적 즐거움", "weight": 50}
    ]
if 'notion_data' not in st.session_state:
    st.session_state.notion_data = ""
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = ""

# --- 유틸리티 함수 ---
def get_weight_description(score):
    if score <= 20: return "⚪ **무시 가능**"
    elif score <= 40: return "🔵 **참고 사항**"
    elif score <= 60: return "🟢 **주요 고려**"
    elif score <= 80: return "🟠 **매우 중요**"
    else: return "🔴 **절대적 기준**"

def get_page_content(api_key, page_id):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28"}
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            blocks = response.json().get("results", [])
            content_list = []
            for block in blocks:
                block_type = block.get("type")
                if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item", "quote", "callout", "to_do"]:
                    rich_text = block.get(block_type, {}).get("rich_text", [])
                    text = "".join([t.get("plain_text", "") for t in rich_text])
                    if text: content_list.append(text)
            return "\n".join(content_list)
        return ""
    except: return ""

def fetch_notion_full_data(api_key, database_id):
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
            if not pages: return "노션 데이터베이스가 비어 있습니다."
            
            full_results = []
            for page in pages:
                properties = page.get("properties", {})
                title = "제목 없음"
                for prop in properties.values():
                    if prop.get('type') == 'title':
                        title_list = prop.get('title', [])
                        title = title_list[0]['plain_text'] if title_list else "제목 없음"
                page_id = page.get("id")
                body_content = get_page_content(api_key, page_id)
                full_results.append(f"📄 [페이지: {title}]\n{body_content}\n")
            return "\n".join(full_results)
        else:
            return f"❌ 오류 ({response.status_code}): {response.json().get('message')}"
    except Exception as e: return f"⚠️ 연결 실패: {str(e)}"

def save_analysis_to_notion(api_key, database_id, topic, result_text):
    """분석 결과를 노션 데이터베이스에 새 페이지로 저장합니다."""
    clean_db_id = database_id.replace("-", "").strip()
    url = "https://api.notion.com/v1/pages"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }
    
    # 마크다운 텍스트를 노션 블록(문단) 리스트로 변환
    blocks = []
    for line in result_text.split('\n'):
        if line.strip():
            blocks.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": line}}]}
            })

    # 데이터베이스의 제목 속성(Title)의 이름을 동적으로 찾아야 하지만, 보통 'Name' 혹은 첫 번째 속성입니다.
    # 여기서는 일반적인 'title' 속성을 대상으로 생성합니다.
    payload = {
        "parent": {"database_id": clean_db_id},
        "properties": {
            "title": { # 데이터베이스의 제목 필드 이름이 다를 경우 수정 필요 (예: "Name")
                "title": [{"text": {"content": f"📊 분석 결과: {topic}"}}]
            }
        },
        "children": blocks[:100] # 노션 API는 한 번에 최대 100개 블록까지만 허용
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200: return True
        else:
            # 제목 필드 이름이 'title'이 아닐 경우(예: 'Name') 재시도 로직
            payload["properties"] = {"Name": payload["properties"]["title"]}
            response = requests.post(url, headers=headers, json=payload)
            return response.status_code == 200
    except: return False

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.header("📓 Notion 연동")
    notion_key = st.text_input("Notion API Key", type="password", placeholder="ntn_...")
    notion_db_id = st.text_input("Database ID", placeholder="하이픈 포함 가능")
    
    if st.button("🔌 노션 데이터 불러오기", use_container_width=True):
        if notion_key and notion_db_id:
            with st.spinner("본문 수집 중..."):
                st.session_state.notion_data = fetch_notion_full_data(notion_key, notion_db_id)
                st.success("동기화 완료!")
        else: st.warning("API 키와 DB ID를 입력해주세요.")

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
        st.session_state.value_settings.append({"label": "새 항목", "weight": 50})
        st.rerun()

# 3. 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 방학 프로젝트 주제 선정")

if st.session_state.notion_data:
    with st.expander("📂 참조된 노션 심층 데이터", expanded=False):
        st.text_area("수집 내용 미리보기", value=st.session_state.notion_data, height=150)

st.markdown("### 📋 현재 고려 중인 선택지")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1: name = st.text_input("이름", key=f"opt_name_{i}")
        with c2: detail = st.text_input("기본 설명", key=f"opt_det_{i}")
        c3, c4 = st.columns(2)
        with c3: pros = st.text_area("장점", key=f"opt_pros_{i}", height=70)
        with c4: cons = st.text_area("단점", key=f"opt_cons_{i}", height=70)
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. 분석 실행
if st.button("🚀 데이터 통합 정밀 분석 시작", use_container_width=True):
    valid_options = [f"[{o['name']}]\n- 상세: {o['detail']}\n- 장점: {o['pros']}\n- 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    
    if not openai_key: st.error("OpenAI API 키를 입력해주세요.")
    elif not topic or len(valid_options) < 2: st.warning("주제와 2개 이상의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("심층 분석 중..."):
                value_context = "\n".join([f"- {item['label']}: {item['weight']}/100" for item in st.session_state.value_settings])
                notion_context = f"\n[노션 데이터]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""[주제]: {topic}\n{notion_context}\n[가치관]: {value_context}\n[선택지]:\n{"\n\n".join(valid_options)}\n\n위 데이터를 바탕으로 선택지별 상대적 우위를 분석하고 최종 순위를 제안해줘."""
                
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 분석 결과 및 저장 버튼 표시
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 분석 완료!")
    st.markdown(st.session_state.analysis_result)
    
    # 노션 저장 버튼 (분석 결과가 있을 때만 표시)
    if st.button("💾 분석 결과를 노션에 새 페이지로 저장하기", use_container_width=True):
        if notion_key and notion_db_id:
            with st.spinner("노션에 새 페이지 생성 중..."):
                success = save_analysis_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result)
                if success: st.balloons(); st.success("노션 데이터베이스에 새로운 결과 페이지가 생성되었습니다!")
                else: st.error("노션 저장 중 오류가 발생했습니다. 권한 설정을 확인해주세요.")
        else: st.warning("사이드바에서 노션 API 키와 DB ID를 먼저 입력해주세요.")
