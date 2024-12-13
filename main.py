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

# JavaScript per swipe e interazioni touch
swipe_js = """
<script src="https://hammerjs.github.io/dist/hammer.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    const mainContent = document.querySelector('.main');
    const hammer = new Hammer(mainContent);
    
    hammer.on('swipeleft swiperight', function(e) {
        const views = ['new_question', 'history'];
        const currentView = window.sessionStorage.getItem('current_view') || 'new_question';
        const currentIndex = views.indexOf(currentView);
        
        if (e.type === 'swipeleft' && currentIndex < views.length - 1) {
            window.sessionStorage.setItem('current_view', views[currentIndex + 1]);
        } else if (e.type === 'swiperight' && currentIndex > 0) {
            window.sessionStorage.setItem('current_view', views[currentIndex - 1]);
        }
        window.location.reload();
    });
});
</script>
"""

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
    
    /* Bottom Navigation Bar */
    .bottom-nav {
        display: none;
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: #1e1e1e;
        box-shadow: 0 -2px 10px rgba(0,0,0,0.2);
        z-index: 1000;
        padding: 10px;
    }
    
    /* Box citazione e altri stili esistenti... */
    .quote-box {
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        font-family: 'Courier New', monospace;
        transition: all 0.3s ease;
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
            justify-content: space-around;
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
    }
</style>

<!-- Bottom Navigation HTML -->
<div class="bottom-nav">
    <button onclick="setView('new_question')" class="nav-btn">
        📝 Nuova
    </button>
    <button onclick="setView('history')" class="nav-btn">
        📚 Storia
    </button>
    <button onclick="document.querySelector('.compact-mode').click()" class="nav-btn">
        📱 Compatta
    </button>
</div>
""", unsafe_allow_html=True)

# Inject swipe JavaScript
st.components.v1.html(swipe_js, height=0)

# Inizializzazione stato
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
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'new_question'

# Client OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
assistant_id = os.getenv('ASSISTANT_ID')

# Funzioni esistenti...
def get_assistant_response(quote, question):
    # ... [il codice della funzione rimane invariato]
    pass

# Layout principale
st.title("🎭 Infinite Jest Assistant")

# Sidebar (visibile solo su desktop)
with st.sidebar:
    with st.expander("📊 Statistiche", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Domande", st.session_state.total_questions)
        with col2:
            time_elapsed = datetime.now() - st.session_state.session_start
            st.metric("Minuti", f"{time_elapsed.seconds//60}")
    
    if st.button("🔄 Reset"):
        st.session_state.clear()
        st.rerun()

# Toggle modalità compatta
st.checkbox('Modalità compatta', key='compact_mode', value=st.session_state.compact_mode)

# Main content area basata sulla vista corrente
if st.session_state.current_view == 'new_question':
    st.markdown("""
    Benvenuto nell'assistente alla lettura di **Infinite Jest**!

    **Il problema:** Foster Wallace è un dito al culo e non ha numeri di capitoli o di pagina.
    
    **La soluzione:** Copia e incolla una frase significativa dell'ultimo passaggio che hai letto.
    """)
    
    quote = st.text_area(
        "Citazione (min 10 parole):",
        height=100
    )
    
    if quote:
        word_count = len(quote.split())
        is_valid = word_count >= 10
        if not is_valid:
            st.warning(f"⚠️ Servono almeno 10 parole ({word_count}/10)")
        else:
            st.success("✅ Citazione valida!")
    
    question = st.text_input("La tua domanda:")
    
    if st.button("📤 Invia", disabled=not (quote and len(quote.split()) >= 10 and question)):
        # ... [logica invio domanda invariata]
        pass

else:  # Vista cronologia
    if st.session_state.messages:
        for msg in reversed(st.session_state.messages):
            with st.expander(
                f"Q: {msg['content']['question'][:30]}..." if msg['role'] == 'user' else "R: Risposta",
                expanded=not st.session_state.compact_mode
            ):
                # ... [visualizzazione messaggi con gestione compact_mode]
                if msg['role'] == 'user':
                    st.markdown(f"**Citazione:** {msg['content']['quote']}")
                    st.markdown(f"**Domanda:** {msg['content']['question']}")
                else:
                    content_class = "compact-response" if st.session_state.compact_mode else ""
                    st.markdown(f'<div class="{content_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# Gestione swipe e bottom navigation
st.components.v1.html("""
<script>
function setView(view) {
    window.sessionStorage.setItem('current_view', view);
    window.location.reload();
}
</script>
""", height=0)
