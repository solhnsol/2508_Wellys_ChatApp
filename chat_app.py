import gradio as gr
import requests
from requests import HTTPError

BASE_API_URL = "https://wellys-chat-service.onrender.com"

def history(session_id):
    try:
        response = requests.post(f"{BASE_API_URL}/history", json={"session_id": session_id})
        response.raise_for_status()
        return response.json()["message"]
    except HTTPError as e:
        print(f"오류: {e}")

def start(user_name):
    try:
        response = requests.post(f"{BASE_API_URL}/start", json={"user_name": user_name})
        response.raise_for_status()
        print(f"세션이 정상적으로 생성되었습니다.")
        return response.json()["session_id"]
    except HTTPError as e:
        print(f"오류: {e}")
        return "세션 생성에 실패했습니다."

def chat(session_id, text):
    try:
        response = requests.post(f"{BASE_API_URL}/chat", json={"session_id": session_id, "content": text})
        response.raise_for_status()
        message = response.json()["message"]

        chat_history = history(session_id)
        if chat_history is None:
                return "챗봇 응답을 가져오는 데 실패했습니다."
        return chat_history
        
    except HTTPError as e:
        print(f"오류: {e}")
        # 오류 발생 시 사용자에게 보여줄 메시지를 반환합니다.
        return f"챗봇 서버에서 오류가 발생했습니다: {e}"

def end(session_id):
    try:
        response = requests.post(f"{BASE_API_URL}/end", json={"session_id": session_id})
        response.raise_for_status()
        return response.json()["message"]
    except HTTPError as e:
        print(f"오류: {e}")

with gr.Blocks(theme="soft") as demo:
    session_id_state = gr.State()

    gr.Markdown(
        """
        # Wellys AI 채팅 서비스
        당신의 건강을 책임지는 Wellys 입니다.
        """
    )

    chatbot = gr.Chatbot(
        [],
        elem_id="chatbot",
        height=460,
        type="messages"
    )

    with gr.Row():
        txt = gr.Textbox(
            show_label=False,
            placeholder="Wellys 에게 물어보세요..",
            container=False,
            scale=7,
        )
        submit_btn = gr.Button("전송", scale=1)

    gr.Examples(
        [["요즘 허리가 아픈데, 갱년기 증상일까?"], ["여성 건강에 좋은 음식을 알고 싶어."], ["갱년기 건강 관리 방법 알려줘"]],
        inputs=txt
    )

    # 챗봇 응답을 처리하는 함수
    def add_message(history, message):
        # 사용자 메시지를 먼저 화면에 표시
        return history + [{"role" : "user", "content": message}]

    # 사용자가 메시지를 입력하고 '전송' 버튼을 누르거나 엔터를 쳤을 때 실행될 함수
    def bot_response(history, session_id):
        user_message = history[-1]["content"]
        new_history = chat(session_id, user_message)

        return new_history, None

    txt.submit(add_message, [chatbot, txt], [chatbot], queue=False).then(
        bot_response, [chatbot, session_id_state], [chatbot, txt]
    )
    submit_btn.click(add_message, [chatbot, txt], [chatbot], queue=False).then(
        bot_response, [chatbot, session_id_state], [chatbot, txt]
    )

    # UI가 처음 로드될 때 실행되는 함수
    def start_session():
        user_name = "홍길순"
        new_session_id = start(user_name)
        return new_session_id

    demo.load(start_session, inputs=None, outputs=[session_id_state])


if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7861, share=True)