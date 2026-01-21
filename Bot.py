from openai import OpenAI
from dotenv import load_dotenv
import os
import streamlit as st
import json

load_dotenv()

client = OpenAI(api_key = os.getenv('OPENAI_API_KEY'))

st.title('Your AI Interview Bot 🤖')

if 'custom_topic' not in st.session_state:
    st.session_state.custom_topic = ''

if 'started' not in st.session_state:
    st.session_state.started = False

if 'question_no' not in st.session_state:
    st.session_state.question_no = 0

if 'conversation' not in st.session_state:
    st.session_state.conversation = []

if 'results' not in st.session_state:
    # Yahan question, topics, marks store honge
    st.session_state.results = []

if 'ui_history' not in st.session_state:
    st.session_state.ui_history = []

st.sidebar.title('Interview Settings')

# Select Topic

preset_topic = st.sidebar.selectbox(
    'Select Topic',
    [
        '',
        'Python',
        'Machine Learning',
        'Deep Learning',
        'Web Development',
        'C',
        'C++',
        'Java',
        'Javascript',
        'Frontend Languages'
    ],
    index=0
)

# Auto-fill text input if preset selected
if preset_topic:
    st.session_state.custom_topic = preset_topic
# Choose difficulty

difficulty = st.sidebar.slider('Select Difficulty', 
                               min_value = 1,
                               max_value = 3,
                               value = 1)

# Difficulty logic

if difficulty == 1:
    diff_text = 'easy, beginner level questions'
    marking_style = 'Lenient'

elif difficulty == 2:
    diff_text = 'Medium level, conceptual and practical questions'
    marking_style = 'balanced'

else:
    diff_text = 'Hard level, advanced interview questions'
    marking_style = 'very strict'

# Interview start 
st.subheader("Choose Interview Topic")

custom_topic = st.text_input(
    "Enter your interview topic (you can type your own):",
    value=st.session_state.custom_topic
)

# Keep session state updated
st.session_state.custom_topic = custom_topic.strip()

final_topic = st.session_state.custom_topic

if not final_topic:
    st.warning("Please select or enter a topic to start the interview.")
    st.stop()

if st.button('Start interview'):
    st.session_state.started = True
    st.session_state.question_no = 1
    st.session_state.conversation = []
    st.session_state.results = []
    st.session_state.ui_history = []

    system_prompt = f"""
You are a professional AI Interviewer but good and polite.
but when the interviewee give wrong answers again and again, 
reprimand the interviewee.

Interview Topic : {final_topic}
Difficulty level : {diff_text}
Marking style : {marking_style}

Rules:
- Ask only one question at a time
- Ask exactly 5 questions
- Questions must be direct and specific
- Do NOT use concepts or methods from other languages topics.
- Ask questions strictly based on topic syntax and features.
- if the interviewee give the topic in the text input take the interview on that topic
- DO NOT repeat question numbers
- Ask ONLY the question text
- Questions must follow the selected topic and difficulty
- After each answer evaluate silently
- Don"t ask the next question until the topic of the previous question is completely clear.
- Do not show marks
- Don't label the greet with Question, only show Question before the real question
- After each answer, respond ONLY in JSON:
{{
  "score": <0-10>,
  "feedback": "<short feedback>",
  "next_question": "<next question text>"
}}
- Ask next question yourself when the topic of previous question is completely clear.
"""
    
    st.session_state.conversation = [{'role' : 'system', 'content' : system_prompt}]
    
    response = client.chat.completions.create(
        model = 'gpt-4o-mini',
        messages = st.session_state.conversation)
    
    first_ques = response.choices[0].message.content.strip()
    st.session_state.current_ques = first_ques

    st.session_state.ui_history.append({
        'type' : 'question',
        'text' : first_ques
    })
    st.session_state.conversation.append(
        {'role': 'assistant', 'content' : first_ques}
    )

    st.rerun()

if st.session_state.started and st.session_state.question_no <= 5:
    st.subheader('Interview Progress')

    for item in st.session_state.ui_history:
        if item['type'] == 'question':
            st.markdown(f"🟢 **{item['text']}**")
        elif item['type'] == 'answer':
            st.markdown(f"👤 **Your Answer:** {item['text']}")
        elif item['type'] == 'feedback':
            st.info(f"🤖 Feedback: **{item['text']}**")


    user_ans = st.text_input(
        'Your Answer:',
        key=f'ans_{st.session_state.question_no}'
    )

    if st.button('Submit Answer'):
        st.session_state.ui_history.append(
            {'type' : 'answer', 'text' : user_ans}
        )
        st.session_state.conversation.append(
            {'role': 'user', 'content': user_ans}
        )

        eval_prompt = """
Respond ONLY in valid json.
No extra text.

{"score" : <integer 0-10>,
"feedback" : "<short feedback>",
"next_question" : "<next question>"}

"""

        st.session_state.conversation.append(
            {'role' : 'system', 'content' : eval_prompt}
            )

        response = client.chat.completions.create(
                model = 'gpt-4o-mini',
                messages = st.session_state.conversation
            )

        ai_reply = response.choices[0].message.content

        ## Safe json format

        try:
            data = json.loads(ai_reply)
            score = int(data.get('score', 0))
            feedback = data.get('feedback', "")
            next_ques = data.get('next_question', "")

            st.session_state.ui_history.append(
                {'type' : 'feedback',
                 'text': feedback}
            )

        except Exception:
            score = 0
            feedback = 'Evaluation failed'
            next_ques = response.choices[0].message.content.strip()

        st.session_state.results.append(
                {'question_no' : st.session_state.question_no,
                 'topic' : final_topic,
                 'question' : st.session_state.current_ques,
                 'marks' : score}
            )

        st.session_state.conversation.append(
                {'role' : 'assistant' , 'content' : ai_reply}
            )
                        
            # Next Question

        if st.session_state.question_no < 5:
                st.session_state.question_no += 1
                st.session_state.ui_history.append({
                'type' : 'question',
                'text' : f'Question : {st.session_state.question_no}: {next_ques}'
            })
                st.session_state.conversation.append(
                    {'role' : 'assistant', 'content' : next_ques}
                )
                st.rerun()
        else:
            st.session_state.question_no += 1
            st.rerun()
            # Interview end

if st.session_state.started and st.session_state.question_no > 5:
    st.success('Interview completed ✅')
    st.balloons()
    st.subheader('Detailed Marks Report')

    total = 0
    for r in st.session_state.results:
        st.markdown(
                        f"""
#### Question : {r['question_no']}\n
- Topic : {r['topic']}\n
- Question Asked : {r['question']}\n
- Marks : {r['marks']}/10
---
"""
                    )

        total += r['marks']
    st.subheader(f"🎯 Overall Score {total}/50")