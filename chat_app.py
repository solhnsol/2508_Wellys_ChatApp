import gradio as gr
import httpx
import uuid
import asyncio

BASE_API_URL = "https://wellys-chat-service.onrender.com"

js_script = f"""
function(session_id) {{
    if (window.unloadListener) {{
        window.removeEventListener('beforeunload', window.unloadListener);
    }}
    window.unloadListener = () => {{
        if (session_id) {{
            const url = `{BASE_API_URL}/end`;
            const data = new Blob([JSON.stringify({{ "session_id": session_id }})], {{ type: 'application/json' }});
            navigator.sendBeacon(url, data);
        }}
    }};
    window.addEventListener('beforeunload', window.unloadListener);
    return null;
}}
"""

# ChatInterface에 연결할 응답 함수를 새로 정의합니다.
# 이 함수는 'message'와 'history'를 받아 '답변 메시지(문자열)'만 반환하면 됩니다.
async def respond_for_interface(message, history, session_id):
    if not session_id:
        return "Session not started. Please refresh the page."
    if not message.strip():
        return "Please enter a message."

    chat_endpoint = f"{BASE_API_URL}/chat"
    try:
        async with httpx.AsyncClient() as client:
            # 백엔드에 메시지 전송
            await client.post(
                chat_endpoint,
                json={"session_id": session_id, "content": message},
                timeout=20
            )
            # 최신 대화 기록을 가져옴
            history_endpoint = f"{BASE_API_URL}/history"
            response = await client.post(
                history_endpoint,
                json={"session_id": session_id},
                timeout=10
            )
            response.raise_for_status()
            updated_history = response.json().get("message", [])
            
            # 마지막 응답(assistant의 답변)을 찾아 반환
            if updated_history and updated_history[-1]["role"] == "assistant":
                return updated_history[-1]["content"]
            else:
                return "Sorry, I couldn't get a response."

    except Exception as e:
        print(f"Error in respond_for_interface: {e}")
        return f"**Error:** {e}"

async def auto_start_session_async():
    session_id = str(uuid.uuid4())
    user_name = "Guest"
    start_endpoint = f"{BASE_API_URL}/start"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                start_endpoint,
                json={"session_id": session_id, "user_name": user_name},
                timeout=10
            )
        print(f"Session started automatically: {session_id} for user {user_name}")
        # ChatInterface를 위한 출력은 이제 필요 없으므로, 세션 ID와 JS 실행을 위한 ID만 반환
        return session_id, session_id
    except Exception as e:
        print(f"Error starting session automatically: {e}")
        return None, None

async def end_session_async(session_id):
    if not session_id:
        # ChatInterface를 초기화하고, 비활성화된 메시지를 표시
        return None, None, [[None, "Session not started. Please refresh the page."]]

    end_endpoint = f"{BASE_API_URL}/end"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(end_endpoint, json={"session_id": session_id}, timeout=10)
        print(f"Session ended manually: {session_id}")
        # 세션 종료 후, ChatInterface를 초기화하고 종료 메시지를 표시
        return None, None, [[None, "Session ended. Please refresh the page."]]
    except Exception as e:
        print(f"Error ending session: {e}")
        # 에러 발생 시 현재 상태 유지
        return session_id, session_id, gr.update()


# --- UI 구성 (ChatInterface 사용) ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as chat_demo:
    session_id_state = gr.State(value=None)
    session_id_for_js = gr.Textbox(visible=False)
    
    gr.Markdown("# Wellys Chat Service")
    
    # ChatInterface 컴포넌트 선언
    chat_interface = gr.ChatInterface(
        fn=respond_for_interface, # 핵심 로직 함수 연결
        additional_inputs=[session_id_state], # 숨겨진 입력으로 세션 ID 전달
        title=None, # 상단 타이틀 제거
        chatbot=gr.Chatbot(label="Wellys", height=600),
    )

    # 세션 종료 버튼을 ChatInterface 위에 별도로 배치
    end_btn = gr.Button("End Session")

    # --- 이벤트 핸들러 ---
    chat_demo.load(
        auto_start_session_async,
        outputs=[session_id_state, session_id_for_js]
    )
    
    session_id_for_js.change(None, inputs=[session_id_for_js], js=js_script)

    end_btn.click(
        end_session_async,
        inputs=[session_id_state],
        # 종료 시 세션ID, JS용ID, 그리고 ChatInterface 자체를 초기화
        outputs=[session_id_state, session_id_for_js, chat_interface.chatbot]
    )

if __name__ == "__main__":
    chat_demo.launch(server_port=7861)