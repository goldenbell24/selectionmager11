import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("과거의 기록과 현재의 가치를 결합하여 최적의 의사결정을 설계합니다.")

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
            data = response.json()
            pages = data.get("results", [])
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
        st.success("노션 데이터 동기화 완료!")

# 2. 메인 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 방학 프로젝트 주제 선정")

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

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# --- 3. 가이드 분석 실행 ---
st.markdown("---")
if st.button("🔍 AI 가중치 및 가치 항목 가이드 받기", use_container_width=True):
    valid_options = [f"[{o['name']}] 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    if not openai_key or not topic or len(valid_options) < 2:
        st.warning("API 키와 주제, 최소 2개의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("과거 데이터와 현재 선택지를 분석 중..."):
                current_values = ", ".join([v['label'] for v in st.session_state.value_settings])
                notion_context = f"\n[사용자의 과거 고민 이력]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""
                [주제]: {topic}
                {notion_context}
                [현재 설정된 가치 항목]: {current_values}
                [현재 선택지]: {valid_options}

                위 정보를 바탕으로 대학생 사용자의 의사결정을 돕기 위한 가이드를 작성해줘:
                1. 노션에 기록된 과거 고민들을 참고하여 사용자가 중요하게 여겨왔던 가치관이 무엇인지 파악하고, 이번 결정에 적절한 가중치(%)를 제안해줘.
                2. 현재 설정된 가치 항목 외에 추가하면 좋을 가치와, 이번 결정에서 불필요해 보이는 삭제 대상 가치를 추천해줘.
                3. 분석 근거를 명확하고 친절하게 설명해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.advice_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# --- 4. 가중치 정밀 조정 및 항목 편집 화면 ---
if st.session_state.advice_result:
    with st.chat_message("assistant"):
        st.markdown("### 💡 AI 가중치 및 항목 추천 가이드")
        st.markdown(st.session_state.advice_result)
    
    st.markdown("### ⚙️ 2단계: 가치 항목 및 가중치 정밀 조정")
    st.info("AI의 추천을 참고하여 분석 기준을 최종 확정하세요. 항목을 추가하거나 삭제할 수 있습니다.")
    
    # 가중치 슬라이더 및 삭제 버튼
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            col_slide, col_del = st.columns([5, 1])
            with col_slide:
                # 항목 이름 수정 및 슬라이더
                new_label = st.text_input(f"가치 이름 #{idx+1}", value=item["label"], key=f"label_edit_{idx}")
                st.session_state.value_settings[idx]["label"] = new_label
                weight = st.slider(f"'{new_label}'의 가중치", 0, 100, item["weight"], key=f"weight_slide_{idx}")
                st.session_state.value_settings[idx]["weight"] = weight
                st.caption(get_weight_description(weight))
            with col_del:
                st.write("") # 간격 맞춤
                if st.button("🗑️ 삭제", key=f"del_val_{idx}"):
                    st.session_state.value_settings.pop(idx)
                    st.rerun()

    # 새로운 가치 항목 추가
    col_add_name, col_add_btn = st.columns([4, 1])
    with col_add_name:
        new_val_name = st.text_input("새로운 가치 항목 이름", placeholder="예: 미래 성장성", key="new_val_input")
    with col_add_btn:
        st.write("") # 간격 맞춤
        if st.button("➕ 항목 추가", use_container_width=True):
            if new_val_name:
                st.session_state.value_settings.append({"label": new_val_name, "weight": 50})
                st.rerun()

    # --- 5. 최종 심층 분석 ---
    st.markdown("---")
    if st.button("🚀 3단계: 최종 심층 분석 시작", use_container_width=True, type="primary"):
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("설정된 가중치를 반영하여 정밀 시뮬레이션 중..."):
                value_context = "\n".join([f"- {v['label']}: {v['weight']}/100" for v in st.session_state.value_settings])
                valid_options_full = [f"[{o['name']}] 상세: {o['detail']}, 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
                
                prompt = f"""
                [주제]: {topic}
                [사용자 최종 가중치]:
                {value_context}
                [선택지 정보]:
                {valid_options_full}

                위 데이터를 바탕으로:
                1. 사용자가 설정한 가중치를 엄격하게 적용하여 각 선택지의 점수를 산출하고 순위를 매겨줘.
                2. 각 선택지가 가중치가 높은 핵심 가치들을 얼마나 충족하는지 상대적으로 비교 분석해줘.
                3. 최종 결정을 내리는 데 도움이 될 한 줄 평을 작성해줘.
                결과는 Markdown 표와 리스트로 가독성 있게 작성해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 최종 결과 출력 및 저장
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 최종 심층 분석 결과")
    st.markdown(st.session_state.analysis_result)
    
    if st.button("💾 분석 결과를 노션에 새 페이지로 기록", use_container_width=True):
        if save_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result):
            st.balloons(); st.success("노션에 성공적으로 저장되었습니다!")
        else: st.error("노션 저장에 실패했습니다. API 설정을 확인하세요.")
