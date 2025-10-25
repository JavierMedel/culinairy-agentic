import streamlit as st
from openai import OpenAI

# Connect to your local NIM endpoint
client = OpenAI(base_url="http://localhost:8000/v1", api_key="none")

st.set_page_config(page_title="💬 NVIDIA Llama Chat", layout="wide")
st.title("💬 Chat with NVIDIA Llama 3.1 (Local)")

# Session state to store chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I’m your local NVIDIA Llama model. How can I help today?"}
    ]

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🧑 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **Llama:** {msg['content']}")

# Input box for new user messages
user_input = st.chat_input("Type your message here...")

# When user sends a new message
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-nano-8b-v1",
            messages=st.session_state.messages,
            max_tokens=256,
            temperature=0.7,
        )

        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})

    st.rerun()
