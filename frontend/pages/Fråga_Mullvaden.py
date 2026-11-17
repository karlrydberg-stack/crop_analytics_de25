# --- Chat page should appear in the sidebar next to the dashboard ---
# --- Command: uv run --env-file .env streamlit run frontend/dashboard.py

import streamlit as st
from pydantic_ai.exceptions import FallbackExceptionGroup, ModelHTTPError, UsageLimitExceeded
from pydantic_ai.usage import UsageLimits
import asyncio
from concurrent.futures import ThreadPoolExecutor

from chatbot_agent import ChatDeps, build_agent, create_chatbot_engine

# --- Protection suggested by LLM to stay into free quota with 20 questions per session --- 
MAX_QUESTIONS_PER_SESSION = 20   
# --- With 6 as max Gemini calls for one question ---
LIMITS = UsageLimits(request_limit=6)  

st.title("🌾 Låt oss gräva ner sig i datan / Let's dig into the data!")
st.caption(
    "Fråga om svenska grödor för perioden 1965–2025 / Ask about Swedish crops for the period 1965–2025"
)


@st.cache_resource
def get_agent():
    return build_agent()


@st.cache_resource
def get_engine():
    return create_chatbot_engine()


def ask_agent(question, deps):
    """Run the agent in its own thread with its own event loop
    (Streamlit may already have a loop running in the page thread)."""
    # Read Streamlit things here, in the page thread, not inside the new thread
    agent = get_agent()
    history = st.session_state.history

    def _run():
        return asyncio.run(
            agent.run(
                question,
                deps=deps,
                message_history=history,
                usage_limits=LIMITS,
            )
        )

    with ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_run).result()






# --- Chat status ---
if "chat" not in st.session_state:
# --- what we show: dicts with role / content / sql ---
    st.session_state.chat = []      
# --- what the model remembers --- 
    st.session_state.history = []   
    st.session_state.asked = 0

# --- Show the conversation ---
for msg in st.session_state.chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sql"):
            with st.expander("SQL"):
                for q in msg["sql"]:
                    st.code(q, language="sql")

question = st.chat_input("Skriv din fråga… / Type your question…")

if question:
    st.session_state.chat.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        sql_used: list[str] = []
        if st.session_state.asked >= MAX_QUESTIONS_PER_SESSION:
            answer = "You have reached the question limit for this session. Reload the page later."
        else:
            deps = ChatDeps(engine=get_engine())
            try:
                with st.spinner("Thinking…"):
                    result = ask_agent(question, deps)
                    
                answer = result.output
                st.session_state.history = result.all_messages()
                st.session_state.asked += 1
            except ModelHTTPError as exc:
                if exc.status_code == 429:
                    answer = "The chatbot is busy (free quota reached). Try again in a minute."
                else:
                    answer = f"The language model returned an error ({exc.status_code}). Try again."
            except UsageLimitExceeded:
                answer = "That question needed too many steps. Try asking it more simply."
            except FallbackExceptionGroup:
                answer = "The language models are busy right now. Try again in a minute."
            sql_used = deps.queries if "deps" in locals() else []
            

        st.markdown(answer)
        if sql_used:
            with st.expander("SQL"):
                for q in sql_used:
                    st.code(q, language="sql")

    st.session_state.chat.append({"role": "assistant", "content": answer, "sql": sql_used})