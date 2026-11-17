# --- Chatbot agent should answer questions about the Swedish crop data ---

import os
from dataclasses import dataclass, field

import pandas as pd
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from sqlalchemy import URL, create_engine, text
from pydantic_ai.models.fallback import FallbackModel       # Added for backup if model is too busy, error 503

MAX_ROWS = 200  


# --- Database (read-only user, 5 seconds statement_timeout set in setup_db.py) ---

def create_chatbot_engine():
    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("CHATBOT_DB_USER", "chatbot_reader"),
# --- Docker/Azure use CHATBOT_DB_PASSWORD, local .env has CHATBOT_READER_PASSWORD ---
        password=os.getenv("CHATBOT_DB_PASSWORD") or os.getenv("CHATBOT_READER_PASSWORD"),
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
        query={"sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")},
    )
    return create_engine(url)


@dataclass
class ChatDeps:
    """What the agent's tool gets access to during one question."""
    engine: object
    queries: list[str] = field(default_factory=list)  # SQL run, shown in the UI


# --- Instructions ---
# --- Helped from LLM to be as precise as possible ---
INSTRUCTIONS = """
You are an expert in Swedish crop statistics from Jordbruksverket (1965-2025).
Answer ONLY from the database, using the run_sql tool. Never invent numbers.

The only table is chatbot.mart_chatbot, one row per place, crop and year:
- level        text     'national' (Sweden as a whole) or 'county'
- county       text     county name in Swedish; for level='national' it is 'Riket'
- region       text     group of counties (NULL for national rows)
- crop         text     crop name in Swedish, e.g. 'Höstvete', 'Vårkorn', 'Havre', 'Matpotatis'
- crop_group   text     'Spannmål', 'Oljeväxter', 'Baljväxter', 'Rotfrukter', 'Vall och foder'
- year         integer
- area_ha      numeric  cultivated area in hectares (can be NULL)
- harvest_ton  numeric  total harvest in tonnes (can be NULL)
- yield_ton_ha numeric  yield in tonnes per hectare (can be NULL)

Rules:
- Total rows are already removed, so summing crops does not double count.
- For Sweden as a whole, use level = 'national'. Do NOT sum the counties.
- For county comparisons, use level = 'county'.
- If you are unsure of an exact crop or county name, first run a query like
  SELECT DISTINCT crop FROM chatbot.mart_chatbot to check.
- Write one PostgreSQL SELECT query at a time. Aggregate in SQL; don't fetch raw rows you don't need.
- If the data has no answer (missing years, NULL values), say so plainly.

Answer in the same language as the question (Swedish or English).
Keep answers short: the key numbers with units (ha, ton, ton/ha), and the year(s).
"""


# --- The agent ---
# --- Flash 2.5 would be depracated in December 2026 ---
def build_agent() -> Agent[ChatDeps, str]:
    provider = GoogleProvider(api_key=os.environ["GEMINI_API_KEY"])
        # If the main model is busy (503) or out of quota (429), try the lighter one.
    model = FallbackModel(
        GoogleModel(os.getenv("GEMINI_MODEL", "gemini-3.5-flash"), provider=provider),
        GoogleModel(os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.5-flash-lite"), provider=provider),
    )
    agent = Agent(model, deps_type=ChatDeps, instructions=INSTRUCTIONS)

    @agent.tool
    def run_sql(ctx: RunContext[ChatDeps], query: str) -> str:
        """Run one read-only SELECT query on chatbot.mart_chatbot and return the rows as CSV."""
        sql = query.strip().rstrip(";")
        if not sql.lower().startswith(("select", "with")):
            return "Error: only SELECT queries are allowed."
        if ";" in sql:
            return "Error: only one query at a time."

        ctx.deps.queries.append(sql)
# --- Wrapping guarantees a single SELECT and caps the number of rows ---
        wrapped = f"SELECT * FROM ({sql}) AS q LIMIT {MAX_ROWS}"
        try:
            with ctx.deps.engine.connect() as conn:
                df = pd.read_sql(text(wrapped), conn)
        except Exception as exc:  # bad SQL, timeout, ... -> let the model fix it
            return f"SQL error: {exc.__class__.__name__}: {str(exc).splitlines()[0]}"

        if df.empty:
            return "The query returned no rows."
        return df.to_csv(index=False)

    return agent