import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("결정의 성격에 맞춰 분석 기준을 자유롭게 디자인하세요.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 

if 'value_settings' not in st.session_state:
    st.session_state.value_settings = [
        {"label": "경제적 효율성", "weight": 50},
        {"label": "시간적 효율성", "weight": 50},
        {"label": "개인적 즐거움", "weight": 50}
    ]

if 'risk_tolerance' not in st.session_state:
    st.session_state.risk_tolerance = "균형 잡힌"

# --- 유틸리티 함수: 슬라이더 점수 의미 해석 ---
def get_weight_description(score):
    if score <= 20:
        return "⚪ **무시 가능** (결정에 거의 영향을 주지 않음)"
    elif score <= 40:
        return "🔵 **참고 사항** (있으면 좋지만 없어도 그만)"
    elif score <= 60:
        return "🟢 **주요 고려** (결정의 핵심 축 중 하나)"
    elif score <= 80:
        return "🟠 **매우 중요** (이 조건이 나쁘면 선택하기 어려움)"
    else:
        return "🔴 **절대적 기준** (최우선순위, 타협 불가능)"

# 1. 사이드바 설정
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.info("💡 **Tip**: 메인 화면의 '가치관 상세 설정' 버튼을 통해 분석 기준을 커스텀하세요.")

# 2. 가치관 상세 설정 (팝업창 - UI 구조 개선)
with st.popover("🎯 의사결정 가치관 & 가중치 편집", use_container_width=True):
    st.markdown("### 🛠️ 분석 가치 항목 설정")
    st.caption("항목 이름을 수정하고 바로 아래 슬라이더로 중요도를 조절하세요.")
    
    new_settings = []
    
    # 각 가치 항목별로 이름과 슬라이더를 세트로 배치
    for idx, item in enumerate(st.session_state.value_settings):
        with st.container(border=True): # 항목별 경계선 추가로 시인성 확보
            col_name, col_del = st.columns([4, 1])
            with col_name:
                # 항목 이름 입력
                label = st.text_input(f"가치 항목 {idx+1}", value=item["label"], key=f"label_{idx}")
            with col_del:
                # 삭제 버튼
                st.write("") # 간격 맞춤용
                if st.button("🗑️", key=f"del_{idx}") and len(st.session_state.value_settings) > 1:
                    st.session_state.value_settings.pop(idx)
                    st.rerun()
            
            # 항목 이름 바로 아래에 슬라이더 배치
            weight = st.slider(f"{label} 중요도", 0, 100, item["weight"], key=f"weight_{idx}")
            st.caption(get_weight_description(weight))
            
            new_settings.append({"label": label, "weight": weight})
    
    # 설정 업데이트
    st.session_state.value_settings = new_settings

    # 항목 추가 버튼
    if st.button("➕ 새로운 가치 항목 추가", use_container_width=True):
        st.session_state.value_settings.append({"label": "새 가치 항목", "weight": 50})
        st.rerun()

    st.markdown("---")
    st.session_state.risk_tolerance = st.select_slider(
        "🛡️ 의사결정 성향 (안정성 vs 도전성)",
        options=["매우 보수적", "신중함", "균형 잡힌", "도전적", "매우 실험적"],
        value=st.session_state.risk_tolerance
    )

# 3. 사용자 입력 섹션
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 여름방학 유럽 여행지 결정")

st.markdown("### 📋 비교 선택지 입력")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            name = st.text_input("이름", key=f"opt_name_{i}", placeholder="예: 스페인 여행")
        with c2:
            detail = st.text_input("기본 설명", key=f"opt_det_{i}", placeholder="예: 2주 일정, 예상 경비 400만원")
        
        c3, c4 = st.columns(2)
        with c3:
            pros = st.text_area("장점", key=f"opt_pros_{i}", placeholder="새로운 문화 체험", height=70)
        with c4:
            cons = st.text_area("단점", key=f"opt_cons_{i}", placeholder="높은 비용 부담", height=70)
        
        option_data.append({"name": name, "detail": detail, "pros": pros, "cons": cons})

if st.button("➕ 선택지 추가"):
    st.session_state.options_count += 1
    st.rerun()

# 4. AI 분석 실행
if st.button("🚀 나만의 맞춤 분석 시작"):
    valid_options = [f"[{o['name']}]\n- 상세: {o['detail']}\n- 장점: {o['pros']}\n- 단점: {o['cons']}" for o in option_data if o['name'].strip()]
    
    if not openai_key:
        st.error("사이드바에 OpenAI API Key를 입력해주세요.")
    elif not topic or len(valid_options) < 2:
        st.warning("주제와 최소 2개 이상의 선택지를 입력해주세요.")
    else:
        try:
            client = OpenAI(api_key=openai_key)
            with st.spinner("가치관을 반영하여 심층 분석 중입니다..."):
                value_context = "\n".join([f"- {item['label']}: {item['weight']}/100 ({get_weight_description(item['weight'])})" for item in st.session_state.value_settings])
                
                prompt = f"""
                [분석 주제]: {topic}
                [사용자 정의 가치관]:
                {value_context}
                - 의사결정 성향: {st.session_state.risk_tolerance}
                
                [비교 선택지]:
                {"\n\n".join(valid_options)}
                
                위 데이터를 바탕으로:
                1. 가치 항목별로 각 선택지를 대조 분석해줘.
                2. 점수가 높은 가치에 더 큰 비중을 두어 최종 순위를 산출해줘.
                3. 결과는 Markdown 표와 리스트로 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 분석 완료!")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
