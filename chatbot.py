import streamlit as st

def build_context_block():
    ctx = st.session_state
    lines = ["You are a patient, direct DSA tutor helping a student who is confused mid-task."]
    lines.append(f"Current tab: {ctx.get('active_tab', 'Unknown')}")
    lines.append(f"Topic: {ctx.get('learn_topic') or ctx.get('selected_topic', 'Unknown')}")
    lines.append(f"Concept: {ctx.get('learn_concept', 'Unknown')}")
    lines.append(f"Language: {ctx.get('language', 'Python')}")

    tab = ctx.get("active_tab", "")
    if tab == "Learn Mode":
        stage = ctx.get("learn_stage", 1)
        stage_names = {1: "UNDERSTAND IT", 2: "VISUALIZE IT (trace table)",
                       3: "PSEUDOCODE (fill blanks)", 4: "CODE IT",
                       5: "FEYNMAN CHECK", 6: "RECALL QUIZ"}
        lines.append(f"Stage: {stage} — {stage_names.get(stage, '')}")
        if stage == 2 and ctx.get("current_trace"):
            lines.append(f"Trace table on screen:\n{ctx['current_trace']}")
            lines.append(f"Question asked to student: {ctx.get('trace_question', '')}")
        if stage == 3 and ctx.get("current_pseudocode"):
            lines.append(f"Pseudocode with blanks:\n{ctx['current_pseudocode']}")
        if stage == 6 and ctx.get("current_quiz_question"):
            lines.append(f"Current quiz question: {ctx['current_quiz_question']}")
    elif tab in ["Practice", "Story / Case"]:
        if ctx.get("problem"):
            lines.append(f"Problem on screen:\n{ctx['problem']}")
        if ctx.get("solution") and ctx.get("solution_shown"):
            lines.append(f"Solution shown:\n{ctx['solution']}")
        if ctx.get("user_code"):
            lines.append(f"User's current code:\n{ctx['user_code']}")
        if ctx.get("last_run_result"):
            r = ctx["last_run_result"]
            lines.append(f"Last run: {'✅ Success' if r['success'] else '❌ ' + r.get('error_type','')}")
            if not r["success"]:
                lines.append(f"Error: {r['clean_error']}")

    lines += ["", "Rules:",
              "- Keep answers to 4–6 lines max. Student is mid-task.",
              "- If asked about a trace table row, explain that exact row using the table above.",
              "- If asked about a code error, reference the exact error message shown above.",
              "- NEVER reveal the full solution in Practice Mode unless solution_shown is True.",
              "- Use real-world analogies before technical terms for conceptual questions.",
              "- Tone: calm senior engineer helping a junior. Direct, no fluff."]
    return "\n".join(lines)


def get_quick_questions():
    ctx = st.session_state
    tab = ctx.get("active_tab", "")
    stage = ctx.get("learn_stage", 1)

    if tab == "Learn Mode":
        buttons = {
            1: ["Explain this more simply", "Give a different analogy",
                "When would I use this?", "How does this differ from brute force?"],
            2: ["What does 'row' mean here?", "Explain each column",
                "Walk me through row 1", "Why did this value change?"],
            3: ["What goes in the blank?", "Explain this pseudocode line",
                "Why is this step needed?", "What happens if I skip this step?"],
            4: ["Explain this line of code", "Why is this line critical?",
                "What's the most common mistake?", "How do I remember this?"],
            5: ["Am I on the right track?", "What key idea am I missing?"],
            6: ["Why is this answer wrong?", "Explain the correct answer",
                "What's the complexity and why?"]
        }
        return buttons.get(stage, ["I'm confused", "Explain this"])
    elif tab in ["Practice", "Story / Case"]:
        if not ctx.get("solution_shown"):
            return ["I don't understand the problem", "Give me a simpler example",
                    "What should I think about first?", "Help me understand my error"]
        else:
            return ["Explain the solution", "Why is brute force worse?",
                    "How do I remember this?", "What's a variation of this?"]
    return ["I'm confused", "Explain this to me"]


def call_chatbot_llm(user_message: str, api_key: str) -> str:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        system_prompt = build_context_block()
        messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.get("chat_history", [])[:-1]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": user_message})
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            max_tokens=300,
            temperature=0.5
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Tutor unavailable: {str(e)}"


def _send_message(user_message: str):
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        st.session_state["chat_history"].append({
            "role": "assistant",
            "content": "⚠️ Please add your Groq API key in the sidebar."
        })
        return
    st.session_state["chat_history"].append({"role": "user", "content": user_message})
    with st.spinner("Thinking..."):
        reply = call_chatbot_llm(user_message, api_key)
    st.session_state["chat_history"].append({"role": "assistant", "content": reply})


def render_chatbot_panel():
    st.markdown("### 🤖 DSA Tutor")
    topic = st.session_state.get("learn_topic") or st.session_state.get("selected_topic", "")
    stage = st.session_state.get("learn_stage", "")
    tab = st.session_state.get("active_tab", "")
    if topic:
        badge = f"📍 {topic}"
        if tab == "Learn Mode" and stage:
            badge += f" | Stage {stage}/6"
        st.caption(badge)

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    with st.container(height=260):
        for msg in st.session_state["chat_history"][-6:]:
            if msg["role"] == "user":
                st.markdown(
                    f"<div style='text-align:right;background:#1e3a5f;padding:8px 12px;"
                    f"border-radius:12px;margin:4px 0;font-size:0.84em'>{msg['content']}</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='text-align:left;background:#2a2a2a;padding:8px 12px;"
                    f"border-radius:12px;margin:4px 0;font-size:0.84em'>{msg['content']}</div>",
                    unsafe_allow_html=True)

    st.markdown("**Quick questions:**")
    for q in get_quick_questions():
        if st.button(q, key=f"qq_{q[:25]}_{tab}", use_container_width=True):
            _send_message(q)
            st.rerun()

    st.markdown("---")
    user_input = st.text_input("Ask anything:", key=f"chat_input_{tab}",
                               placeholder="e.g. what does row 3 mean?",
                               label_visibility="collapsed")
    if st.button("Send ➤", use_container_width=True, key=f"chat_send_{tab}"):
        if user_input.strip():
            _send_message(user_input.strip())
            st.rerun()

    if st.session_state.get("chat_history"):
        if st.button("🗑 Clear chat", use_container_width=True, key=f"chat_clear_{tab}"):
            st.session_state["chat_history"] = []
            st.rerun()
