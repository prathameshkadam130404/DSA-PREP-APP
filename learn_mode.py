import streamlit as st
import json
from datetime import datetime
from llm_client import *
from utils import mark_concept_learned

def render_learn_mode():
    st.header("📖 Learn Mode")
    
    # Check if concept is selected
    if not st.session_state.learn_concept:
        st.info("Select a topic and concept from the sidebar 'Learn' mode to begin learning.")
        return

    concept = st.session_state.learn_concept
    topic = st.session_state.learn_topic
    stage = st.session_state.learn_stage
    
    st.progress(stage / 6, text=f"Stage {stage} of 6 — {concept}")
    
    # Render stages based on progress
    if stage >= 1:
        render_stage_1(concept, topic)
    if stage >= 2:
        render_stage_2(concept)
    if stage >= 3:
        render_stage_3(concept)
    if stage >= 4:
        render_stage_4(concept, st.session_state.get("language", "Python"))
    if stage >= 5:
        render_stage_5(concept)
    if stage >= 6:
        render_stage_6(concept, topic)

def render_stage_1(concept, topic):
    st.subheader("Stage 1: UNDERSTAND IT")
    
    content_key = f"learn_stage1_{concept}"
    if content_key not in st.session_state:
        with st.spinner("Generating explanation..."):
            st.session_state[content_key] = learn_stage_1(concept, topic)
            
    st.markdown(st.session_state[content_key])
    
    if st.session_state.learn_stage == 1:
        if st.button("✅ I understand this, continue →", key="btn_s1"):
            st.session_state.learn_stage = 2
            st.rerun()
    st.divider()

def render_stage_2(concept):
    st.subheader("Stage 2: VISUALIZE IT")
    
    content_key = f"learn_stage2_{concept}"
    if content_key not in st.session_state:
        with st.spinner("Generating trace..."):
            st.session_state[content_key] = learn_stage_2(concept, "[1, 3, 5, 7, 9]") # Generic small input
            
    trace_content = st.session_state[content_key]
    
    # Split content around the "Interactive check" to hide the bottom part initially
    if "Interactive check:" in trace_content:
        parts = trace_content.split("Interactive check:")
        trace_table = parts[0]
        check_text = "Interactive check:" + parts[1]
    else:
        trace_table = trace_content
        check_text = "What would the next row look like?"
        
    st.session_state["current_trace"] = trace_content
    st.session_state["trace_question"] = check_text
        
    st.markdown(trace_table)
    
    if not st.session_state.learn_trace_answered:
        st.write(check_text)
        user_guess = st.text_input("Your prediction:", key=f"pred_{concept}")
        if st.button("Check", key="check_s2"):
            if user_guess:
                st.session_state.learn_trace_answered = True
                st.rerun()
    else:
        st.success("Great! Let's continue.")
        if st.session_state.learn_stage == 2:
            if st.button("✅ I understand this, continue →", key="btn_s2"):
                st.session_state.learn_stage = 3
                st.rerun()
    st.divider()

def render_stage_3(concept):
    st.subheader("Stage 3: PSEUDOCODE IT")
    
    content_key = f"learn_stage3_{concept}"
    if content_key not in st.session_state:
        with st.spinner("Generating pseudocode..."):
            st.session_state[content_key] = learn_stage_3(concept, "Look for the key condition")
            
    content = st.session_state[content_key]
    st.session_state["current_pseudocode"] = content
    
    if not st.session_state.learn_blank_answered:
        st.markdown(content)
        user_fill = st.text_input("Fill in the blanks:", key=f"fill_{concept}")
        if st.button("Check", key="check_s3"):
            if user_fill:
                st.session_state.learn_blank_answered = True
                st.rerun()
    else:
        st.markdown(content)
        st.success("Looks correct!")
        if st.session_state.learn_stage == 3:
            if st.button("✅ I understand this, continue →", key="btn_s3"):
                st.session_state.learn_stage = 4
                st.rerun()
    st.divider()

def render_stage_4(concept, language):
    st.subheader("Stage 4: CODE IT")
    
    content_key = f"learn_stage4_{concept}_{language}"
    if content_key not in st.session_state:
        with st.spinner("Generating code..."):
            st.session_state[content_key] = learn_stage_4(concept, language)
            
    st.markdown(st.session_state[content_key])
    
    if st.session_state.learn_stage == 4:
        if st.button("✅ I understand this, continue →", key="btn_s4"):
            st.session_state.learn_stage = 5
            st.rerun()
    st.divider()

