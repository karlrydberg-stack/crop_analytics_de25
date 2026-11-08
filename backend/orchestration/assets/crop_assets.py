
import shutil
import subprocess
from pathlib import Path

from dagster import asset

from backend.ingestion.pipeline import run_pipeline
from backend.transformations.clean_crops import main as clean_crops


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DBT_PROJECT_DIR = PROJECT_ROOT / "crop_analytics_dbt"


@asset
def raw_crops(context):
    """Ingest the source CSV into PostgreSQL staging."""

    context.log.info("Starting dlt ingestion.")

    load_info = run_pipeline()

    context.log.info("dlt ingestion completed.")
    context.log.info(str(load_info))


@asset
def cleaned_crops(context, raw_crops):
    """Clean staging data and load it into cleaned.crops."""

    context.log.info("Starting crop data transformation.")

    clean_crops()

    context.log.info("Cleaning and loading completed.")


def run_dbt_command(context, command):
    """Execute a dbt CLI command and capture its output."""

    dbt_executable = shutil.which("dbt")

    if dbt_executable is None:
        raise RuntimeError(
            "Could not find dbt executable. "
            "Make sure dbt is installed in the active environment."
        )

    result = subprocess.run(
        [dbt_executable, *command],
        cwd=DBT_PROJECT_DIR,
        capture_output=True,
        text=True
    )

    if result.stdout:
        context.log.info(result.stdout)

    if result.stderr:
        context.log.info(result.stderr)

    if result.returncode != 0:
        raise RuntimeError(
            f"dbt {' '.join(command)} failed "
            f"with exit code {result.returncode}"
        )


@asset
def warehouse_models(context, cleaned_crops):
    """Build the dbt warehouse models."""

    context.log.info("Starting dbt run.")

    run_dbt_command(context, ["run"])

    context.log.info("dbt models built successfully.")


@asset
def warehouse_tests(context, warehouse_models):
    """Run dbt data quality tests."""

    context.log.info("Starting dbt tests.")

    run_dbt_command(context, ["test"])

    context.log.info("All dbt tests passed.")
