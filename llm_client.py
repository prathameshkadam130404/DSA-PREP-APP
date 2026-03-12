import json
import time
import streamlit as st
from groq import Groq

def get_groq_client():
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        raise ValueError("API Key not set. Please provide your Groq API key in the sidebar or .env file.")
    return Groq(api_key=api_key)

def call_llm(prompt, temperature=0.7):
    client = get_groq_client()
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200,
            temperature=temperature
        )
        time.sleep(0.5) # Rate limit protection for free tier (30 req/min)
        return response.choices[0].message.content
    except Exception as e:
        raise RuntimeError(f"API Error: {str(e)}")

# --- EXACT PROMPTS FROM SPEC ---

def generate_practice_problem(topic, concept, difficulty, language, is_story_mode=False):
    if is_story_mode:
        prompt = f"""You are a coding interview question generator. Top tech companies wrap DSA problems in real-world scenarios.

Generate a STORY-BASED problem testing: {concept} ({topic}) at {difficulty} difficulty.
The scenario must come from a realistic tech context (e-commerce, logistics, banking, ride-sharing, etc.).
Do NOT name the algorithm or data structure in the problem.

Format EXACTLY:
**Scenario:** [2–3 sentence real-world context]
**Problem:** [problem statement that naturally requires the DSA concept]
**Input:** [format]
**Output:** [format]
**Example 1:** Input: ... | Output: ...
**Example 2:** Input: ... | Output: ...
**Constraints:** [brief]
**Pattern:** [shown only after user views solution]"""
    else:
        prompt = f"""You are an expert coding interview question generator for FAANG/product company interviews.

Generate a coding problem:
- Topic: {topic}
- Concept: {concept}
- Difficulty: {difficulty}
- Language: {language}

Format EXACTLY:
**Problem:** [1–3 sentences]
**Input:** [format]
**Output:** [format]
**Example 1:** Input: ... | Output: ...
**Example 2:** Input: ... | Output: ...
**Constraints:** [brief]
**Pattern:** [pattern name e.g. Two Pointers, Sliding Window, Hashing]

No solution. No fluff."""
    return call_llm(prompt)

def generate_solution(problem_statement, language, topic, concept):
    prompt = f"""You are a coding interview coach. Generate a clean, interview-optimized solution.

Problem: {problem_statement}
Language: {language}
Topic: {topic} | Concept: {concept}

Requirements:
- Most optimal known solution
- Line 1: comment with Time: O(...) | Space: O(...)
- Brief inline comments on key logic only
- SHORT — timed interview style, not production code
- No unnecessary boilerplate

Return ONLY the code. No text outside the code block."""
    return call_llm(prompt)

def generate_hint(problem_statement, concept):
    prompt = f"""The user is solving this problem: {problem_statement}
The underlying concept is: {concept}

Give ONE sentence nudging toward the right approach WITHOUT:
- Naming the algorithm or data structure
- Giving away the solution
- Using the word "{concept}"

One sentence only. Be subtle but genuinely useful."""
    return call_llm(prompt)

def generate_explanation(solution_code, language, concept, topic):
    prompt = f"""Explain this {language} solution for {concept} ({topic}) in exactly 5–7 lines.
Cover: (1) core algorithm/pattern, (2) key insight, (3) why over brute force, (4) complexity.
Direct. Technical. No filler.

Solution: {solution_code}"""
    return call_llm(prompt)

# --- LEARN MODE PROMPTS ---

def learn_stage_1(concept, topic):
    prompt = f"""You are a patient CS tutor teaching {concept} ({topic}) to someone who has NEVER seen it before.

Generate:
1. A 4–6 sentence plain-English explanation of what {concept} does and why it exists
2. A real-world analogy that requires NO coding knowledge (e.g., stack = plate stack)
3. The core question this algorithm/structure answers (one sentence)
4. When to use it: 2–3 bullet points (describe situations, not algorithm names)

No code. No pseudocode. No jargon without explanation.
Use simple language. The goal is an "aha moment", not a textbook definition."""
    return call_llm(prompt)

def learn_stage_2(concept, example_input):
    prompt = f"""Generate a step-by-step trace of {concept} on this small input: {example_input}.

Format as a markdown table showing all relevant variable states at each step.
- Column headers = the key variables in this algorithm
- One row per step
- Last row = final result

After the table, write:
"Interactive check: What would row {{N}} look like?" (pick a middle row)

Keep the input tiny (array of 5-6 elements max). Make the trace self-explanatory."""
    return call_llm(prompt)

def learn_stage_3(concept, brief_hint=""):
    prompt = f"""Write the pseudocode for {concept} as numbered steps with indentation.
Use plain English, no syntax. Make it readable to a non-programmer.

Then provide a "fill-in-the-blank" version:
Replace 2 key lines with "_____ (hint: {brief_hint})"
These should be the most important/non-non_obvious lines.

Show both: the complete pseudocode, then the blanked version."""
    return call_llm(prompt)

def learn_stage_4(concept, language):
    prompt = f"""Write a clean, interview-optimized {language} solution for {concept}.

Requirements:
- Line 1: # Time: O(...) | Space: O(...)
- Every 2-3 lines: one-line comment explaining the logic (not what the code does, WHY)
- Short and writable in under 5 minutes

After the code, provide two sections:
**Key lines to memorize:** [2–3 lines that are the heart of the algorithm, with why]
**Common beginner mistakes:** [2 bullet points]"""
    return call_llm(prompt)

def learn_stage_5(concept, user_explanation):
    prompt = f"""A student learning {concept} for the first time wrote this explanation:
"{user_explanation}"

Evaluate strictly:
- Does it show genuine understanding of the core mechanism? (not just surface words)
- Is the key insight present, even if phrased differently?
- What's missing or wrong if anything?

Respond with:
**Verdict:** Understood / Partially Understood / Try Again
**Feedback:** [2–3 sentences: what they got right, what's missing, what the key insight actually is]

Be honest. Don't be encouraging if the explanation misses the point."""
    return call_llm(prompt)

def learn_stage_6(concept, topic):
    prompt = f"""Generate 3 multiple-choice questions to test understanding of {concept} ({topic}).

Question types (one each):
1. Conceptual: what does this do / when to use it
2. Complexity: time or space complexity
3. Code/logic: what does this line produce / what's the bug in this snippet

Format for each question:
Q: [question text]
A) [option]
B) [option]
C) [option]
D) [option]
Answer: [letter]
Explanation: [one sentence why]

Make the wrong answers plausible (common misconceptions, off-by-one errors, etc.)
Return as JSON array for easy parsing:
[{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "answer": "B", "explanation": "..."}}]"""
    return call_llm(prompt)
