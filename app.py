import streamlit as st
import os
import requests
from google import genai
from google.genai import types

# 1. 페이지 설정
st.set_page_config(page_title="나만의 Gemini 에이전트", layout="centered")
st.title("🤖 나만의 Gemini API 에이전트")
st.caption("외부 API와 Gemini를 연결하는 나만의 대화창입니다.")

# 2. 보안 키 설정 (Streamlit Secrets 또는 환경변수에서 불러오기)
# Streamlit Cloud 배포 시 설정 메뉴에서 키를 입력하면 안전하게 불러옵니다.
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", os.environ.get("GEMINI_API_KEY", ""))
EXTERNAL_API_KEY = st.secrets.get("EXTERNAL_API_KEY", os.environ.get("EXTERNAL_API_KEY", ""))
EXTERNAL_API_URL = st.secrets.get("EXTERNAL_API_URL", os.environ.get("EXTERNAL_API_URL", "https://api.example.com/data"))

# 3. 외부 API 호출 함수 정의
def call_external_api(query_param=""):
    try:
        # API 공급자의 양식에 맞게 URL과 헤더, 파라미터를 수정해야 합니다.
        headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
        params = {"query": query_param}
        
        response = requests.get(EXTERNAL_API_URL, headers=headers, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API 호출 실패 (상태코드: {response.status_code})"}
    except Exception as e:
        return {"error": str(e)}

# 4. 세션 상태(대화 기록) 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 기록 표시
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 5. 사용자 입력창
if user_input := st.chat_input("Gemini에게 명령을 입력하세요..."):
    # 유저 메시지 표시 및 저장
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # AI 응답 생성
    with st.chat_message("assistant"):
        if not GEMINI_API_KEY:
            st.error("Gemini API 키가 설정되지 않았습니다. 관리자 설정을 확인해주세요.")
        else:
            with st.spinner("생각 중..."):
                try:
                    # 외부 API로부터 먼저 데이터를 수집 (예시 파라미터로 유저 입력 전달)
                    api_data = call_external_api(query_param=user_input)
                    
                    # Gemini 클라이언트 초기화
                    client = genai.Client(api_key=GEMINI_API_KEY)
                    
                    # 프롬프트 조립: 외부 API 데이터와 유저의 질문을 결합
                    system_prompt = f"당신은 유저를 돕는 AI 에이전트입니다. 외부 API로부터 가져온 다음 데이터를 참고하여 유저의 질문에 친절하게 답변해주세요.\n\n[외부 API 데이터]:\n{api_data}"
                    
                    # 대화 기록 포맷 변환
                    contents = []
                    for msg in st.session_state.messages[:-1]: # 마지막 입력 제외한 이전 대화
                        contents.append(f"{msg['role']}: {msg['content']}")
                    contents.append(f"user: {user_input}")
                    
                    # Gemini 호출 (gemini-2.5-flash 활용)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=contents,
                        config=types.GenerateContentConfig(
                            system_instruction=system_prompt
                        )
                    )
                    
                    # 응답 출력 및 저장
                    ai_response = response.text
                    st.markdown(ai_response)
                    st.session_state.messages.append({"role": "assistant", "content": ai_response})
                    
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {e}")
