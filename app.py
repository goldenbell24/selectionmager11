import streamlit as st
from openai import OpenAI
import requests

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("중요도 기반의 상대적 비교를 통해 최적의 결정을 제안합니다.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 
if 'value_settings' not in st.session_state:
    st.session_state.value_settings = [
        {"label": "예산 효율성", "level": "보통"},
        {"label": "시간적 효율성", "level": "보통"},
        {"label": "개인적 즐거움", "level": "보통"}
    ]
if 'notion_data' not in st.session_state:
    st.session_state.notion_data = ""
if 'advice_result' not in st.session_state:
    st.session_state.advice_result = ""
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = ""

# 중요도 5단계 정의
IMPORTANCE_LEVELS = ["매우 덜 중요", "덜 중요", "보통", "중요", "매우 중요"]

# --- 유틸리티 함수 ---
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
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 여행지 최종 선정")

st.markdown("### 📋 1단계: 선택지 입력")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        name = c1.text_input("이름", key=f"opt_name_{i}", placeholder="예: 제주도")
        detail = c2.text_input("기본 설명", key=f"opt_det_{i}", placeholder="3박 4일, 예산 80만원")
        c3, c4 = st.columns(2)
        pros = c3.text_area("장점", key=f"opt_pros_{i}", placeholder="익숙함, 짧은 이동시간", height=70)
        cons = c4.text_area("단점", key=f"opt_cons_{i}", placeholder="성수기 인파, 렌트카 비용", height=70)
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# --- 3. 가이드 분석 실행 ---
st.markdown("---")
if st.button("🔍 AI 가치 항목 및 중요도 가이드 받기", use_container_width=True):
    valid_options = [f"[{o['name']}] 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    if not openai_key or not topic or len(valid_options) < 2:
        st.warning("API 키와 주제, 최소 2개의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("과거 데이터와 현재 상황을 분석하여 가이드를 작성 중..."):
                current_values = ", ".join([v['label'] for v in st.session_state.value_settings])
                notion_context = f"\n[사용자의 과거 고민 이력]:\n{st.session_state.notion_data}" if st.session_state.notion_data else ""
                
                prompt = f"""
                [주제]: {topic}
                {notion_context}
                [현재 가치 항목]: {current_values}
                [현재 선택지]: {valid_options}

                대학생 사용자를 위해 다음 가이드를 제공해줘:
                1. 과거 노션 데이터를 참고할 때, 사용자가 이전에 내린 결정에서 어떤 가치를 가장 '중요'하게 여겼었는지 분석해줘.
                2. 이번 결정에서 5단계 중요도(매우 덜 중요 ~ 매우 중요)를 각각 어떻게 설정하면 좋을지 추천해줘.
                3. 현재 항목 외에 '추가'하거나 '삭제'할 항목이 있다면 그 이유와 함께 제안해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.advice_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# --- 4. 가중치 정밀 조정 (5단계 체크박스/라디오 방식) ---
if st.session_state.advice_result:
    with st.chat_message("assistant"):
        st.markdown("### 💡 AI 중요도 설정 가이드")
        st.markdown(st.session_state.advice_result)
    
    st.markdown("### ⚙️ 2단계: 가중치 및 항목 정밀 조정")
    st.info("AI의 추천을 참고하여 중요도를 5단계로 설정하세요.")
    
    # 가치 항목 편집 및 중요도 설정
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True):
            col_name, col_level, col_del = st.columns([2, 3, 1])
            with col_name:
                new_label = st.text_input(f"가치 이름 #{idx+1}", value=item["label"], key=f"label_edit_{idx}")
                st.session_state.value_settings[idx]["label"] = new_label
            with col_level:
                # 5단계 라디오 버튼 (가로 배치)
                selected_level = st.radio(
                    f"'{new_label}' 중요도", 
                    options=IMPORTANCE_LEVELS, 
                    index=IMPORTANCE_LEVELS.index(item["level"]),
                    key=f"level_radio_{idx}",
                    horizontal=True
                )
                st.session_state.value_settings[idx]["level"] = selected_level
            with col_del:
                st.write("")
                if st.button("🗑️ 삭제", key=f"del_val_{idx}"):
                    st.session_state.value_settings.pop(idx)
                    st.rerun()

    # 새로운 항목 추가
    col_add_name, col_add_btn = st.columns([4, 1])
    with col_add_name:
        new_val_name = st.text_input("추가할 새로운 가치 이름", key="new_val_input")
    with col_add_btn:
        st.write("")
        if st.button("➕ 항목 추가", use_container_width=True):
            if new_val_name:
                st.session_state.value_settings.append({"label": new_val_name, "level": "보통"})
                st.rerun()

    # --- 5. 최종 상대적 비교 분석 ---
    st.markdown("---")
    if st.button("🚀 3단계: 최종 상대 비교 분석 시작", use_container_width=True, type="primary"):
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("각 선택지를 1:1로 대조하며 상대적 우위를 분석 중..."):
                value_context = "\n".join([f"- {v['label']}: {v['level']}" for v in st.session_state.value_settings])
                valid_options_full = [f"[{o['name']}] 상세: {o['detail']}, 장점: {o['pros']}, 단점: {o['cons']}" for o in option_data if o['name'].strip()]
                
                prompt = f"""
                [분석 주제]: {topic}
                
                [사용자 설정 중요도]:
                {value_context}
                
                [비교 대상 선택지]:
                {"\n\n".join(valid_options_full)}

                위 데이터를 바탕으로 다음 지침에 따라 '상대적 분석'을 수행해줘:
                1. 단순한 점수 합산 방식을 지양하고, 선택지 간의 1:1 상대적 비교에 집중해줘.
                2. "A는 B에 비해 [중요도가 높은 가치] 측면에서 어떤 우위가 있는지", 반대로 "B가 A보다 나은 점은 무엇인지"를 교차 분석해줘.
                3. 사용자가 설정한 중요도 단계(매우 중요 ~ 매우 덜 중요)를 분석의 우선순위로 삼아줘.
                4. 최종적으로 어떤 선택지가 사용자의 현재 가치관에 비추어 가장 설득력 있는지 제안해줘.
                5. 결과는 Markdown 표(상대 비교표)와 논리적인 리스트로 가독성 있게 작성해줘.
                """
                response = client.chat.completions.create(model="gpt-4o", messages=[{"role": "user", "content": prompt}])
                st.session_state.analysis_result = response.choices[0].message.content
        except Exception as e: st.error(f"오류: {e}")

# 최종 결과 출력 및 노션 저장
if st.session_state.analysis_result:
    st.markdown("---")
    st.success("✅ 최종 상대 비교 분석 완료")
    st.markdown(st.session_state.analysis_result)
    
    if st.button("💾 이 분석 결과를 노션에 새 페이지로 기록", use_container_width=True):
        if save_to_notion(notion_key, notion_db_id, topic, st.session_state.analysis_result):
            st.balloons(); st.success("노션에 성공적으로 저장되었습니다!")
        else: st.error("노션 저장에 실패했습니다.")
