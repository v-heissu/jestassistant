import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
import json

load_dotenv()

st.set_page_config(
    page_title="Infinite Jest Assistant",
    page_icon="📚",
    layout="wide"
)

# Inizializzazione delle variabili di sessione
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')

def get_assistant_response(page_number, question):
    """Ottiene la risposta dall'assistant"""
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    
    formatted_question = f"Sono a pagina {page_number}. {question}"
    
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=formatted_question
    )
    
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )
    
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            return {"safe_content": "Mi dispiace, c'è stato un errore.", "spoiler_content": "", "notes": []}
        time.sleep(1)
    
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    
    try:
        # Cerca di parsare la risposta come JSON
        response = json.loads(messages.data[0].content[0].text.value)
        return response
    except json.JSONDecodeError:
        # Se la risposta non è in formato JSON, usa il formato standard con separatore [SPOILER ALERT]
        full_response = messages.data[0].content[0].text.value
        safe_content = full_response
        spoiler_content = ""
        
        if "[SPOILER ALERT" in full_response:
            parts = full_response.split("[SPOILER ALERT")
            safe_content = parts[0]
            spoiler_content = parts[1]
        
        return {
            "safe_content": safe_content,
            "spoiler_content": spoiler_content,
            "notes": []
        }

st.title("🎭 Infinite Jest Assistant")
st.markdown("""
    Benvenuto nell'assistente alla lettura di Infinite Jest.
    Indica a che pagina sei arrivato e fai le tue domande!
""")

with st.sidebar:
    st.header("ℹ️ Informazioni")
    st.markdown("""
        Questo assistente ti aiuta nella lettura di Infinite Jest,
        fornendo risposte basate sul punto in cui ti trovi nel libro
        per evitare spoiler.
    """)
    
    if st.button("Nuova Conversazione"):
        st.session_state.thread_id = None
        st.session_state.messages = []
        st.rerun()

col1, col2 = st.columns([1, 4])
with col1:
    page_number = st.number_input("Pagina attuale:", min_value=1, max_value=1079, value=1)
with col2:
    question = st.text_input("La tua domanda:")

if st.button("Invia domanda"):
    if question:
        with st.spinner("Elaboro la risposta..."):
            response = get_assistant_response(page_number, question)
            st.session_state.messages.append({
                "role": "user", 
                "content": question
            })
            st.session_state.messages.append({
                "role": "assistant", 
                "content": response
            })

# Visualizza la cronologia dei messaggi
st.markdown("### Cronologia")
for msg in reversed(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown("**Tu:**")
        st.markdown(msg["content"])
    else:
        st.markdown("**Assistant:**")
        # Contenuto sicuro
        st.markdown(msg["content"]["safe_content"])
        
        # Spoiler con expander
        if msg["content"]["spoiler_content"]:
            with st.expander("👀 Mostra spoiler"):
                st.markdown(msg["content"]["spoiler_content"])
        
        # Note con expander
        if msg["content"]["notes"]:
            with st.expander("📝 Mostra note"):
                for note in msg["content"]["notes"]:
                    st.markdown(f"**Nota {note['number']}** (riferimento: p.{note['reference_page']})")
                    st.markdown(note["safe_content"])
                    if note["spoiler_content"]:
                        with st.expander("👀 Spoiler della nota"):
                            st.markdown(note["spoiler_content"])
    
    st.markdown("---")
