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

st.title("🎭 Infinite Jest Assistant")

st.markdown("""
    Benvenuto nell'assistente alla lettura di Infinite Jest.
    
    Per evitare spoiler e fornirti risposte precise, ho bisogno di sapere esattamente a che punto della lettura sei arrivato: Foster Wallace è un dito al culo e non ha numeri di capitoli o di pagina, quindi dobbiamo farci furbi.
    Per favore, copia e incolla una frase significativa dell'ultimo passaggio che hai letto (almeno 10 parole).
    Questo mi aiuterà a contestualizzare meglio la tua posizione nel libro e a darti risposte pertinenti.
""")

# Input utente
anchor_text = st.text_area(
    "Copia una frase significativa dell'ultimo passaggio letto:",
    help="Incolla qui una frase di almeno 10 parole dall'ultimo passaggio che hai letto. Questo mi aiuterà a capire esattamente dove ti trovi nel libro.",
    max_chars=500
)

question = st.text_input(
    "La tua domanda:",
    help="Cosa vorresti sapere su personaggi, temi, eventi o note fino al punto che hai raggiunto?"
)

# Validazione input
def validate_anchor(text):
    words = text.split()
    return len(words) >= 10

if st.button("Invia domanda"):
    if not anchor_text:
        st.error("Per favore, inserisci una frase dal testo per aiutarmi a capire dove ti trovi nella lettura.")
    elif not validate_anchor(anchor_text):
        st.error("La frase deve essere di almeno 10 parole per essere sufficientemente precisa.")
    elif not question:
        st.error("Per favore, inserisci una domanda.")
    else:
        with st.spinner("Elaboro la risposta..."):
            # Formato la richiesta includendo l'ancora testuale
            formatted_question = f"""ANCORA DI RIFERIMENTO NEL TESTO: "{anchor_text}"
            
DOMANDA: {question}"""
            
            if not st.session_state.thread_id:
                thread = client.beta.threads.create()
                st.session_state.thread_id = thread.id
            
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
                    st.error("Mi dispiace, c'è stato un errore nel processare la tua richiesta.")
                    break
                time.sleep(1)
            
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            
            response = messages.data[0].content[0].text.value
            
            # Salva nella cronologia
            st.session_state.messages.append({
                "role": "user",
                "content": formatted_question
            })
            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

# Visualizzazione cronologia
if st.session_state.messages:
    st.markdown("### Cronologia")
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "user":
            st.markdown("**Tu:**")
            st.markdown(msg["content"])
        else:
            st.markdown("**Assistant:**")
            st.markdown(msg["content"])
        st.markdown("---")
