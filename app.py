import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("중요도 기반의 상대적 비교를 통해 최적의 결정을 제안합니다.")

# --- 1. 세션 상태 초기화 및 관리 ---
def init_session_state(reset_data=False):
    if 'options_count' not in st.session_state or reset_data:
        st.session_state.options_count = 2 
    if 'value_settings' not in st.session_state or reset_data:
        st.session_state.value_settings = [
            {"label": "예산 효율성", "level": "보통"},
            {"label": "시간적 효율성", "level": "보통"},
            {"label": "개인적 즐거움", "level": "보통"}
        ]
    if 'advice_result' not in st.session_state or reset_data:
        st.session_state.advice_result = ""
    if 'analysis_result' not in st.session_state or reset_data:
        st.session_state.analysis_result = ""
    if 'notion_data' not in st.session_state:
        st.session_state.notion_data = ""

init_session_state()

# 중요도 5단계 정의
IMPORTANCE_LEVELS = ["매우 덜 중요", "덜 중요", "보통", "중요", "매우 중요"]

# --- 2. 유틸리티 함수 ---
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
                        title_list = prop.get('title', [])
                        title = title_list[0]['plain_text'] if title_list else "제목 없음"
                full_results.append(f"• {title}")
            return "\n".join(full_results)
        return f"❌ 노션 연결 오류: {response.status_code}"
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

# --- 3. 사이드바 설정 ---
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

# --- 4. 메인 입력 섹션 (1단계) ---
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 여행지 최종 선정", key="topic_input")

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

# 선택지 추가 및 선택지 전용 초기화 버튼
col_opt_add, col_opt_reset = st.columns(2)
with col_opt_add:
    if st.button("➕ 선택지 추가", use_container_width=True):
        st.session_state.options_count += 1
        st.rerun()
with col_opt_reset:
    # 선택지 데이터만 초기화하는 버튼
    if st.button("🗑️ 선택지만 초기화", use_container_width=True):
        for key in list(st.session_state.keys()):
            if key.startswith("opt_"):
                del st.session_state[key]
        st.session_state.options_count = 2
        st.rerun()

# --- 5. 가이드 분석 (2단계) ---
st.markdown("---")
if st.button("🔍 AI 가치 항목 및 중요도 가이드 받기", use_container_width=True):
    valid_options = [f"[{o['name']}] 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    if not openai_key or not topic or len(valid_options) < 2:
        st.warning("API 키와 주제, 최소 2개의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("가이드 분석 중..."):
                current_values = ", ".join([v['label'] for v in st.session_state.value_settings])
                notion_context = f"\n[과거 고민 이력]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                prompt = f"[주제]: {topic}\n{notion_context}\n[현재 가치]: {current_values}\n[선택지]: {valid_options}\n\n위 데이터를 바탕으로 중요도 가이드와 항목 추천을 해줘."
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.advice_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# --- 6. 중요도 정밀 조정 화면 ---
if st.session_state.advice_result:
    with st.chat_message("assistant"):
        st.markdown(st.session_state.advice_result)
    
    st.markdown("### ⚙️ 2단계: 가중치 및 항목 정밀 조정")
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            col_name, col_level, col_del = st.columns([2, 3, 1])
            with col_name:
                st.session_state.value_settings[idx]["label"] = st.text_input(f"가치 이름 #{idx+1}", value=item["label"], key=f"label_edit_{idx}")
            with col_level:
                st.session_state.value_settings[idx]["level"] = st.radio(f"'{item['label']}' 중요도", options=IMPORTANCE_LEVELS, index=IMPORTANCE_LEVELS.index(item["level"]), key=f"level_radio_{idx}", horizontal=True)
            with col_del:
                st.write("")
                if st.button("🗑️ 삭제", key=f"del_val_{idx}"):
                    st.session_state.value_settings.pop(idx); st.rerun()

    col_add_name, col_add_btn = st.columns([4, 1])
    new_val_name = col_add_name.text_input("새로운 가치 이름", key="new_val_input")
    if col_add_btn.button("➕ 항목 추가", use_container_width=True):
        if new_val_name: st.session_state.value_settings.append({"label": new_val_name, "level": "보통"}); st.rerun()

    # --- 7. 최종 상대 분석 ---
    st.markdown("---")
    if st.button("🚀 3단계: 최종 상대 비교 분석 시작", use_container_width=True, type="primary"):
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("상대적 우위 분석 중..."):
                value_context = "\n".join([f"- {v['label']}: {v['level']}" for v in st.session_state.value_settings])
                valid_options_full = [f"[{o['name']}] 상세: {o['detail']}, 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
                prompt = f"[주제]: {topic}\n[중요도]:\n{value_context}\n[선택지]:\n{valid_options_full}\n\n위 데이터를 바탕으로 선택지 간의 1:1 상대적 분석을 수행하고 최종 제안을 Markdown으로 작성해줘."
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 최종 결과 및 저장
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 최종 분석 완료")
    st.markdown(st.session_state.analysis_result)
    if st.button("💾 노션에 새 페이지로 기록", use_container_width=True):
        if save_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result):
            st.balloons(); st.success("저장 완료!")
        else: st.error("저장 실패")

# --- 8. 하단 전체 리셋 버튼 ---
st.markdown("<br><br><br>", unsafe_allow_html=True)
st.markdown("---")
if st.button("🔄 모든 입력 및 분석 결과 초기화 (API 설정 제외)", use_container_width=True):
    for key in list(st.session_state.keys()):
        if key.startswith(("opt_", "label_edit_", "level_radio_", "new_val_input", "topic_input")):
            del st.session_state[key]
    init_session_state(reset_data=True)
    st.rerun()
