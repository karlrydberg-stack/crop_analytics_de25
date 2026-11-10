SELECT
    crops.crop_key,
    counties.county_key,
    years.year_key,

    staging.area_ha,
    staging.harvest_ton,
    staging.yield_ton_ha

FROM {{ ref('stg_crops') }} AS staging

LEFT JOIN {{ ref('dim_crops') }} AS crops
    ON staging.crop_name = crops.crop_name

LEFT JOIN {{ ref('dim_counties') }} AS counties
    ON staging.county_code = counties.county_code

LEFT JOIN {{ ref('dim_years') }} AS years
    ON staging.year = years.year