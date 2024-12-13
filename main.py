import streamlit as st
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from datetime import datetime

load_dotenv()

# Configurazione pagina
st.set_page_config(
    page_title="Infinite Jest Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Stile CSS personalizzato con ottimizzazioni mobile
st.markdown("""
<style>
    /* Stili generali */
    .main {
        background-color: #1e1e1e;
    }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #2d2d2d;
        color: #ffffff;
    }
    
    /* Bottom Navigation Bar ottimizzata */
    .bottom-nav {
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        width: 200px;
        background: #1e1e1e;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        padding: 10px;
    }
    
    .bottom-nav button {
        margin-right: 8px;
        padding: 8px 12px;
        border-radius: 20px;
        border: none;
        background: #4CAF50;
        color: white;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .bottom-nav button:hover {
        background: #45a049;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.4);
    }
    
    /* Box citazione */
    .quote-box {
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
        transition: all 0.3s ease;
    }
    .quote-valid {
        background-color: rgba(76, 175, 80, 0.1);
        border: 2px solid #4CAF50;
        box-shadow: 0 0 10px rgba(76, 175, 80, 0.2);
    }
    .quote-invalid {
        background-color: rgba(244, 67, 54, 0.1);
        border: 2px solid #F44336;
    }
    
    /* Modalità compatta per risposte */
    .compact-response {
        max-height: 150px;
        overflow: hidden;
        position: relative;
    }
    .compact-response::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 50px;
        background: linear-gradient(transparent, #1e1e1e);
    }
    
    /* Ottimizzazioni mobile */
    @media (max-width: 768px) {
        .bottom-nav {
            display: flex;
            align-items: center;
        }
        
        .sidebar {
            display: none;
        }
        
        .main .block-container {
            padding: 1rem 1rem 4rem 1rem;
        }
        
        .stButton>button {
            width: 100%;
        }
        
        .word-counter {
            font-size: 0.7em;
            padding: 3px 6px;
        }
    }
</style>
""", unsafe_allow_html=True)

# Inizializzazione stati
if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()
if 'compact_mode' not in st.session_state:
    st.session_state.compact_mode = False

# Client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')

def get_assistant_response(quote, question):
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id
    
    formatted_question = f"""PUNTO DI RIFERIMENTO: "{quote}"
    
DOMANDA: {question}"""
    
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
            return "Mi dispiace, c'è stato un errore nel processare la tua richiesta."
        time.sleep(1)
    
    messages = client.beta.threads.messages.list(
        thread_id=st.session_state.thread_id
    )
    
    return messages.data[0].content[0].text.value

# Layout principale
st.title("📚 Infinite Jest Assistant")

st.markdown("""
    👋 Un supporto (emotivo) alla lettura di **Infinite Jest** di David Foster Wallace, con meno bestemmie.

    **Il problema:** Il libro non ha una numerazione standard dei capitoli o delle pagine.
    
    **La soluzione:** Inserisci una frase significativa dell'ultimo passaggio letto.
    
    **Perché?** Per poterti dare risposte pertinenti ed evitare spoiler involontari.
""")

# Sidebar (desktop only)
with st.sidebar:
    with st.expander("📊 Statistiche", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Domande", st.session_state.total_questions)
        with col2:
            time_elapsed = datetime.now() - st.session_state.session_start
            st.metric("Minuti", f"{time_elapsed.seconds//60}")
    
    if st.button("🔄 Ricomincia"):
        st.session_state.clear()
        st.rerun()

# Toggle visualizzazione compatta
st.checkbox('Visualizzazione compatta', key='compact_mode', value=st.session_state.compact_mode)

# Area principale
quote = st.text_area(
    "Citazione dall'ultimo passaggio letto (minimo 10 parole):",
    height=100,
    help="Inserisci una frase che ti aiuti a ricordare dove sei arrivato"
)

if quote:
    word_count = len(quote.split())
    is_valid = word_count >= 10
    if not is_valid:
        st.warning(f"⚠️ Servono almeno 10 parole ({word_count}/10)")
    else:
        st.success("✅ Citazione valida!")

question = st.text_input(
    "La tua domanda:",
    help="Cosa vorresti sapere su personaggi, temi, eventi o note?"
)

if st.button("📤 Invia", disabled=not (quote and len(quote.split()) >= 10 and question)):
    with st.spinner("🤔 Ci penso..."):
        response = get_assistant_response(quote, question)
        st.session_state.total_questions += 1
        
        st.session_state.messages.append({
            "role": "user",
            "content": {"quote": quote, "question": question}
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

# Cronologia
if st.session_state.messages:
    st.markdown("### 📚 Cronologia")
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown("**Tu:**")
            with st.expander("Mostra citazione"):
                st.markdown(f'<div class="quote-box quote-valid">{msg["content"]["quote"]}</div>', 
                    unsafe_allow_html=True)
            st.markdown(msg["content"]["question"])
        else:
            st.markdown("**Assistant:**")
            if "[SPOILER ALERT" in msg["content"]:
                safe_content, spoiler_content = msg["content"].split("[SPOILER ALERT", 1)
                st.markdown(safe_content)
                with st.expander("👀 Spoiler"):
                    st.markdown(f'<div class="spoiler">{spoiler_content}</div>', 
                        unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])
        st.markdown("---")

# Bottom navigation ottimizzata per mobile
st.markdown("""
<div class="bottom-nav">
    <button onclick="window.scrollTo(0,0)">⬆️</button>
    <button onclick="document.querySelector('.compact-mode').click()">📱</button>
</div>
""", unsafe_allow_html=True)
