import streamlit as st
from datetime import datetime, date
import os
from dotenv import load_dotenv

def process_api_key():
    load_dotenv()
    env_key = os.getenv("GROQ_API_KEY", "")
    if env_key and env_key != "your_key_here" and not st.session_state.get("api_key"):
        st.session_state.api_key = env_key

def initialize_session_state():
    """Initialize necessary session state variables for the app."""
    defaults = {
        "problem": None,
        "solution": None,
        "api_key": "",
        "practiced": set(),
        "history": [],
        "timer_start": None,
        "timed_mode": False,
        "timer_duration_minutes": 10,
        "problem_generated": False,
        "solution_shown": False,
        "learn_stage": 1,
        "learn_concept": None,
        "learn_topic": None,
        "learn_trace_answered": False,
        "learn_blank_answered": False,
        "learn_feynman_submitted": False,
        "learn_quiz_submitted": False,
        "learned_concepts": {},  # "topic::concept" -> {"score": X, "first_learned": date, "next_review": date}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
            
    process_api_key()

def get_due_concepts():
    """Return a list of concepts that are due for review."""
    due = []
    today = date.today()
    if "learned_concepts" in st.session_state:
        for concept_key, data in st.session_state["learned_concepts"].items():
            if data["next_review"] and data["next_review"] <= today:
                due.append(concept_key)
    return due
    
def mark_concept_learned(topic, concept, score):
    """Update spaced repetition schedule based on score."""
    today = date.today()
    key = f"{topic}::{concept}"
    
    if score == 3:
        next_review_days = 3
    elif score == 2:
        next_review_days = 1
    else:
        next_review_days = 0 # Today/immediate
        
    next_review = date.fromordinal(today.toordinal() + next_review_days)
    
    st.session_state["learned_concepts"][key] = {
        "score": score,
        "first_learned": today,
        "next_review": next_review
    }
