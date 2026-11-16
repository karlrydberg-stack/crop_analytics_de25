WITH unique_counties AS (

    SELECT DISTINCT
        county_code,
        county_name
    FROM {{ ref('stg_crops') }}
    WHERE county_code IS NOT NULL

)

SELECT
    MD5(u.county_code) AS county_key,
    u.county_code,
    u.county_name,

    CASE
        WHEN u.county_code = '00' THEN 'national'
        ELSE 'county'
    END AS geography_type,

    r.region

FROM unique_counties AS u
LEFT JOIN {{ ref('county_regions') }} AS r
    ON u.county_name = r.county_name