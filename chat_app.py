import gradio as gr
import httpx
import uuid
import asyncio

BASE_API_URL = "https://wellys-chat-service.onrender.com"

# JavaScript code remains unchanged.
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

async def get_history(session_id):
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_API_URL}/history", json={"session_id": session_id}, timeout=10)
        response.raise_for_status()
        return response.json().get("message", [])

# --- All user-facing strings are now in English ---
async def respond_for_ui(message, chat_history, session_id):
    if not session_id:
        chat_history.append({'role': 'user', 'content': message})
        chat_history.append({'role': 'assistant', 'content': "Session not started. Please refresh the page."})
        yield "", chat_history
        return

    if not message.strip():
        yield "", chat_history
        return

    chat_history.append({'role': 'user', 'content': message})
    yield "", chat_history

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{BASE_API_URL}/chat", json={"session_id": session_id, "content": message}, timeout=20)
            
            updated_history = await get_history(session_id)
            
            yield "", updated_history

    except Exception as e:
        print(f"Error in respond_for_ui: {e}")
        chat_history.append({'role': 'assistant', 'content': f"An error occurred: {e}"})
        yield "", chat_history


async def auto_start_session_async():
    session_id = str(uuid.uuid4())
    print(f"Session started automatically: {session_id}")
    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{BASE_API_URL}/start", json={"session_id": session_id, "user_name": "Guest"}, timeout=10)
        return session_id
    except Exception as e:
        print(f"Error starting session automatically: {e}")
        return None

# --- All user-facing strings are now in English ---
async def end_session_async(session_id):
    final_message = "Session has ended. Please refresh the page to start a new one."
    final_message_for_chatbot = [{'role': 'assistant', 'content': final_message}]

    if not session_id:
        return None, final_message_for_chatbot, gr.update(interactive=False, placeholder="Session Ended"), gr.update(interactive=False)

    try:
        async with httpx.AsyncClient() as client:
            await client.post(f"{BASE_API_URL}/end", json={"session_id": session_id}, timeout=10)
        print(f"Session ended manually: {session_id}")
        return None, final_message_for_chatbot, gr.update(interactive=False, placeholder="Session Ended"), gr.update(interactive=False)
    except Exception as e:
        print(f"Error ending session: {e}")
        return session_id, gr.update(), gr.update(), gr.update()

# --- UI strings are now in English ---
with gr.Blocks(theme=gr.themes.Soft(), css="footer {display: none !important}") as chat_demo:
    session_id_state = gr.State(value=None)
    
    gr.Markdown("# Wellys Chat Service")
    
    chatbot = gr.Chatbot(label="Wellys", height=500, type="messages")
    with gr.Row():
        msg_textbox = gr.Textbox(
            show_label=False,
            placeholder="Type a message",
            scale=7,
        )
        send_btn = gr.Button("Send", scale=1)

    end_btn = gr.Button("End Session")

    chat_demo.load(
        auto_start_session_async,
        outputs=[session_id_state]
    )

    submit_args = {
        'fn': respond_for_ui,
        'inputs': [msg_textbox, chatbot, session_id_state],
        'outputs': [msg_textbox, chatbot]
    }
    send_btn.click(**submit_args)
    msg_textbox.submit(**submit_args)

    end_btn.click(
        fn=end_session_async,
        inputs=[session_id_state],
        outputs=[session_id_state, chatbot, msg_textbox, send_btn] 
    )

if __name__ == "__main__":
    chat_demo.launch(server_port=7861, server_name="0.0.0.0")