import pandas as pd
from sqlalchemy import inspect, text
import re

from backend.database import engine


def extract_data():
    """Extract raw crop data from PostgreSQL staging."""

    query = text("""
        SELECT *
        FROM staging.crops;
    """)

    with engine.connect() as connection:
        df = pd.read_sql_query(query, connection)

    print(f"Extracted {len(df)} rows and {len(df.columns)} columns.")

    return df


def clean_data(df):

    """Apply cleaning and preparation steps."""

    # -----------------------------------------
    # 1. Initial inspection
    # -----------------------------------------

    print("\nInitial data overview:")
    print(df.info())

    print("\nMissing values:")
    print(df.isna().sum())

    crop_replace = {
    "H�stvete": "Höstvete",
    "V�rvete": "Vårvete",
    "R�g": "Råg",
    "H�stkorn": "Höstkorn",
    "V�rkorn": "Vårkorn",
    "Havre": "Havre",
    "R�gvete": "Rågvete",
    "H�str�gvete": "Höstrågvete",
    "V�rr�gvete": "Vårrågvete",
    "Blands�d": "Blandsäd",
    "Majs": "Majs",
    "Spannm�l totalt": "Spannmål totalt",
    "�rter": "Ärter",
    "�kerb�nor": "Åkerbönor",
    "H�straps": "Höstraps",
    "V�rraps": "Vårraps",
    "H�strybs": "Höstrybs",
    "V�rrybs": "Vårrybs",
    "Str�s�desgr�dor (exkl. majs) till gr�nfoder": "Stråsädesgrödor (exkl. majs) till grönfoder",
    "Majs till gr�nfoder": "Majs till grönfoder",
    "Andra ett�riga gr�dor till gr�nfoder": "Andra ettåriga grödor till grönfoder",
    "Oljelin": "Oljelin",
    "Matpotatis": "Matpotatis",
    "Potatis f�r st�rkelse": "Potatis för stärkelse",
    "Sockerbetor": "Sockerbetor",
    "Sl�ttervall, f�rsta sk�rd": "Slåttervall, första skörd",
    "Sl�ttervall, �terv�xt": "Slåttervall, återväxt",
    "Sl�ttervall, total vallsk�rd": "Slåttervall, total vallskörd",
    }

    region_replace = {
    "00": "Riket",
    "01": "Stockholm",
    "03": "Uppsala",
    "04": "Södermanland",
    "05": "Östergötland",
    "06": "Jönköping",
    "07": "Kronoberg",
    "08": "Kalmar",
    "09": "Gotland",
    "10": "Blekinge",
    "11": "Kristianstad",
    "12": "Skåne",
    "122": "Malmöhus",
    "13": "Halland",
    "14": "Västra Götaland",
    "141": "Göteborg och Bohus",
    "15": "Älvsborg",
    "16": "Skaraborg",
    "17": "Värmland",
    "18": "Örebro",
    "19": "Västmanland",
    "20": "Dalarna",
    "21": "Gävleborg",
    "22": "Västernorrland",
    "23": "Jämtland",
    "24": "Västerbotten",
    "25": "Norrbotten",
    }   


    
    # Work on a copy rather than modifying the extracted DataFrame
    df = df.copy()

    df = df.rename(columns={
    "l_n": "Län",
    "gr_da": "Gröda",
    "variabel": "Variabel",
    "tabelluppgift": "Tabelluppgift"
    })
    # -----------------------------------------
    # 2. Standardise crop and county names
    # -----------------------------------------

    df["Gröda"] = df["Gröda"].replace(crop_replace)

    # Extract county code
    df["Län_kod"] = (
        df["Län"]
        .astype("string")
        .str.extract(r"^(\d+)", expand=False)
    )

    # Map county code to readable county name
    df["Län"] = df["Län_kod"].map(region_replace)

    # Remove unused metadata
    df = df.drop(columns=["Tabelluppgift"])

    # Check for county codes without a mapping
    unmapped = df.loc[df["Län"].isna(), "Län_kod"].unique()

    if len(unmapped) > 0:
        raise ValueError(f"Unmapped county codes: {unmapped}")

    # -----------------------------------------
    # 3. Standardise measurement names
    # -----------------------------------------

    variable = df["Variabel"].astype("string").str.strip()

    is_area = variable.str.startswith("Areal", na=False)
    is_harvest = variable.str.startswith("Totalsk", na=False)

    if not (is_area | is_harvest).all():
        unknown = variable.loc[~(is_area | is_harvest)].unique()
        raise ValueError(f"Unexpected measurement types: {unknown}")

    df["Variabel"] = pd.NA
    df.loc[is_area, "Variabel"] = "area_ha"
    df.loc[is_harvest, "Variabel"] = "harvest_ton"

    # -----------------------------------------
    # 4. Identify annual columns
    # -----------------------------------------

    year_columns = [
    col for col in df.columns
    if re.fullmatch(r"_\d{4}", str(col))
    ]

    if not year_columns:
        raise ValueError("No year columns found.")

    # -----------------------------------------
    # 5. Wide format -> long format
    # -----------------------------------------

    long_df = df.melt(
        id_vars=[
            "Län_kod",
            "Län",
            "Gröda",
            "Variabel"
        ],
        value_vars=year_columns,
        var_name="År",
        value_name="value"
    )

    # Convert measurement values to numeric
    # "." represents missing values in the source
    long_df["value"] = pd.to_numeric(
        long_df["value"].replace(".", pd.NA),
        errors="coerce"
    )

    # -----------------------------------------
    # 6. Check for duplicate measurements
    # -----------------------------------------

    duplicate_columns = [
        "Län_kod",
        "Gröda",
        "År",
        "Variabel"
    ]

    duplicates = long_df.duplicated(
        subset=duplicate_columns,
        keep=False
    )

    if duplicates.any():
        raise ValueError(
            "Duplicate measurements found:\n"
            f"{long_df.loc[duplicates].head(10)}"
        )

    # -----------------------------------------
    # 7. Long format -> analytical format
    # -----------------------------------------

    tidy = long_df.pivot(
        index=["Län_kod", "Län", "Gröda", "År"],
        columns="Variabel",
        values="value"
    ).reset_index()

    tidy.columns.name = None

    # -----------------------------------------
    # 8. Convert year to integer
    # -----------------------------------------

    tidy["År"] = pd.to_numeric(
    tidy["År"].astype("string").str.lstrip("_"),
    errors="raise"
    ).astype("int64")

    # -----------------------------------------
    # 9. Calculate yield
    # -----------------------------------------

    tidy["yield_ton_ha"] = (
        tidy["harvest_ton"] /
        tidy["area_ha"].where(tidy["area_ha"] > 0)
    )

    # -----------------------------------------
    # 10. Validation
    # -----------------------------------------

    print("\nCleaned data overview:")
    tidy.info()

    print("\nMissing values:")
    print(tidy.isna().sum())

    print("\nFinal shape:", tidy.shape)

    print("\nYear range:")
    print(tidy["År"].min(), "-", tidy["År"].max())

    print("\nDuplicate county/crop/year combinations:")
    print(
        tidy.duplicated(
            subset=["Län_kod", "Gröda", "År"]
        ).sum()
    )

    return tidy

