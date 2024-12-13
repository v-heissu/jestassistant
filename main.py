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
    initial_sidebar_state="expanded"
)

# Stile CSS personalizzato
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
    
    /* ASCII Art */
    .dfw-ascii {
        font-family: monospace;
        white-space: pre;
        font-size: 10px;
        line-height: 1.2;
        color: #4CAF50;
        text-align: left;
        margin-bottom: 20px;
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
    
    /* Spoiler */
    .spoiler {
        background-color: #2d2d2d;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    
    /* Badge contatore parole */
    .word-counter {
        position: absolute;
        right: 10px;
        bottom: 10px;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.8em;
    }
    
    /* Tema scuro personalizzato */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border: none;
        border-radius: 20px;
        padding: 10px 25px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 0 15px rgba(76, 175, 80, 0.4);
    }
    
    /* Header decorativo */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 20px;
        background-color: #2d2d2d;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    
    /* Timeline visiva */
    .timeline {
        margin: 20px 0;
        padding: 10px;
        background: linear-gradient(90deg, #4CAF50 var(--progress), #2d2d2d var(--progress));
        border-radius: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ASCII Art migliorato di DFW
dfw_ascii = """
    ⠀⠀⠀⠀⠀⣀⣤⣴⣶⣶⣶⣶⣦⣤⣀⠀⠀⠀⠀⠀
    ⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀⠀⠀
    ⠀⣴⣿⣿⣿⣿⣿⣿⠟⠛⠛⠻⣿⣿⣿⣿⣿⣿⣦⠀
    ⣼⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠈⢻⣿⣿⣿⣿⣿⣧
    ⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⣿⣿⣿
    ⣿⣿⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿
    ⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿
    ⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⣿⣿⣿⣿
    ⢿⣿⣿⣿⡄⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⡿
    ⠈⢿⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⡿⠁
    ⠀⠀⠻⣿⣿⣿⣷⣄⡀⠀⢀⣠⣾⣿⣿⣿⡿⠟⠁⠀
    ⠀⠀⠀⠈⠙⠛⠿⢿⣿⣿⣿⡿⠿⠛⠋⠁⠀⠀⠀⠀
"""

# Inizializzazione client e variabili di sessione
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')

if 'thread_id' not in st.session_state:
    st.session_state.thread_id = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'total_questions' not in st.session_state:
    st.session_state.total_questions = 0
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.now()

# Funzione per ottenere la risposta dall'assistant
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
col1, col2 = st.columns([3, 1])
with col1:
    st.title("🎭 Infinite Jest Assistant")
with col2:
    st.markdown(f'<div class="dfw-ascii">{dfw_ascii}</div>', unsafe_allow_html=True)

# Sidebar con statistiche e info
with st.sidebar:
    st.header("📊 Statistiche Sessione")
    st.metric("Domande Poste", st.session_state.total_questions)
    time_elapsed = datetime.now() - st.session_state.session_start
    st.metric("Tempo Sessione", f"{time_elapsed.seconds//60} minuti")
    
    if st.button("🔄 Nuova Sessione"):
        st.session_state.thread_id = None
        st.session_state.messages = []
        st.session_state.total_questions = 0
        st.session_state.session_start = datetime.now()
        st.rerun()
    
    st.markdown("---")
    st.markdown("""
    ### 💡 Tips
    - Usa citazioni significative
    - Sii specifico nelle domande
    - Esplora i collegamenti
    """)

# Area principale
st.markdown("""
    Per evitare spoiler e fornirti risposte precise, ho bisogno di sapere esattamente a che punto della lettura sei 
    arrivato: Foster Wallace è un dito al culo e non ha numeri di capitoli o di pagina, quindi dobbiamo farci furbi. 
    Per favore, copia e incolla una frase significativa dell'ultimo passaggio che hai letto (almeno 10 parole). 
    Questo mi aiuterà a contestualizzare meglio la tua posizione nel libro e a darti risposte pertinenti.
""")

# Input con validazione e contatore parole
quote = st.text_area(
    "Copia una frase significativa dell'ultimo passaggio letto:",
    help="La frase deve essere di almeno 10 parole",
    height=100
)

word_count = len(quote.split()) if quote else 0
if quote:
    is_valid = word_count >= 10
    quote_class = "quote-valid" if is_valid else "quote-invalid"
    st.markdown(
        f'<div class="quote-box {quote_class}">{quote}'
        f'<span class="word-counter">{word_count} parole</span></div>',
        unsafe_allow_html=True
    )
    if not is_valid:
        st.warning("⚠️ La citazione deve contenere almeno 10 parole")
    else:
        st.success("✅ Citazione valida!")

question = st.text_input(
    "La tua domanda:",
    help="Cosa vorresti sapere su personaggi, temi, eventi o note fino al punto che hai raggiunto?"
)

# Gestione invio domanda
if st.button("📤 Invia domanda", disabled=not (quote and word_count >= 10 and question)):
    with st.spinner("🤔 Elaboro la risposta..."):
        response = get_assistant_response(quote, question)
        st.session_state.total_questions += 1
        
        # Salva nella cronologia
        st.session_state.messages.append({
            "role": "user",
            "content": {"quote": quote, "question": question}
        })
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })

# Visualizzazione cronologia
if st.session_state.messages:
    st.markdown("### 📚 Cronologia")
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown("**Tu:**")
            with st.expander("Mostra citazione di riferimento"):
                st.markdown(f'<div class="quote-box quote-valid">{msg["content"]["quote"]}</div>', 
                    unsafe_allow_html=True)
            st.markdown(msg["content"]["question"])
        else:
            st.markdown("**Assistant:**")
            if "[SPOILER ALERT" in msg["content"]:
                safe_content, spoiler_content = msg["content"].split("[SPOILER ALERT", 1)
                st.markdown(safe_content)
                with st.expander("👀 Mostra spoiler"):
                    st.markdown(f'<div class="spoiler">{spoiler_content}</div>', 
                        unsafe_allow_html=True)
            else:
                st.markdown(msg["content"])
        st.markdown("---")
