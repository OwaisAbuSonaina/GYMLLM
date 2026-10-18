import httpx
import gradio as gr
from client import GYMLLM_API_URL

# Backend FastAPI URL (configurable via env var for Docker Compose)

# Client-side JavaScript to toggle Dark/Light mode reliably
TOGGLE_THEME_JS = """
function() {
    document.body.classList.toggle('dark');
    document.documentElement.classList.toggle('dark');
    const isDark = document.body.classList.contains('dark') || document.documentElement.classList.contains('dark');
    return isDark ? "☀️ Light Mode" : "🌙 Dark Mode";
}
"""

CUSTOM_CSS = """
/* Dashboard container polish */
.gradio-container {
    max-width: 950px !important;
    margin: 0 auto !important;
    padding-top: 1.5rem !important;
}

/* Header badge styling */
.badge {
    display: inline-block;
    padding: 0.25rem 0.6rem;
    font-size: 0.75rem;
    font-weight: 600;
    border-radius: 9999px;
    background-color: #34d399; /* Light green */
    color: #111827;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.5rem;
}

/* Chat bubble typography */
.message {
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
}
"""


async def stream_chat(message: str, history: list):
    """
    Streams responses from the FastAPI /GYMLLM endpoint into the Gradio UI.
    """
    if not message.strip():
        return

    # Format history to match FastAPI HRRequest schema: List[Dict[str, str]]
    # Handles both dict format (messages) and tuple format across Gradio versions
    formatted_history = []
    for turn in history:
        if isinstance(turn, dict):
            formatted_history.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})
        elif isinstance(turn, (list, tuple)) and len(turn) == 2:
            u_msg, a_msg = turn
            if u_msg:
                formatted_history.append({"role": "user", "content": str(u_msg)})
            if a_msg:
                formatted_history.append({"role": "assistant", "content": str(a_msg)})

    payload = {
        "hr_question": message,
        "history": formatted_history
    }

    bot_reply = ""
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", GYMLLM_API_URL, json=payload) as response:
                if response.status_code != 200:
                    yield f"⚠️ API Error ({response.status_code}): Unable to process query."
                    return

                async for chunk in response.aiter_text():
                    bot_reply += chunk
                    yield bot_reply

    except httpx.ConnectError:
        yield "❌ Connection Error: Could not connect to the FastAPI backend. Ensure `app.py` is running on port 8000."
    except Exception as err:
        yield f"❌ System Error: {str(err)}"


# Theme setup - Updated to emerald (light green)
theme = gr.themes.Soft(
    primary_hue="emerald",
    secondary_hue="zinc",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "sans-serif"]
)

with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="The Yard | HQ HR Assistant") as demo:
    with gr.Row(elem_id="header-bar"):
        with gr.Column(scale=8):
            gr.HTML(
                """
                <div>
                    <span class="badge">The Yard HQ</span>
                    <h2 style="margin: 0; font-weight: 700;">GYMLLM</h2>
                </div>
                """
            )
        with gr.Column(scale=2, min_width=130):
            theme_btn = gr.Button("🌙 Dark Mode", size="sm", variant="secondary")

    # Interactive Chat Window
    chatbot = gr.Chatbot(
        height=520,
        show_copy_button=True,
        placeholder="💡 Ask any question regarding HR policies, payroll timelines, disciplinary steps, or branch operations...",
        type="messages"
    )

    with gr.Row():
        msg_input = gr.Textbox(
            placeholder="Type your HR compliance question here (e.g., notice requirements, credential checks)...",
            show_label=False,
            scale=9,
            container=False,
            autofocus=True
        )
        send_btn = gr.Button("Send", variant="primary", scale=1)

    with gr.Row():
        clear_btn = gr.Button("🗑️ Clear Conversation", size="sm", variant="subdued")

    # Fast-access example prompts for HQ HR workflows
    gr.Examples(
        examples=[
            "Describe the maximum permitted workweek and daily working hours for operational staff",
            "Who is the current branch manager of Khalda branch?",
            "Summarize the Termination Protocol of The Yard."
        ],
        inputs=msg_input,
        label="Quick Inquiries"
    )

    # Event handlers
    def submit_user_msg(user_msg, chat_history):
        chat_history = chat_history or []
        chat_history.append({"role": "user", "content": user_msg})
        return "", chat_history

    async def generate_response(chat_history):
        user_message = chat_history[-1]["content"]
        # History excluding the active message
        prior_history = chat_history[:-1]
        
        chat_history.append({"role": "assistant", "content": ""})
        async for token_text in stream_chat(user_message, prior_history):
            chat_history[-1]["content"] = token_text
            yield chat_history

    # Send button & enter key triggers
    msg_input.submit(
        submit_user_msg,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot],
        queue=False
    ).then(
        generate_response,
        inputs=[chatbot],
        outputs=[chatbot]
    )

    send_btn.click(
        submit_user_msg,
        inputs=[msg_input, chatbot],
        outputs=[msg_input, chatbot],
        queue=False
    ).then(
        generate_response,
        inputs=[chatbot],
        outputs=[chatbot]
    )

    clear_btn.click(lambda: [], None, chatbot, queue=False)
    theme_btn.click(fn=None, js=TOGGLE_THEME_JS, outputs=theme_btn)


if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, inbrowser=True)
