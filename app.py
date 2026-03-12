import streamlit as st
import time
from datetime import datetime

from utils import initialize_session_state, get_due_concepts
from question_bank import QUESTION_BANK
from llm_client import generate_practice_problem, generate_solution, generate_hint, generate_explanation
from learn_mode import render_learn_mode
from chatbot import render_chatbot_panel
from code_runner import execute_code
from code_editor import code_editor

def _render_output(result: dict):
    st.markdown("#### Output")
    if result["success"]:
        st.success("✅ Ran successfully")
        if result["stdout"].strip():
            st.code(result["stdout"], language="text")
        else:
            st.info("No output printed.")
    else:
        labels = {"compile_error": "🔴 Compile Error",
                  "runtime_error": "🟠 Runtime Error",
                  "timeout": "⏱ Time Limit Exceeded"}
        st.error(labels.get(result["error_type"], "❌ Error"))
        if result["clean_error"]:
            st.code(result["clean_error"], language="text")
        if result["stderr"] and result["stderr"] != result["clean_error"]:
            with st.expander("Full error details"):
                st.code(result["stderr"], language="text")

st.set_page_config(layout="wide", page_title="DSA Interview Prep", page_icon="🧠")

initialize_session_state()

if "chat_history" not in st.session_state:
    st.session_state["chat_history"] = []
if "active_tab" not in st.session_state:
    st.session_state["active_tab"] = "Practice"
if "user_code" not in st.session_state:
    st.session_state["user_code"] = ""
if "last_run_result" not in st.session_state:
    st.session_state["last_run_result"] = None
if "current_trace" not in st.session_state:
    st.session_state["current_trace"] = ""
if "trace_question" not in st.session_state:
    st.session_state["trace_question"] = ""
if "current_pseudocode" not in st.session_state:
    st.session_state["current_pseudocode"] = ""
if "current_quiz_question" not in st.session_state:
    st.session_state["current_quiz_question"] = ""

# --- SIDEBAR ---
with st.sidebar:
    st.title("🧠 DSA Interview Prep")
    
    api_key_input = st.text_input("Groq API Key (If not using .env)", type="password", value=st.session_state.api_key)
    if api_key_input != st.session_state.api_key:
        st.session_state.api_key = api_key_input
        st.rerun()
        
    st.markdown("---")
    
    # Topic and concept selectors
    topic_list = list(QUESTION_BANK.keys())
    
    # Default indices based on session state "route"
    default_topic_idx = 0
    if st.session_state.learn_topic in topic_list:
        default_topic_idx = topic_list.index(st.session_state.learn_topic)
        
    topic = st.selectbox("Topic", topic_list, index=default_topic_idx)
    st.session_state.learn_topic = topic
    
    concept_list = QUESTION_BANK[topic]
    default_concept_idx = 0
    if st.session_state.learn_concept in concept_list:
        default_concept_idx = concept_list.index(st.session_state.learn_concept)
        
    concept = st.selectbox("Concept", concept_list, index=default_concept_idx)
    st.session_state.learn_concept = concept
    
    difficulty = st.radio("Difficulty", ["Easy", "Medium", "Hard"])
    language = st.radio("Language", ["Python", "C++", "Java"])
    st.session_state.language = language
    
    mode = st.radio("Mode", ["🧩 Practice", "📖 Learn", "📖 Story/Case"])
    
    st.markdown("---")
    timed_mode = st.toggle("⏱ Interview Simulation")
    
    if timed_mode:
        duration_map = {"Easy": 10, "Medium": 20, "Hard": 30}
        st.session_state.timer_duration_minutes = duration_map[difficulty]
        
    st.markdown("---")
    with st.expander("Session History"):
        for item in reversed(st.session_state.history):
            st.write(f"- {item}")

# Handle timer logic
if timed_mode and st.session_state.timer_start:
    elapsed = (datetime.now() - st.session_state.timer_start).total_seconds()
    remaining = max(0, (st.session_state.timer_duration_minutes * 60) - elapsed)
    
    timer_placeholder = st.sidebar.empty()
    mins, secs = divmod(int(remaining), 60)
    timer_placeholder.markdown(f"### ⏱ {mins:02d}:{secs:02d}")
    
    if remaining == 0:
        st.warning("⏰ Time's up!")
        st.session_state.solution_shown = True # Auto reveal
        st.session_state.timer_start = None
    else:
        time.sleep(1)
        st.rerun()

