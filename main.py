import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time

# Carica le variabili d'ambiente
load_dotenv()

# Configurazione della pagina
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

# Inizializzazione client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')  # Da configurare dopo aver creato l'assistant

def create_thread():
    """Crea un nuovo thread se non esiste"""
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

def get_assistant_response(page_number, question):
    """Ottiene la risposta dall'assistant"""
    if not st.session_state.thread_id:
        create_thread()
    
    # Formatta il messaggio con il numero di pagina
    formatted_question = f"Sono a pagina {page_number}. {question}"
    
    # Invia il messaggio
    message = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=formatted_question
    )
    
    # Avvia la run
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=assistant_id
    )
    
    # Attendi la risposta
    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=st.session_state.thread_id,
            run_id=run.id
        )
        if run_status.status == 'completed':
            break
        elif run_status.status == 'failed':
            return "Mi dispiace, c'è stato un errore nel processare la tua richiesta."
        time.sleep(1)
    
    # Ottieni i messaggi
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    
    # Ritorna l'ultima risposta
    return messages.data[0].content[0].text.value

# UI Layout
st.title("🎭 Infinite Jest Assistant")
st.markdown("""
    Benvenuto nell'assistente alla lettura di Infinite Jest.
    Indica a che pagina sei arrivato e fai le tue domande!
""")

# Sidebar per informazioni e configurazione
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

# Input utente
col1, col2 = st.columns([1, 4])
with col1:
    page_number = st.number_input("Pagina attuale:", min_value=1, max_value=1079, value=1)
with col2:
    question = st.text_input("La tua domanda:")

# Pulsante per inviare la domanda
if st.button("Invia domanda"):
    if question:
        with st.spinner("Elaboro la risposta..."):
            response = get_assistant_response(page_number, question)
            
            # Aggiungi messaggi alla cronologia
            st.session_state.messages.append({"role": "user", "content": question})
            st.session_state.messages.append({"role": "assistant", "content": response})
    else:
        st.warning("Per favore, inserisci una domanda.")

# Visualizza la cronologia dei messaggi
st.markdown("### Cronologia")
for msg in reversed(st.session_state.messages):
    if msg["role"] == "user":
        st.markdown("**Tu:**")
        st.markdown(msg["content"])
    else:
        st.markdown("**Assistant:**")
        st.markdown(msg["content"])
    st.markdown("---")
