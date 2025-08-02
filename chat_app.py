import gradio as gr
import requests
import uuid # session_id 생성을 위해 uuid 모듈 추가

BASE_API_URL = "https://wellys-chat-service.onrender.com"

def get_history(session_id):
    history_endpoint = f"{BASE_API_URL}/history"
    try:
        response = requests.post(
            history_endpoint,
            json={"session_id": session_id},
            timeout=10
        )
        response.raise_for_status()
        # API 응답에서 메시지 리스트를 파싱하여 Gradio 챗봇 형식으로 반환
        history_data = response.json().get("message", [])
        
        return history_data

    except Exception as e:
        print(f"Error fetching history: {e}")
        return [] # 오류 발생 시 빈 리스트 반환

def respond(message, session_id):
    chat_endpoint = f"{BASE_API_URL}/chat"
    try:
        response = requests.post(
            chat_endpoint,
            json={"session_id": session_id, "content": message},
            timeout=10
        )
        response.raise_for_status()
        
        # 챗봇의 응답 내용을 파싱
        return "", get_history(session_id)

    except Exception as e:
        print(f"Error sending message: {e}")
        return "", get_history(session_id)

def start_session(user_name_input):
    # 새로운 세션 ID 생성
    session_id = str(uuid.uuid4())
    start_endpoint = f"{BASE_API_URL}/start"
    try:
        response = requests.post(
            start_endpoint,
            json={"session_id": session_id, "user_name": user_name_input},
            timeout=10
        )
        response.raise_for_status()
        print(f"Session started: {session_id} for user {user_name_input}")
        return session_id, get_history(session_id), gr.update(interactive=True), gr.update(interactive=True), gr.update(value=f"세션 ID: {session_id} - {user_name_input}님 환영합니다!") # 세션 ID와 빈 채팅 기록 반환
    except Exception as e:
        print(f"Error starting session: {e}")
        return '세션 시작 실패', get_history(session_id), gr.update(interactive=False), gr.update(interactive=False), gr.update(value=f"세션 시작 실패: {e}")

def end_session(session_id):
    end_endpoint = f"{BASE_API_URL}/end"
    try:
        response = requests.post(
            end_endpoint,
            json={"session_id": session_id},
            timeout=10
        )
        response.raise_for_status()
        print(f"Session ended: {session_id}")
        return '세션 종료됨', get_history(session_id), gr.update(interactive=False), gr.update(interactive=False), gr.update(value="세션이 종료되었습니다. 새 세션을 시작하세요.") # 세션 ID 초기화 및 채팅 기록 비우기
    except Exception as e:
        print(f"Error ending session: {e}")
        return '세션 종료 실패', get_history(session_id), gr.update(interactive=False), gr.update(interactive=False), gr.update(value=f"세션 종료 실패: {e}")

with gr.Blocks() as chat_demo:
    # 세션 ID를 저장할 상태 변수
    session_id_state = gr.State(value=None)
    
    gr.Markdown("# Wellys 채팅 서비스")

    with gr.Row():
        with gr.Column(scale=1):
            user_name_input = gr.Textbox(label="사용자 이름", value="정한솔") # 기본값 설정
            start_btn = gr.Button("새 세션 시작")
            end_btn = gr.Button("세션 종료")
            session_status_output = gr.Textbox(label="세션 상태", interactive=False)

        with gr.Column(scale=3):
            chatbot = gr.Chatbot(label="채팅 기록", type="messages")
            msg = gr.Textbox(label="메시지 입력", interactive=False) # 세션 시작 전에는 비활성화
            clear_btn = gr.Button("채팅 초기화")
    
    # 세션 시작 버튼 클릭 시
    start_btn.click(
        start_session,
        inputs=[user_name_input],
        outputs=[session_id_state, chatbot, msg, clear_btn, session_status_output]
    )

    # 메시지 전송 시
    msg.submit(
        respond,
        inputs=[msg, session_id_state], # chatbot을 inputs에 추가
        outputs=[msg, chatbot]
    )

    # 채팅 초기화 버튼 클릭 시 (현재 대화만 초기화)
    clear_btn.click(lambda: [], outputs=chatbot, queue=False)

    # 세션 종료 버튼 클릭 시
    end_btn.click(
        end_session,
        inputs=[session_id_state],
        outputs=[session_id_state, chatbot, msg, clear_btn, session_status_output]
    )


if __name__ == "__main__":
    chat_demo.launch(server_port=7861)