# --- MAIN TABS ---
tab1, tab2, tab3 = st.tabs(["🧩 Practice", "📖 Learn Mode", "📋 Question Bank"])

with tab1:
    st.session_state["active_tab"] = "Practice"
    col_main, col_chat = st.columns([2, 1])
    with col_main:
        st.header("🧩 Practice Mode")
        if mode == "📖 Learn":
            st.info("You selected 'Learn' in the sidebar mode. Switch to the '📖 Learn Mode' tab to start learning, or change Mode in the sidebar to 'Practice'.")
        else:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("Generate Problem"):
                    with st.spinner("Generating problem..."):
                        st.session_state.timer_start = datetime.now() if timed_mode else None
                        is_story = (mode == "📖 Story/Case")
                        prob = generate_practice_problem(topic, concept, difficulty, language, is_story)
                        st.session_state.problem = prob
                        st.session_state.problem_generated = True
                        st.session_state.solution_shown = False
                        st.session_state.solution = None
                        st.session_state["chat_history"] = []
                        st.session_state["user_code"] = ""
                        st.session_state["last_run_result"] = None
                        st.session_state.history.append(f"{difficulty} {topic}: {concept} ({mode})")
                        
            with col2:
                if st.session_state.problem_generated:
                    if st.button("New Problem, Same Topic"):
                        with st.spinner("Generating new problem..."):
                            is_story = (mode == "📖 Story/Case")
                            prob = generate_practice_problem(topic, concept, difficulty, language, is_story)
                            st.session_state.problem = prob
                            st.session_state.solution_shown = False
                            st.session_state.solution = None
                            st.session_state["chat_history"] = []
                            st.session_state["user_code"] = ""
                            st.session_state["last_run_result"] = None
                            st.session_state.timer_start = datetime.now() if timed_mode else None
                            st.session_state.history.append(f"{difficulty} {topic}: {concept} ({mode})")
    
            if st.session_state.problem:
                st.markdown(st.session_state.problem)
                
                with st.expander("💡 Hint"):
                    if st.button("Show Hint"):
                        with st.spinner("Generating hint..."):
                            hint = generate_hint(st.session_state.problem, concept)
                            st.info(hint)
    
                if not st.session_state.solution_shown:
                    if st.button("Show Solution"):
                        st.session_state.solution_shown = True
                        st.session_state.timer_start = None # Stop timer
                        st.rerun()
                
                if st.session_state.solution_shown:
                    st.subheader("Solution")
                    if not st.session_state.solution:
                        with st.spinner("Generating solution..."):
                            sol = generate_solution(st.session_state.problem, language, topic, concept)
                            st.session_state.solution = sol
                            key = f"{topic}::{concept}"
                            st.session_state.practiced.add(key)
                    
                    lang_code = language.lower()
                    if lang_code == "c++": lang_code = "cpp"
                    st.code(st.session_state.solution, language=lang_code)
                    
                    if st.button("Explain Solution"):
                        with st.spinner("Explaining..."):
                            explanation = generate_explanation(st.session_state.solution, language, concept, topic)
                            st.info(explanation)
                
                # ── Code Editor ──────────────────────────────────────────────────────────
                st.markdown("#### ✏️ Your Code")
    
                lang_map = {"Python": "python", "C++": "c_cpp", "Java": "java"}
                language = st.session_state.get("language", "Python")
    
                TEMPLATES = {
                    "Python": "def solution():\n    # Write your code here\n    pass\n\n# Test\nprint(solution())",
                    "C++": '#include <iostream>\n#include <vector>\nusing namespace std;\n\nint main() {\n    // Write your code here\n    return 0;\n}',
                    "Java": 'public class Solution {\n    public static void main(String[] args) {\n        // Write your code here\n    }\n}'
                }
    
                default_code = st.session_state.get("user_code") or TEMPLATES.get(language, "")
    
                editor_buttons = [
                    {"name": "▶ Run", "feather": "Play", "primary": True, "hasText": True,
                     "showWithIcon": True, "commands": ["submit"],
                     "style": {"bottom": "0.44rem", "right": "0.4rem"}},
                    {"name": "Copy", "feather": "Copy", "hasText": True,
                     "commands": ["copyAll"], "style": {"bottom": "0.44rem", "right": "6rem"}}
                ]
    
                response = code_editor(
                    code=default_code,
                    lang=lang_map.get(language, "python"),
                    height="300px",
                    theme="monokai",
                    buttons=editor_buttons,
                    options={"fontSize": 14, "tabSize": 4, "showPrintMargin": False,
                             "enableBasicAutocompletion": True, "enableLiveAutocompletion": True},
                    key=f"editor_{language}"
                )
    
                # Handle Run button
                if response and response.get("type") == "submit":
                    code = response.get("text", "")
                    st.session_state["user_code"] = code
                    with st.spinner("Running..."):
                        result = execute_code(code, language)
                    st.session_state["last_run_result"] = result
                    _render_output(result)
    
                # AI Code Review button
                if st.session_state.get("user_code") and st.session_state.get("problem"):
                    if st.button("🤖 Check with AI", key="ai_review"):
                        review_prompt = f"""You are a DSA interview code reviewer.
    
                Problem: {st.session_state['problem']}
                Language: {language}
                User's code:
                {st.session_state['user_code']}
    
                Respond in this EXACT format:
                **Verdict:** Correct / Partially Correct / Incorrect / Syntax Error
                **What's right:** [1–2 sentences]
                **Issues:** [bullet list — specific, with line numbers if possible]
                **Hint to fix:** [one sentence nudge, no full solution]
                **Complexity:** Time: O(?) | Space: O(?)"""
    
                        with st.spinner("Reviewing your code..."):
                            from llm_client import call_llm   # use your existing llm_client function
                            review = call_llm(review_prompt, st.session_state.get("api_key", ""))
                        st.markdown("#### 🤖 AI Review")
                        st.info(review)
    
                # Load Solution into Editor button (show only after solution is revealed)
                if st.session_state.get("solution_shown") and st.session_state.get("solution"):
                    if st.button("📋 Load Solution into Editor", key="load_solution"):
                        st.session_state["user_code"] = st.session_state["solution"]
                        st.rerun()
    with col_chat:
        render_chatbot_panel()

