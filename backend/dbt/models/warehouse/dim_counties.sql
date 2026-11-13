WITH unique_counties AS (

    SELECT DISTINCT
        county_code,
        county_name
    FROM {{ ref('stg_crops') }}
    WHERE county_code IS NOT NULL

)

SELECT
    MD5(county_code) AS county_key,
    county_code,
    county_name,

    CASE
        WHEN county_code = '00' THEN 'national'
        ELSE 'county'
    END AS geography_type

FROM unique_counties