from groq import Groq
from dotenv import load_dotenv
import os
import streamlit as st

st.title('Your AI Tutor 🤖')

if "conversation" not in st.session_state:
    st.session_state.conversation = [{"role": "system", "content": "You are a strict but good and friendly AI interviewer. Give answers in about 20 words"}]


load_dotenv()

api = os.getenv('api')
api = Groq(api_key = api)

st.sidebar.title('Interview Topics')
topic = st.sidebar.selectbox('Select a topic', ['Python', 'Machine Learning', 'Deep Learning', 'Web development', 'Frontend Languages', 'C', 'C++', 'Java', 'Javascript', 'R'])

if 'user_input' not in st.session_state:
    st.session_state.user_input = f'Ask easy questions of {topic} and then advance'
else:
    st.session_state.user_input = f"Explain {topic} in simple words"

inp = st.text_input('Ask your question :', value = st.session_state.user_input)    

if st.button("Ask AI Tutor"):
    st.session_state.conversation.append({"role": "user", "content": inp})
        
response = api.chat.completions.create(model = 'llama-3.1-8b-instant',
                                       messages = st.session_state.conversation)

answer = response.choices[0].message.content
st.session_state.conversation.append({'role' : 'assistant', 'content' : answer})

st.subheader('AI Interviewer answer')
st.write(answer)