# --- Changed few things, see below ---
# def load_data(df):
#     """Replace the contents of cleaned.crops without dropping the table."""

#     with engine.begin() as connection:

#         # Remove existing rows while preserving the table and dependent views
#         connection.execute(
#             text("TRUNCATE TABLE cleaned.crops")
#         )

#         # Insert the newly cleaned data
#         df.to_sql(
#             name="crops",
#             schema="cleaned",
#             con=connection,
#             if_exists="append",
#             index=False,
#             chunksize=1000,
#             method="multi"
#         )

#     print(f"Loaded {len(df)} rows into cleaned.crops.")

def load_data(df):
    """Replace the contents of cleaned.crops without dropping the table."""

    with engine.begin() as connection:

        # Create the schema the first time the pipeline runs
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS cleaned"))

        # Empty the table if it already exists (keeps dependent dbt views working)
        if inspect(connection).has_table("crops", schema="cleaned"):
            connection.execute(text("TRUNCATE TABLE cleaned.crops"))

        # Insert the cleaned data (creates the table on the first run)
        df.to_sql(
            name="crops",
            schema="cleaned",
            con=connection,
            if_exists="append",
            index=False,
            chunksize=1000,
            method="multi"
        )

    print(f"Loaded {len(df)} rows into cleaned.crops.")


def main():
    df = extract_data()
    cleaned_df = clean_data(df)
    load_data(cleaned_df)


if __name__ == "__main__":
    main()