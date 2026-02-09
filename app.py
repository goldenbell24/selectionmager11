import streamlit as st
from openai import OpenAI

# 페이지 설정
st.set_page_config(page_title="AI 상대적 의사결정 분석기", page_icon="⚖️", layout="wide")

st.title("⚖️ AI 상대적 의사결정 분석기")
st.subheader("결정의 성격에 맞춰 분석 기준을 자유롭게 디자인하세요.")

# --- 세션 상태 초기화 ---
if 'options_count' not in st.session_state:
    st.session_state.options_count = 2 

# 분석 가치 항목 초기화 (리스트 형태로 관리하여 순서 유지 및 편집 용이성 확보)
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

# 1. 사이드바 설정 (API 키)
with st.sidebar:
    st.header("🔑 API 설정")
    openai_key = st.text_input("OpenAI API Key", type="password", placeholder="sk-...")
    st.markdown("---")
    st.info("💡 **Tip**: 메인 화면의 '가치관 상세 설정' 버튼을 통해 분석 기준을 커스텀하세요.")

# 2. 가치관 상세 설정 (팝업창 - 편집 기능 추가)
with st.popover("🎯 의사결정 가치관 & 가중치 편집", use_container_width=True):
    st.markdown("### 🛠️ 분석 가치 항목 편집")
    st.caption("결정하려는 주제에 맞는 평가 항목을 추가하거나 삭제하세요.")
    
    # 항목 편집 레이아웃
    new_settings = []
    for idx, item in enumerate(st.session_state.value_settings):
        cols = st.columns([3, 1])
        with cols[0]:
            new_label = st.text_input(f"항목 {idx+1} 이름", value=item["label"], key=f"edit_label_{idx}")
        with cols[1]:
            # 삭제 버튼 (최소 1개는 남겨두도록 처리)
            if st.button("🗑️ 삭제", key=f"del_btn_{idx}") and len(st.session_state.value_settings) > 1:
                st.session_state.value_settings.pop(idx)
                st.rerun()
        new_settings.append({"label": new_label, "weight": item["weight"]})
    
    # 항목 추가 버튼
    if st.button("➕ 가치 항목 추가"):
        st.session_state.value_settings.append({"label": "새 가치 항목", "weight": 50})
        st.rerun()

    st.markdown("---")
    st.markdown("### 📊 가중치 세부 설정")
    
    # 슬라이더 및 의미 표시
    for idx, item in enumerate(new_settings):
        st.write(f"**{item['label']}**")
        weight = st.slider(f"{item['label']} 가중치 설정", 0, 100, item["weight"], 
                           key=f"slide_{idx}", label_visibility="collapsed")
        st.caption(get_weight_description(weight))
        new_settings[idx]["weight"] = weight
    
    st.session_state.value_settings = new_settings

    st.markdown("---")
    st.session_state.risk_tolerance = st.select_slider(
        "🛡️ 의사결정 성향 (안정성 vs 도전성)",
        options=["매우 보수적", "신중함", "균형 잡힌", "도전적", "매우 실험적"],
        value=st.session_state.risk_tolerance
    )

# 3. 사용자 입력 섹션 (선택지 입력)
topic = st.text_input("어떤 결정을 내리고 싶나요?", placeholder="예: 아이패드 구매 vs 맥북 구매")

st.markdown("### 📋 비교 선택지 입력")
option_data = []
for i in range(st.session_state.options_count):
    with st.expander(f"선택지 {i+1}", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            name = st.text_input("이름", key=f"opt_name_{i}", placeholder="예: 아이패드 프로")
        with c2:
            detail = st.text_input("기본 설명", key=f"opt_det_{i}", placeholder="예: 11인치, M4 모델, 150만원")
        
        c3, c4 = st.columns(2)
        with c3:
            pros = st.text_area("장점", key=f"opt_pros_{i}", placeholder="휴대성 최강, 필기감 우수", height=70)
        with c4:
            cons = st.text_area("단점", key=f"opt_cons_{i}", placeholder="가격 부담, 멀티태스킹의 한계", height=70)
        
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
            with st.spinner("설정하신 가치 기준에 따라 정밀 분석 중입니다..."):
                # 가치관 설정을 텍스트로 변환
                value_context = "\n".join([f"- {item['label']}: {item['weight']}/100 ({get_weight_description(item['weight'])})" for item in st.session_state.value_settings])
                
                options_str = "\n\n".join(valid_options)
                
                prompt = f"""
                [분석 주제]: {topic}
                
                [사용자 정의 가치관 및 가중치]:
                {value_context}
                - 의사결정 성향: {st.session_state.risk_tolerance}
                
                [비교 선택지]:
                {options_str}
                
                위 데이터를 바탕으로 심층 분석해줘:
                1. 사용자가 직접 정의한 각 가치 항목별로 선택지들을 대조 분석해줘.
                2. 점수가 높은(80 이상) 가치 항목에 대해서는 더 엄격한 잣대를 적용해줘.
                3. 사용자의 성향({st.session_state.risk_tolerance})에 가장 잘 어울리는 '추천 선택지'를 선정해줘.
                4. 결과는 Markdown 표와 시각적 리스트를 활용해 가독성 있게 작성해줘.
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}]
                )
                
                st.markdown("---")
                st.success("✅ 분석 완료! 당신을 위한 최적의 제안입니다.")
                st.markdown(response.choices[0].message.content)
                
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
