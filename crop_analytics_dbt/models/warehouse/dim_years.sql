WITH unique_years AS (

    SELECT DISTINCT
        year
    FROM {{ ref('stg_crops') }}
    WHERE year IS NOT NULL

)

SELECT
    year AS year_key,
    year

FROM unique_years