with tab2:
    st.session_state["active_tab"] = "Learn Mode"
    col_main, col_chat = st.columns([2, 1])
    with col_main:
        if mode == "📖 Learn":
            render_learn_mode()
        else:
             st.info("You are currently in Practice Mode. Change 'Mode' in the sidebar to '📖 Learn' to start the learning sequence here.")
    with col_chat:
        render_chatbot_panel()

with tab3:
    st.session_state["active_tab"] = "Question Bank"
    st.header("📋 Question Bank")
    
    due_concepts = get_due_concepts()
    
    for tpc, configs in QUESTION_BANK.items():
        practiced_in_topic = sum(1 for c in configs if f"{tpc}::{c}" in st.session_state.practiced)
        learned_in_topic = sum(1 for c in configs if f"{tpc}::{c}" in st.session_state.learned_concepts)
        
        st.subheader(f"{tpc} (Learned: {learned_in_topic}/{len(configs)}, Practiced: {practiced_in_topic}/{len(configs)})")
        st.progress(learned_in_topic / len(configs))
        
        for c in configs:
            key = f"{tpc}::{c}"
            
            status = "⬜ Not started"
            if key in due_concepts:
                status = "🔥 Review due"
            elif key in st.session_state.learned_concepts:
                status = "✅ Learned"
            elif key in st.session_state.practiced:
                status = "📝 Practiced"
                
            colA, colB, colC = st.columns([6, 2, 2])
            colA.write(f"**{c}** — {status}")
            
            if colB.button("Practice This", key=f"prac_{tpc}_{c}"):
                st.session_state.learn_topic = tpc
                st.session_state.learn_concept = c
                st.rerun()
                
            if colC.button("Learn This", key=f"lrn_{tpc}_{c}"):
                st.session_state.learn_topic = tpc
                st.session_state.learn_concept = c
                # Force reset learn stage so learn mode restarts for this concept
                st.session_state.learn_stage = 1
                st.session_state.learn_trace_answered = False
                st.session_state.learn_blank_answered = False
                st.session_state.learn_feynman_submitted = False
                st.session_state.learn_quiz_submitted = False
                st.rerun()
