import streamlit as st
from openai import OpenAI
import requests
import re

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("주제에 최적화된 가치 기준을 AI가 직접 제안하고 분석합니다.")

# --- 1. 세션 상태 초기화 ---
def init_session_state(reset_data=False):
    if 'options_count' not in st.session_state or reset_data:
        st.session_state.options_count = 2 
    if 'value_settings' not in st.session_state or reset_data:
        st.session_state.value_settings = []
    if 'advice_result' not in st.session_state or reset_data:
        st.session_state.advice_result = ""
    if 'analysis_result' not in st.session_state or reset_data:
        st.session_state.analysis_result = ""
    if 'notion_data' not in st.session_state:
        st.session_state.notion_data = ""

init_session_state()

IMPORTANCE_LEVELS = ["매우 덜 중요", "덜 중요", "보통", "중요", "매우 중요"]

# --- 2. 유틸리티 함수 (노션 및 데이터 처리) ---
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
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json={})
        if response.status_code == 200:
            pages = response.json().get("results", [])
            full_results = []
            for page in pages:
                title = "제목 없음"
                for prop in page.get("properties", {}).values():
                    if prop.get('type') == 'title':
                        title = prop.get('title')[0].get('plain_text') if prop.get('title') else "제목 없음"
                page_id = page.get("id")
                body = get_page_content(api_key, page_id)
                full_results.append(f"📄 [과거 기록: {title}]\n{body}\n")
            return "\n".join(full_results)
        return f"❌ 오류: {response.status_code}"
    except Exception as e: return f"⚠️ 연결 실패: {str(e)}"

