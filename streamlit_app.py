  import streamlit as st
  from openai import OpenAI

  SYSTEM_PROMPT = """당신은 10년 경력의 스포츠 용품 전문 상담사입니다.
  - 사용자가 어떤 운동을 하는지, 실력 수준(입문/중급/상급), 예산, 사용 목적(취미/시합용)을
  파악하기 전까지는 섣불리 특정 제품을 추천하지 말고 먼저 되물어보세요.
  - 정보가 충분해지면 카테고리(브랜드보다는 종류·스펙 중심)와 이유를 함께 제안하세요.
  - 가격대는 여러 옵션(가성비/중급/프리미엄)으로 나눠 설명하세요.
  - 모르는 최신 가격·재고는 추측하지 말고, 매장/공식몰 확인을 권하세요.
  - 친절하고 간결한 한국어로 답하세요."""

  st.title("스포츠 용품 상담 챗봇")
  st.write(
      "운동 종목, 실력, 예산을 알려주시면 어떤 스포츠 용품이 맞을지 상담해드려요. "
      "이용하려면 OpenAI API 키가 필요합니다."
  )

  openai_api_key = st.text_input("OpenAI API Key", type="password")
  if not openai_api_key:
      st.info("Please add your OpenAI API key to continue.", icon="key")
  else:
      client = OpenAI(api_key=openai_api_key)

      if "messages" not in st.session_state:
          st.session_state.messages = []

      for message in st.session_state.messages:
          with st.chat_message(message["role"]):
              st.markdown(message["content"])

      if prompt := st.chat_input("어떤 운동 용품을 찾으세요? (예: 초보 러닝화 추천해줘)"):
          st.session_state.messages.append({"role": "user", "content": prompt})
      st.info("Please add your OpenAI API key to continue.", icon="key")
  else:
      client = OpenAI(api_key=openai_api_key)

      if "messages" not in st.session_state:
          st.session_state.messages = []

      for message in st.session_state.messages:
          with st.chat_message(message["role"]):
              st.markdown(message["content"])

      if prompt := st.chat_input("어떤 운동 용품을 찾으세요? (예: 초보 러닝화 추천해줘)"):
          st.session_state.messages.append({"role": "user", "content": prompt})
          with st.chat_message("user"):
              st.markdown(prompt)

          api_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + [
              {"role": m["role"], "content": m["content"]}
              for m in st.session_state.messages
          ]

          stream = client.chat.completions.create(
              model="gpt-3.5-turbo",
              messages=api_messages,
              stream=True,
          )

          with st.chat_message("assistant"):
              response = st.write_stream(stream)
          st.session_state.messages.append({"role": "assistant", "content": response})
