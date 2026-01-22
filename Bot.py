from openai import OpenAI
from dotenv import load_dotenv
import os
import streamlit as st
import json

# -------------------- SETUP --------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="AI Interview Bot", layout="centered")
st.title("🎤 AI Interview Bot (HR Mode)")

# -------------------- SESSION STATE --------------------
defaults = {
    "started": False,
    "question_no": 0,
    "conversation": [],
    "ui_history": [],
    "results": [],
    "current_question": "",
    "topic": ""
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# -------------------- SIDEBAR --------------------
st.sidebar.header("Interview Settings")

preset_topic = st.sidebar.selectbox(
    "Select Topic",
    ["", "Python", "Machine Learning", "Deep Learning","Web Development", "C", "C++", "Java", "Javascript", "Frontend Languages"]
)

difficulty = st.sidebar.slider("Difficulty", 1, 3, 1)

if difficulty == 1:
    diff_text = 'easy, beginner level questions'
    marking_style = 'Lenient'

elif difficulty == 2:
    diff_text = 'Medium level, conceptual and practical questions'
    marking_style = 'balanced'

else:
    diff_text = 'Hard level, advanced interview questions'
    marking_style = 'very strict'

custom_topic = st.text_input(
    "Enter your interview topic (you can type your own):",
    value=preset_topic
).strip()

if not custom_topic:
    st.warning("Please select or enter a topic.")
    st.stop()

# -------------------- START INTERVIEW --------------------
if st.button("Start Interview"):
    st.session_state.started = True
    st.session_state.question_no = 1
    st.session_state.topic = custom_topic
    st.session_state.conversation = []
    st.session_state.ui_history = []
    st.session_state.results = []

    system_prompt = f"""
You are a senior HR technical interviewer but good and polite.
but when the interviewee give wrong answers again and again, 
reprimand the interviewee.

Interview topic: {custom_topic}
Difficulty: {diff_text}
Marking Style: {marking_style}

STRICT RULES:
- Ask exactly 5 questions
- Ask ONE question at a time
- No greetings, no introduction
- Do NOT use concepts or methods from other languages, topics.
- Ask questions strictly based on topic syntax and features.
- DO NOT repeat question numbers
- Questions must follow the selected topic and difficulty
- Be professional and strict
- Penalize vague or incorrect answers
- If answer is weak, mention it clearly
- Give feedback after each answer
- Do not reveal marks to candidate
IMPORTANT:
- First response MUST be ONLY the first interview question (plain text, no JSON)
- JSON response is REQUIRED ONLY AFTER user answers
- After each answer respond ONLY in JSON:
{{
  "score": 0-10,
  "feedback": "short HR-style feedback",
  "next_question": "next question text"
}}
- First response MUST be ONLY the first question
- Ask next question yourself
"""

    st.session_state.conversation.append(
        {"role": "system", "content": system_prompt}
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=st.session_state.conversation
    )

    first_q = response.choices[0].message.content.strip()
    st.session_state.current_question = first_q

    st.session_state.ui_history.append(
        {"type": "question", "text": first_q}
    )

    st.session_state.conversation.append(
        {"role": "assistant", "content": first_q}
    )

    st.rerun()

# -------------------- INTERVIEW UI --------------------
if st.session_state.started and st.session_state.question_no <= 5:

    st.subheader(f"Question {st.session_state.question_no}")

    for item in st.session_state.ui_history:
        if item["type"] == "question":
            st.markdown(f"**🟢 {item['text']}**")
        elif item["type"] == "answer":
            st.markdown(f"👤 **Your Answer:** {item['text']}")
        elif item["type"] == "feedback":
            st.info(f"🤖 HR Feedback: {item['text']}")

    # ---------- FORM (IMPORTANT FIX) ----------
    with st.form("answer_form", clear_on_submit=True):
        user_answer = st.text_input("Your Answer")
        submitted = st.form_submit_button("Submit Answer")

    if submitted:
        if user_answer.strip() == "":
            st.warning("Answer cannot be empty.")
            st.stop()

        st.session_state.ui_history.append(
            {"type": "answer", "text": user_answer}
        )

        st.session_state.conversation.append(
            {"role": "user", "content": user_answer}
        )

        eval_prompt = """
Respond ONLY in valid JSON.
No explanations.
"""

        messages = st.session_state.conversation + [
            {"role": "system", "content": eval_prompt}
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"}
        )

        data = json.loads(response.choices[0].message.content)

        score = int(data["score"])
        feedback = data["feedback"]
        next_q = data["next_question"]

        st.session_state.ui_history.append(
            {"type": "feedback", "text": feedback}
        )

        st.session_state.results.append({
            "question_no": st.session_state.question_no,
            "question": st.session_state.current_question,
            "feedback": feedback,
            "marks": score,
            "answer": user_answer
        })

        st.session_state.question_no += 1

        if st.session_state.question_no <= 5:
            st.session_state.current_question = next_q
            st.session_state.ui_history.append(
                {"type": "question", "text": next_q}
            )
            st.session_state.conversation.append(
                {"role": "assistant", "content": next_q}
            )

        st.rerun()

# -------------------- FINAL REPORT --------------------
if st.session_state.started and st.session_state.question_no > 5:
    st.success("Interview Completed ✅")
    st.balloons()
    st.subheader("📊 HR Evaluation Report")

    total = 0
    for r in st.session_state.results:
        st.markdown(
            f"""
**Question {r['question_no']}**
- Question: {r['question']}
- Answer: {r['answer']}
- HR Feedback: {r['feedback']}
- Marks: {r['marks']}/10
---
"""
        )
        total += r["marks"]

    st.subheader(f"🎯 Final Score: {total}/50")

    if total < 15:
        st.error("❌ HR Verdict: Not Suitable")
    elif total < 35:
        st.warning("⚠️ HR Verdict: Needs Improvement")
    else:
        st.success("✅ HR Verdict: Strong Candidate")