def save_to_notion(api_key, database_id, topic, result_text):
    clean_db_id = database_id.replace("-", "").strip()
    url = "https://api.notion.com/v1/pages"
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    blocks = [{"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": line}}]}} for line in result_text.split('\n') if line.strip()]
    payload = {
        "parent": {"database_id": clean_db_id},
        "properties": {"title": {"title": [{"text": {"content": f"📊 상대 분석 결과: {topic}"}}]}},
        "children": blocks[:100]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200

# --- 3. 사이드바 ---
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.header("📓 Notion 연동")
    notion_key = st.text_input("Notion API Key", type="password", placeholder="ntn_...")
    notion_db_id = st.text_input("Database ID", placeholder="하이픈 포함 가능")
    if st.button("🔌 노션 데이터 불러오기", use_container_width=True):
        st.session_state.notion_data = fetch_notion_full_data(notion_key, notion_db_id)
        st.success("노션 데이터 동기화 완료!")

# --- 4. 1단계: 선택지 입력 ---
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 대학원 진학 vs 취업", key="topic_input")

st.markdown("### 📋 1단계: 선택지 입력")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        name = c1.text_input("이름", key=f"opt_name_{i}")
        detail = c2.text_input("기본 설명", key=f"opt_det_{i}")
        c3, c4 = st.columns(2)
        pros = c3.text_area("장점", key=f"opt_pros_{i}", height=70)
        cons = c4.text_area("단점", key=f"opt_cons_{i}", height=70)
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

col_add, col_reset = st.columns(2)
with col_add:
    if st.button("➕ 선택지 추가", use_container_width=True):
        st.session_state.options_count += 1; st.rerun()
with col_reset:
    if st.button("🗑️ 선택지만 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("opt_"): del st.session_state[key]
        st.session_state.options_count = 2; st.rerun()

# --- 5. 2단계: AI 맞춤형 가치 생성 및 가이드 ---
st.markdown("---")
if st.button("🔍 AI 맞춤 가치 생성 및 가중치 가이드 받기", use_container_width=True):
    valid_options = [f"[{o['name']}] 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    if not openai_key or not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("주제에 적합한 가치 항목을 생성하는 중..."):
                notion_context = f"\n[사용자의 노션 과거 기록]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""
                [현재 주제]: {topic}
                {notion_context}
                [현재 선택지]: {valid_options}

                대학생 사용자를 위해 다음을 수행해줘:
                1. 노션 기록과 주제를 분석하여 이 결정에서 고려해야 할 핵심 가치 항목 3~5개를 새로 생성해줘. (예: 예산, 학업 영향, 미래 성장성 등)
                2. 생성한 가치 항목들을 응답 하단에 반드시 'VALUE_START: 항목1, 항목2, 항목3 :VALUE_END' 형식으로 포함해줘.
                3. 과거 사례를 참고하여 각 항목의 추천 중요도(5단계)를 제안하고 그 이유를 설명해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                res_text = response.choices[0].message.content
                st.session_state.advice_result = res_text
                
                match = re.search(r"VALUE_START: (.*?) :VALUE_END", res_text)
                if match:
                    new_labels = [label.strip() for label in match.group(1).split(",")]
                    st.session_state.value_settings = [{"label": label, "level": "보통"} for label in new_labels]
                
                st.rerun()
        except Exception as e: st.error(f"오류: {e}")

# --- 6. 가중치 정밀 조정 ---
if st.session_state.advice_result:
    with st.chat_message("assistant"):
        clean_advice = re.sub(r"VALUE_START: .* :VALUE_END", "", st.session_state.advice_result)
        st.markdown(clean_advice)
    
    st.markdown("### ⚙️ 2단계: AI 추천 가치 및 중요도 정밀 조정")
    
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            col_name, col_level, col_del = st.columns([2, 3, 1])
            with col_name:
                st.session_state.value_settings[idx]["label"] = st.text_input(f"가치 이름 #{idx+1}", value=item["label"], key=f"label_edit_{idx}")
            with col_level:
                st.session_state.value_settings[idx]["level"] = st.radio(
                    f"'{item['label']}' 중요도", options=IMPORTANCE_LEVELS, 
                    index=IMPORTANCE_LEVELS.index(item["level"]), 
                    key=f"level_radio_{idx}", horizontal=True
                )
            with col_del:
                st.write(""); 
                if st.button("🗑️ 삭제", key=f"del_val_{idx}"): st.session_state.value_settings.pop(idx); st.rerun()

    col_add_name, col_add_btn = st.columns([4, 1])
    new_val_name = col_add_name.text_input("직접 추가할 가치 이름", key="new_val_input")
    if col_add_btn.button("➕ 항목 추가", use_container_width=True):
        if new_val_name: st.session_state.value_settings.append({"label": new_val_name, "level": "보통"}); st.rerun()

    # --- 7. 최종 상대 분석 (오류 수정 지점) ---
    st.markdown("---")
    if st.button("🚀 3단계: 최종 상대 비교 분석 시작", use_container_width=True, type="primary"):
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("최종 상대적 우위 분석 중..."):
                # 수정: f 뒤에 괄호 대신 따옴표가 오도록 수정함
                value_context = "\n".join([f"- {v['label']}: {v['level']}" for v in st.session_state.value_settings])
                valid_options_full = [f"[{o['name']}] 상세: {o['detail']}, 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
                
                prompt = f"""
                [분석 주제]: {topic}
                [과거 맥락]: {st.session_state.notion_data[:1000]}
                [중요도 설정]:
                {value_context}
                [선택지]:
                {"\n\n".join(valid_options_full)}

                위 데이터를 기반으로 과거 경험을 반영한 1:1 상대 분석을 수행하고 최적의 제안을 해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 최종 결과 및 노션 저장
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 최종 분석 완료")
    st.markdown(st.session_state.analysis_result)
    if st.button("💾 결과를 노션에 새 페이지로 기록", use_container_width=True):
        if save_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result):
            st.balloons(); st.success("저장 완료!")
        else: st.error("저장 실패")

# --- 8. 전체 리셋 ---
st.markdown("<br><br><br>---", unsafe_allow_html=True)
if st.button("🔄 모든 입력 및 분석 결과 초기화 (API 제외)", use_container_width=True):
    for key in list(st.session_state.keys()):
        if key.startswith(("opt_", "label_edit_", "level_radio_", "new_val_input", "topic_input")):
            del st.session_state[key]
    init_session_state(reset_data=True); st.rerun()
