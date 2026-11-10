WITH unique_crops AS (

    SELECT DISTINCT
        crop_name
    FROM {{ ref('stg_crops') }}
    WHERE crop_name IS NOT NULL

)

SELECT
    MD5(crop_name) AS crop_key,
    crop_name

FROM unique_crops