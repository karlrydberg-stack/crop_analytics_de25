SELECT
    "Län_kod" AS county_code,
    "Län" AS county_name,
    "Gröda" AS crop_name,
    "År" AS year,
    area_ha,
    harvest_ton,
    yield_ton_ha

FROM {{ source('cleaned_data', 'crops') }}