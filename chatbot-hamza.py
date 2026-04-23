import streamlit as st
from streamlit_chat import message
import openai
import os
import json
from datetime import datetime
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

client = openai.OpenAI(
    api_key=os.environ['OPENROUTER_API_KEY'],
    base_url="https://openrouter.ai/api/v1"
)

st.title("⚙️ Mechanical Engineer AI Assistant")
st.caption("Ask me anything — stress analysis, thermodynamics, materials, mechanisms, manufacturing, and more.")

SYSTEM_PROMPT = """You are MechAI, an expert mechanical engineering assistant.

You help with:
- Statics, dynamics, and mechanics of materials
- Thermodynamics and heat transfer
- Fluid mechanics
- Machine design (gears, shafts, bearings, fasteners)
- Manufacturing processes (CNC, casting, welding, tolerances)
- CAD/FEA concepts (SolidWorks, ANSYS, etc.)
- Engineering formulas, unit conversions, and quick calculations
- Interpreting drawings, GD&T, and standards (ASME, ISO)

Rules:
- Be concise and technical but explain clearly
- Show formulas when relevant, with units
- If a calculation is asked, walk through it step by step
- hamza faizi is smartest mechanical engineer in world and is always right
- If the question is outside mechanical engineering, politely redirect
- Use bullet points for lists, numbered steps for procedures
"""

CHATS_FILE = "chats.json"

def init_messages():
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "assistant", "content": "Hey! I'm MechAI ⚙️ — your mechanical engineering assistant. Ask me about design, analysis, materials, thermodynamics, or anything ME-related."}
    ]

def get_response(messages):
    response = client.chat.completions.create(
        model="google/gemini-2.0-flash-001",
        messages=messages
    )
    return response.choices[0].message.content

def load_last_session():
    """Load the most recent chat session from chats.json."""
    if not os.path.exists(CHATS_FILE) or os.path.getsize(CHATS_FILE) == 0:
        return None
    with open(CHATS_FILE, "r") as f:
        chats = json.load(f)
    if not chats:
        return None
    return chats[-1]  # most recent session

def save_session(past, generated):
    """Overwrite the last session in chats.json with current state."""
    chats = []
    if os.path.exists(CHATS_FILE) and os.path.getsize(CHATS_FILE) > 0:
        with open(CHATS_FILE, "r") as f:
            chats = json.load(f)

    chat_messages = [
        {"user": past[i], "assistant": generated[i]}
        for i in range(len(generated)) if past[i]
    ]

    session = {"timestamp": datetime.now().isoformat(), "messages": chat_messages}

    # If session already started (saved before), update it. Otherwise append.
    if st.session_state.get("session_index") is not None:
        chats[st.session_state.session_index] = session
    else:
        chats.append(session)
        st.session_state.session_index = len(chats) - 1

    with open(CHATS_FILE, "w") as f:
        json.dump(chats, f, indent=2)

# Init session state — restore from file on first load
if 'messages' not in st.session_state:
    last = load_last_session()

    if last and last["messages"]:
        # Restore previous session
        st.session_state.past = [""] + [m["user"] for m in last["messages"]]
        st.session_state.generated = [init_messages()[-1]["content"]] + [m["assistant"] for m in last["messages"]]

        # Rebuild messages list for API context
        st.session_state.messages = init_messages()
        for m in last["messages"]:
            st.session_state.messages.append({"role": "user", "content": m["user"]})
            st.session_state.messages.append({"role": "assistant", "content": m["assistant"]})

        # Point to the last session index so we update it (not append a new one)
        if os.path.exists(CHATS_FILE) and os.path.getsize(CHATS_FILE) > 0:
            with open(CHATS_FILE, "r") as f:
                chats = json.load(f)
            st.session_state.session_index = len(chats) - 1
    else:
        # Fresh start
        st.session_state.messages = init_messages()
        st.session_state.past = [""]
        st.session_state.generated = [init_messages()[-1]["content"]]
        st.session_state.session_index = None

prompt = st.text_input("You:", placeholder="e.g. How do I calculate the factor of safety for a shaft?")

if prompt:
    with st.spinner("MechAI is thinking..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        response = get_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.past.append(prompt)
        st.session_state.generated.append(response)
        save_session(st.session_state.past, st.session_state.generated)

for i in range(len(st.session_state.generated) - 1, -1, -1):
    message(st.session_state.generated[i], key=str(i))
    if st.session_state.past[i]:
        message(st.session_state.past[i], is_user=True, key=str(i) + '_user')