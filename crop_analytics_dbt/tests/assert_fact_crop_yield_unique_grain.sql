SELECT
    crop_key,
    county_key,
    year_key,
    COUNT(*) AS record_count

FROM {{ ref('fact_crop_yield') }}

GROUP BY
    crop_key,
    county_key,
    year_key

HAVING COUNT(*) > 1