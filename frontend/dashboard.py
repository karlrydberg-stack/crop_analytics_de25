# uv run streamlit run frontend/dashboard.py

import os
import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


st.title("🌾 Crop Analytics – Jordbruksverket 1965–2025")

response = requests.get(f"{BACKEND_URL}/crops", timeout=30)
df = pd.DataFrame(response.json())

st.dataframe(df.fillna("saknas"))


st.markdown("---")
st.caption(
    "📊 **Data Source:** [Jordbruksverket (Swedish Board of Agriculture)](https://jordbruksverket.se) | Crop Analytics DE25"
)