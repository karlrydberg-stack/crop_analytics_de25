{#
  Use a model's custom schema name exactly as written (e.g. "chatbot"),
  instead of dbt's default "<target schema>_<custom schema>" (e.g. "warehouse_chatbot").
  Models without a custom schema stay in the profile's schema (warehouse).
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {{ custom_schema_name if custom_schema_name else target.schema }}
{%- endmacro %}