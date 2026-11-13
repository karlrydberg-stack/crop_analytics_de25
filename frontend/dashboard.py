# uv run streamlit run frontend/dashboard.py

import os
import pandas as pd
import requests
import streamlit as st
import plotly.express as px


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


st.title("🌾 Crop Analytics – Jordbruksverket 1965–2025")

response = requests.get(f"{BACKEND_URL}/crops", timeout=30)
df = pd.DataFrame(response.json())

st.dataframe(df.fillna("saknas"))


st.markdown("---")
st.caption(
    "📊 **Data Source:** [Jordbruksverket (Swedish Board of Agriculture)](https://jordbruksverket.se) | Crop Analytics DE25"
)

# --- Test to compare in a chart line the evolution of each crop when available ---
# --- Question: how much does Sweden harvest?

TOTALS = ["Spannmål totalt", "Slåttervall, total vallskörd"]


GROUPS = {
    "Spannmål": ["Höstvete", "Vårvete", "Råg", "Höstkorn", "Vårkorn", "Havre",
                 "Rågvete", "Höstrågvete", "Vårrågvete", "Blandsäd", "Majs"],
    "Oljeväxter": ["Höstraps", "Vårraps", "Höstrybs", "Vårrybs", "Oljelin"],
    "Baljväxter": ["Ärter", "Åkerbönor"],
    "Rotfrukter": ["Matpotatis", "Potatis för stärkelse", "Sockerbetor"],
    "Vall och foder": ["Slåttervall, första skörd", "Slåttervall, återväxt",
                       "Stråsädesgrödor (exkl. majs) till grönfoder",
                       "Majs till grönfoder", "Andra ettåriga grödor till grönfoder"],
}

st.header("Grödor – utveckling sedan 1965")

# --- National level only, no totals ---
riket = df[(df["Län"] == "Riket") & (~df["Gröda"].isin(TOTALS))]

group = st.radio("Grupp", ["Alla"] + list(GROUPS), horizontal=True)
if group != "Alla":
    riket = riket[riket["Gröda"].isin(GROUPS[group])]

view = st.radio("Visa", ["Skörd (ton)", "Index (första år = 100)"], horizontal=True)

plot = riket.dropna(subset=["harvest_ton"]).sort_values("År")
y = "harvest_ton"
if view.startswith("Index"):
    first = plot.groupby("Gröda")["harvest_ton"].transform("first")
    plot = plot.assign(index=plot["harvest_ton"] / first * 100)
    y = "index"

fig = px.line(plot, x="År", y=y, color="Gröda",
              labels={"harvest_ton": "Skörd (ton)", "index": "Index", "År": ""})
fig.update_layout(legend_title_text="", hovermode="x unified")
st.plotly_chart(fig, width="stretch")

# --- Other question that we answer ---
st.header("De sista 20: Höstsådda grödor tar över från vårsådda")

TOTALS = ["Spannmål totalt", "Slåttervall, total vallskörd", "Slåttervall, återväxt"]

area = df[(df["Län"] == "Riket") & (~df["Gröda"].isin(TOTALS))].dropna(subset=["area_ha"])
area = area[~((area["Gröda"] == "Rågvete") & (area["År"] >= 2015))]

# --- It is the average of the 3 years ---
start = area[area["År"].between(2002, 2004)].groupby("Gröda")["area_ha"].mean()
end = area[area["År"].between(2023, 2025)].groupby("Gröda")["area_ha"].mean()

# --- and drops crops that don’t exist in both periods (sugar beet and the fodder crops start later) ---
# from biggest loss to biggest gain
change = (end - start).dropna().round(-1).sort_values().reset_index(name="diff_ha")
change["Riktning"] = change["diff_ha"].map(lambda v: "Ökning" if v > 0 else "Minskning")

fig = px.bar(
    change, x="diff_ha", y="Gröda", orientation="h", color="Riktning",
    color_discrete_map={"Ökning": "#2a78d6", "Minskning": "#eb6834"},
    labels={"diff_ha": "Förändring i areal (hektar)", "Gröda": ""},
)
fig.update_traces(hovertemplate="%{y}: %{x:+,.0f} ha<extra></extra>")
fig.update_layout(legend_title_text="", height=600)
st.plotly_chart(fig, width="stretch")
st.caption("Genomsnittlig areal 2023–2025 jämfört med 2002–2004, riket.")