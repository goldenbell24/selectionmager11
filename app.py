import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("가이드 분석을 통해 가중치를 정교하게 조정하고 최적의 결정을 내리세요.")

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
if 'advice_result' not in st.session_state:
    st.session_state.advice_result = ""
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = ""

# --- 유틸리티 함수 ---
def get_weight_description(score):
    if score <= 20: return "⚪ **무시 가능**"
    elif score <= 40: return "🔵 **참고 사항**"
    elif score <= 60: return "🟢 **주요 고려**"
    elif score <= 80: return "🟠 **매우 중요**"
    else: return "🔴 **절대적 기준**"

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
                full_results.append(f"📄 [참조: {title}]")
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
        "properties": {"title": {"title": [{"text": {"content": f"📊 분석 결과: {topic}"}}]}},
        "children": blocks[:100]
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.header("📓 Notion 연동")
    notion_key = st.text_input("Notion API Key", type="password", placeholder="ntn_...")
    notion_db_id = st.text_input("Database ID", placeholder="하이픈 포함 가능")
    if st.button("🔌 노션 데이터 불러오기", use_container_width=True):
        st.session_state.notion_data = fetch_notion_full_data(notion_key, notion_db_id)
        st.success("동기화 완료!")

# 2. 항목 관리 (추가/삭제만 담당)
with st.popover("⚙️ 가치 항목 편집 (이름 및 추가/삭제)", use_container_width=True):
    for idx, item in enumerate(st.session_state.value_settings):
        cols = st.columns([4, 1])
        with cols[0]:
            st.session_state.value_settings[idx]["label"] = st.text_input(f"항목 {idx+1}", value=item["label"], key=f"edit_label_{idx}")
        with cols[1]:
            if st.button("🗑️", key=f"del_{idx}"):
                st.session_state.value_settings.pop(idx)
                st.rerun()
    if st.button("➕ 가치 항목 추가", use_container_width=True):
        st.session_state.value_settings.append({"label": "새 항목", "weight": 50})
        st.rerun()

# 3. 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 대학 생활 목표 설정")

st.markdown("### 📋 선택지 입력")
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

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# --- 4. 1단계: 가이드 분석 (가중치 조절 전) ---
st.markdown("---")
if st.button("🔍 1단계: 선택지 특성 분석 및 가중치 가이드 받기", use_container_width=True):
    valid_options = [f"[{o['name']}] 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    if not openai_key or not topic or len(valid_options) < 2:
        st.warning("API 키와 주제, 최소 2개의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("선택지들의 특징을 분석하여 가중치 설정을 제안하는 중..."):
                values_list = ", ".join([v['label'] for v in st.session_state.value_settings])
                prompt = f"""[주제]: {topic}\n[선택지]: {valid_options}\n[고려 가치]: {values_list}\n\n위 선택지들의 장단점을 일반적인 대학생 관점에서 분석해서, 각 가치의 가중치를 어떻게 조절하면 좋을지 조언해줘. 아직 구체적인 점수는 고려하지 말고, 어떤 가치가 이 결정에서 핵심이 될지 가이드라인을 제시해줘."""
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.advice_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 가이드 결과 및 가중치 조절 슬라이더 표시
if st.session_state.advice_result:
    with st.chat_message("assistant"):
        st.markdown("### 💡 AI 가중치 설정 가이드")
        st.markdown(st.session_state.advice_result)
    
    st.markdown("### ⚙️ 2단계: 가중치 정밀 조정")
    st.info("위 가이드를 참고하여, 이번 결정에서 각 항목이 차지하는 실제 비중을 설정하세요.")
    
    # 메인 화면에 슬라이더 배치
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            st.session_state.value_settings[idx]["weight"] = st.slider(
                f"**{item['label']}**", 0, 100, item["weight"], key=f"main_weight_{idx}"
            )
            st.caption(get_weight_description(st.session_state.value_settings[idx]["weight"]))

    # --- 5. 2단계: 최종 심층 분석 ---
    if st.button("🚀 3단계: 최종 심층 분석 시작", use_container_width=True, type="primary"):
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("설정된 가중치를 반영하여 최종 순위를 산출 중..."):
                value_context = "\n".join([f"- {v['label']}: {v['weight']}/100" for v in st.session_state.value_settings])
                valid_options_full = [f"[{o['name']}] 상세: {o['detail']}, 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
                
                prompt = f"""[주제]: {topic}\n[가중치 설정]:\n{value_context}\n[선택지 정보]:\n{valid_options_full}\n\n사용자가 설정한 가중치를 엄격하게 적용하여 각 선택지의 상대적 우위를 분석하고, 최종 순위와 이유를 Markdown 표와 리스트로 작성해줘."""
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 최종 결과 및 노션 저장
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 최종 심층 분석 완료")
    st.markdown(st.session_state.analysis_result)
    
    if st.button("💾 이 결과를 노션에 새 페이지로 저장", use_container_width=True):
        if save_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result):
            st.balloons(); st.success("노션에 성공적으로 기록되었습니다!")
        else: st.error("노션 저장에 실패했습니다.")
