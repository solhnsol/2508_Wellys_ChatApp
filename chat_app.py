import gradio as gr
import httpx # requests 대신 httpx 임포트
import uuid
import asyncio # 비동기 함수를 위한 asyncio 임포트

BASE_API_URL = "https://wellys-chat-service.onrender.com"
# BASE_API_URL = "http://127.0.0.1:8000"

async def get_history_async(session_id):
    history_endpoint = f"{BASE_API_URL}/history"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                history_endpoint,
                json={"session_id": session_id},
                timeout=10
            )
            response.raise_for_status()
            history_data = response.json().get("message", [])
            return history_data
    except Exception as e:
        print(f"Error fetching history: {e}")
        return []

async def respond_async(message, chat_history, session_id):
    if not message.strip():
        yield "", chat_history, gr.update(interactive=True)
        return

    # 1. 사용자 메시지와 "생각 중" placeholder를 함께 추가
    chat_history.append({"role": "user", "content": message})
    chat_history.append({"role": "assistant", "content": "Thinking..."})
    # 2. UI 즉시 업데이트 (입력창 비우기, 챗봇 업데이트, 전송 버튼 비활성화)
    yield "", chat_history, gr.update(interactive=False)

    chat_endpoint = f"{BASE_API_URL}/chat"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                chat_endpoint,
                json={"session_id": session_id, "content": message},
                timeout=20
            )
            response.raise_for_status()
        
        # 3. 최종 응답으로 챗봇 전체 업데이트
        # 비동기 함수 호출 시 await 추가
        updated_history = await get_history_async(session_id) 
        yield "", updated_history, gr.update(interactive=True)

    except Exception as e:
        print(f"Error sending message: {e}")
        # 에러 발생 시, 마지막 "생각 중" 메시지를 에러 메시지로 교체
        chat_history[-1] = {"role": "assistant", "content": f"**Error:** {e}"}
        yield "", chat_history, gr.update(interactive=True)

async def start_session_async(user_name_input):
    session_id = str(uuid.uuid4())
    start_endpoint = f"{BASE_API_URL}/start"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                start_endpoint,
                json={"session_id": session_id, "user_name": user_name_input},
                timeout=10
            )
            response.raise_for_status()
        print(f"Session started: {session_id} for user {user_name_input}")
        return session_id, [], gr.update(interactive=True), gr.update(value=f"Session ID: {session_id[:5]}.. - Welcome, {user_name_input}!")
    except Exception as e:
        print(f"Error starting session: {e}")
        return None, [], gr.update(interactive=False), gr.update(value=f"Failed to start session: {e}")

async def end_session_async(session_id):
    if not session_id:
        return None, [], gr.update(interactive=False), gr.update(value="There is no session online.")

    end_endpoint = f"{BASE_API_URL}/end"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                end_endpoint,
                json={"session_id": session_id},
                timeout=10
            )
            response.raise_for_status()
        print(f"Session ended: {session_id}")
        return None, [], gr.update(interactive=False), gr.update(value="Session ended. Please create a new session.")
    except Exception as e:
        print(f"Error ending session: {e}")
        # 비동기 함수 호출 시 await 추가
        return session_id, await get_history_async(session_id), gr.update(interactive=True), gr.update(value=f"Failed to close session: {e}")

with gr.Blocks(theme=gr.themes.Soft()) as chat_demo:
    session_id_state = gr.State(value=None)
    
    gr.Markdown("# Wellys Chat Service")

    with gr.Row():
        user_name_input = gr.Textbox(label="Name", value="", scale=3)
        start_btn = gr.Button("Create Session", scale=1)
        end_btn = gr.Button("End Session", scale=1)

    session_status_output = gr.Textbox(label="Session Status", interactive=False)

    chatbot = gr.Chatbot(label="Chat History", type="messages", height=500)
    
    with gr.Row():
        msg = gr.Textbox(
            label="Enter message",
            interactive=False,
            container=False,
            show_label=False,
            placeholder="Type a message and press Enter key",
            scale=8,
        )
        send_btn = gr.Button("Enter", scale=1) 

    # .click() 메서드에 비동기 함수를 직접 전달합니다. Gradio가 비동기 함수를 자동으로 처리합니다.
    start_btn.click(
        start_session_async,
        inputs=[user_name_input],
        outputs=[session_id_state, chatbot, msg, session_status_output]
    )

    msg.submit(
        respond_async,
        inputs=[msg, chatbot, session_id_state],
        outputs=[msg, chatbot, send_btn]
    )

    send_btn.click(
        respond_async,
        inputs=[msg, chatbot, session_id_state],
        outputs=[msg, chatbot, send_btn]
    )

    end_btn.click(
        end_session_async,
        inputs=[session_id_state],
        outputs=[session_id_state, chatbot, msg, session_status_output]
    )

if __name__ == "__main__":
    chat_demo.launch(server_port=7861, server_name="0.0.0.0")