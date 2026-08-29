import re

import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="스포츠 용품 상담 챗봇", page_icon="🏸", layout="centered")

st.title("🏸 스포츠 용품 상담 챗봇")
st.write(
    "운동 종목, 실력, 예산을 알려주시면 어떤 스포츠 용품이 맞을지 상담해드려요. "
    "음성으로 물어보셔도 되고, 상담 결과는 카카오톡으로 공유할 수 있어요."
)

# --------------------------------------------------
# API KEY
# --------------------------------------------------

openai_api_key = st.text_input("OpenAI API Key", type="password")
if not openai_api_key:
    st.info("Please add your OpenAI API key to continue.", icon="🗝️")
    st.stop()

client = OpenAI(api_key=openai_api_key)

# --------------------------------------------------
# 상담 설정 (사이드바)
# --------------------------------------------------

st.sidebar.header("🏸 상담 설정")

sport = st.sidebar.selectbox(
    "운동 종목",
    ["러닝", "헬스/웨이트", "등산/트레킹", "축구/풋살", "농구", "배드민턴/테니스", "수영", "자전거", "골프", "기타"],
)
level = st.sidebar.selectbox("실력 수준", ["입문", "중급", "상급"])
budget = st.sidebar.select_slider(
    "예산대", options=["가성비", "중급", "프리미엄", "상관없음"], value="상관없음"
)

st.sidebar.divider()
app_url = st.sidebar.text_input(
    "이 앱의 배포 URL",
    value="https://chatbot-sd-2608.streamlit.app/",
    help="카카오톡 공유용 텍스트에 포함될 링크입니다.",
)

# --------------------------------------------------
# AI 역할 설정
# --------------------------------------------------

SYSTEM_PROMPT = f"""당신은 10년 경력의 스포츠 용품 전문 상담사입니다.

사용자가 미리 알려준 정보:
- 운동 종목: {sport}
- 실력 수준: {level}
- 예산대: {budget}

상담 원칙:
1. 위 정보로 충분하지 않으면(사용 목적, 신체조건, 선호 브랜드 등) 가장 중요한 질문 1~2개만 먼저 하세요.
2. 정보가 충분해지면 브랜드보다는 종류·스펙 중심으로 카테고리를 추천하고, 이유를 함께 설명하세요.
3. 가격대는 가성비/중급/프리미엄 등 여러 옵션으로 나눠 설명하세요.
4. 모르는 최신 가격·재고·단종 여부는 추측하지 말고, 매장/공식몰 확인을 권하세요.
5. 답변은 친절하고 간결한 한국어로, 가능하면 아래 형식을 사용하세요.

### 🔍 파악된 니즈
### 💡 추천 카테고리
### ⚠️ 확인할 점
### 🎯 정리
"""

# --------------------------------------------------
# 대화 기록
# --------------------------------------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------------------------
# 카카오톡 공유 버튼 렌더링 함수
# --------------------------------------------------


def render_kakao_share(text: str, key: str):
    # 카카오 JS SDK는 Streamlit이 이 버튼을 iframe(srcdoc)으로 렌더링하는 과정에서
    # 출처(origin)가 없어져 도메인 인증이 항상 실패한다. 대신 복사해서
    # 카카오톡에 붙여넣는 방식으로 공유한다.
    clean_text = re.sub(r"[#*`]", "", text).strip()
    share_message = f"{clean_text[:500]}\n\n📱 더 보기: {app_url}"
    with st.expander("💬 카카오톡으로 공유하기"):
        st.caption("아래 내용을 복사해서 카카오톡 채팅방에 붙여넣으세요.")
        st.code(share_message, language=None)


# --------------------------------------------------
# 기존 대화 + 생성된 이미지 출력
# --------------------------------------------------

for i, message in enumerate(st.session_state.messages):
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            if message.get("image_url"):
                st.image(message["image_url"])
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🖼 추천 상품 이미지로 보기", key=f"img_btn_{i}"):
                    with st.spinner("이미지 생성 중..."):
                        # 마크다운 제목·이모지를 걷어내고 짧게 잘라서 안전한 이미지 프롬프트로 사용
                        clean_text = re.sub(r"[#*`>_🔍💡⚠️🎯]", "", message["content"])
                        clean_text = " ".join(clean_text.split())[:300]
                        image_prompt = f"스포츠 용품 매장 진열 사진, 다음 추천 내용에 어울리는 실제 제품들: {clean_text}"
                        try:
                            image = client.images.generate(
                                model="dall-e-3",
                                prompt=image_prompt,
                                size="1024x1024",
                                n=1,
                            )
                            st.session_state.messages[i]["image_url"] = image.data[0].url
                        except Exception as e:
                            st.error(f"이미지를 생성하지 못했어요: {e}")
                    st.rerun()
            with col2:
                render_kakao_share(message["content"], key=str(i))

# --------------------------------------------------
# 음성 입력 (선택)
# --------------------------------------------------

st.divider()
audio_value = st.audio_input("🎙 음성으로 질문하기 (선택)")

voice_prompt = None
if audio_value is not None:
    with st.spinner("음성 인식 중..."):
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_value,
        )
        voice_prompt = transcript.text
    st.caption(f"인식된 질문: {voice_prompt}")

# --------------------------------------------------
# 텍스트 입력
# --------------------------------------------------

text_prompt = st.chat_input("어떤 운동 용품을 찾으세요? (예: 초보 러닝화 추천해줘)")

prompt = voice_prompt or text_prompt

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=api_messages,
        stream=True,
    )

    with st.chat_message("assistant"):
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
