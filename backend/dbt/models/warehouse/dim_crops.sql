WITH unique_crops AS (

    SELECT DISTINCT
        crop_name
    FROM {{ ref('stg_crops') }}
    WHERE crop_name IS NOT NULL

)

SELECT
    MD5(u.crop_name) AS crop_key,
    u.crop_name,
    g.crop_group

FROM unique_crops AS u
LEFT JOIN {{ ref('crop_groups') }} AS g
    ON u.crop_name = g.crop_name