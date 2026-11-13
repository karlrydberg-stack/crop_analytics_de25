import os

import pandas as pd
import streamlit as st
from sqlalchemy import MetaData, Table, URL, create_engine, inspect, select
from sqlalchemy.exc import SQLAlchemyError


st.set_page_config(
    page_title="Crop Analytics | Data Explorer",
    page_icon="🌾",
    layout="wide",
)

st.title("🌾 Crop Analytics")
st.subheader("Database explorer")
st.write("Browse the schemas, tables, and views available in your PostgreSQL database.")


def create_database_engine():
    required = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST"]
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing database environment variables: " + ", ".join(missing)
        )

    database_url = URL.create(
        drivername="postgresql+psycopg",
        username=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        host=os.environ["POSTGRES_HOST"],
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.environ["POSTGRES_DB"],
        query={"sslmode": os.getenv("POSTGRES_SSLMODE", "prefer")},
    )

    return create_engine(database_url, pool_pre_ping=True)


@st.cache_resource
def get_engine():
    return create_database_engine()


try:
    engine = get_engine()

    with engine.connect() as connection:
        connection.exec_driver_sql("SELECT 1")

    st.sidebar.header("Connection")
    st.sidebar.success("Connected to PostgreSQL")
    st.sidebar.caption(f"Host: {os.getenv('POSTGRES_HOST')}")
    st.sidebar.caption(f"Database: {os.getenv('POSTGRES_DB')}")

    inspector = inspect(engine)
    system_schemas = {"information_schema", "pg_catalog"}
    schemas = sorted(
        schema
        for schema in inspector.get_schema_names()
        if schema not in system_schemas and not schema.startswith("pg_toast")
    )

    if not schemas:
        st.info("No user schemas were found in this database.")
        st.stop()

    st.sidebar.header("Browse data")
    selected_schema = st.sidebar.selectbox("Schema", schemas)

    available_tables = set(inspector.get_table_names(schema=selected_schema))
    available_views = set(inspector.get_view_names(schema=selected_schema))
    relations = sorted(available_tables | available_views)

    if not relations:
        st.info(f"No tables or views found in `{selected_schema}`.")
        st.stop()

    selected_relation = st.sidebar.selectbox("Table or view", relations)
    row_limit = st.sidebar.slider(
        "Maximum rows to display",
        min_value=10,
        max_value=1000,
        value=100,
        step=10,
    )

    st.markdown(f"### `{selected_schema}.{selected_relation}`")
    st.caption(
        "Showing a limited preview. The source table or view is not modified."
    )

    relation = Table(
        selected_relation,
        MetaData(),
        schema=selected_schema,
        autoload_with=engine,
    )
    query = select(relation).limit(row_limit)

    with engine.connect() as connection:
        dataframe = pd.read_sql(query, connection)

    st.write(f"Returned **{len(dataframe):,}** rows")
    st.dataframe(dataframe, use_container_width=True, hide_index=True)

except (SQLAlchemyError, RuntimeError, ValueError) as error:
    st.error("Could not connect to or read from the database.")
    st.exception(error)
except Exception as error:
    st.error("An unexpected error occurred.")
    st.exception(error)