def render_stage_5(concept):
    st.subheader("Stage 5: FEYNMAN CHECK")
    st.write("Close your notes. In 2-3 sentences, explain how this works as if you're explaining it to a friend who doesn't code. Don't use technical terms.")
    
    user_explanation = st.text_area("Your explanation:", key=f"feynman_{concept}")
    
    if st.button("Submit Explanation", key="btn_s5_sub"):
        if user_explanation:
            with st.spinner("Evaluating..."):
                feedback = learn_stage_5(concept, user_explanation)
                st.session_state[f"feynman_feedback_{concept}"] = feedback
                st.session_state.learn_feynman_submitted = True
    
    if st.session_state.learn_feynman_submitted:
        feedback = st.session_state.get(f"feynman_feedback_{concept}", "")
        st.markdown(feedback)
        
        if "Understood" in feedback or "Partially" in feedback:
            if st.session_state.learn_stage == 5:
                if st.button("✅ Move to Final Quiz →", key="btn_s5_next"):
                    st.session_state.learn_stage = 6
                    st.rerun()
    st.divider()

def render_stage_6(concept, topic):
    st.subheader("Stage 6: RECALL QUIZ")
    
    content_key = f"learn_stage6_{concept}"
    if content_key not in st.session_state:
        with st.spinner("Generating Quiz..."):
            quiz_str = learn_stage_6(concept, topic)
            # Try to parse JSON
            try:
                # Strip markdown code blocks if exist
                if "```json" in quiz_str:
                    quiz_str = quiz_str.split("```json")[1].split("```")[0].strip()
                elif "```" in quiz_str:
                    quiz_str = quiz_str.split("```")[1].split("```")[0].strip()
                st.session_state[content_key] = json.loads(quiz_str)
            except Exception as e:
                st.error(f"Failed to load quiz. Error: {e}")
                st.write("Raw Output:", quiz_str)
                return

    quiz_data = st.session_state[content_key]
    
    # Check if already submitted
    submitted = st.session_state.learn_quiz_submitted
    
    answers = []
    
    with st.form(key=f"quiz_form_{concept}"):
        for i, q in enumerate(quiz_data):
            st.write(f"**Q{i+1}: {q['question']}**")
            options = list(q['options'].values())
            keys = list(q['options'].keys())
            
            selected_option = st.radio(
                "Select answer:", 
                options, 
                key=f"q_{concept}_{i}",
                disabled=submitted
            )
            
            # Get corresponding letter
            idx = options.index(selected_option) if selected_option in options else -1
            selected_letter = keys[idx] if idx >= 0 else None
            
            answers.append({
                "selected_letter": selected_letter,
                "correct_letter": q['answer'],
                "explanation": q['explanation']
            })
            
            if submitted:
                if selected_letter == q['answer']:
                    st.success(f"✅ Correct! {q['explanation']}")
                else:
                    st.error(f"❌ Incorrect. Correct answer was {q['answer']}. {q['explanation']}")
            st.write("---")

        sub_btn = st.form_submit_button("Submit Quiz", disabled=submitted)
        if sub_btn and not submitted:
            score = sum([1 for a in answers if a['selected_letter'] == a['correct_letter']])
            st.session_state.learn_quiz_submitted = True
            
            # Record score state in session temporarily so we can show it outside form action too
            st.session_state[f"quiz_score_{concept}"] = score
            mark_concept_learned(topic, concept, score)
            st.rerun()

    if submitted:
        score = st.session_state.get(f"quiz_score_{concept}", 0)
        st.write(f"**Final Score: {score}/3**")
        if score == 3:
            st.success("Mastered! Marked for spaced repetition Day 1 → 3 → 7 → 14")
        elif score == 2:
            st.warning("Good, review Stage 2-3 once more. Marked for review tomorrow.")
        else:
            st.error("Go back to Stage 1. This concept needs more time.")
            if st.button("Restart Concept"):
                # Reset states
                st.session_state.learn_stage = 1
                st.session_state.learn_trace_answered = False
                st.session_state.learn_blank_answered = False
                st.session_state.learn_feynman_submitted = False
                st.session_state.learn_quiz_submitted = False
                st.rerun()
