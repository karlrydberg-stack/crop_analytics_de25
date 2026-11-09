from fastapi import FastAPI
import pandas as pd
from pathlib import Path


app = FastAPI()

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "crop_data_clean.csv"

def load_data() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH) 


@app.get("/crops")
def get_crops():
    tidy = load_data()
    return tidy.astype(object).where(tidy.notna(), None).to_dict(orient="records")


