import os
from pathlib import Path
from urllib.parse import quote_plus

import dlt
import pandas as pd
from dotenv import load_dotenv


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CSV_PATH = PROJECT_ROOT / "data" / "crop_data_1965_2025.csv"

# Load environment variables
load_dotenv(PROJECT_ROOT / ".env")


def load_crop_data():

    # Read source CSV
    df = pd.read_csv(
        CSV_PATH,
        encoding="utf-8",
        sep=","
    )

    print(f"Source rows: {len(df)}")
    print(f"Source columns: {len(df.columns)}")

    # Convert DataFrame into records for dlt
    return df.to_dict(orient="records")


def run_pipeline():

    # PostgreSQL connection string
    connection_string = (
        f"postgresql://"
        f"{quote_plus(os.getenv('POSTGRES_USER'))}:"
        f"{quote_plus(os.getenv('POSTGRES_PASSWORD'))}@"
        f"{os.getenv('POSTGRES_HOST')}:"
        f"{os.getenv('POSTGRES_PORT')}/"
        f"{os.getenv('POSTGRES_DB')}"
    )

    # Define dlt pipeline
    pipeline = dlt.pipeline(
        pipeline_name="crop_analytics",
        destination=dlt.destinations.postgres(
            credentials=connection_string
        ),
        dataset_name="staging"
    )

    # Define resource
    crops = dlt.resource(
        load_crop_data(),
        name="crops",
        write_disposition="replace"
    )

    # Execute pipeline
    load_info = pipeline.run(crops)

    print("\nPipeline completed!")
    print(load_info)

    return load_info


if __name__ == "__main__":
    run_pipeline()