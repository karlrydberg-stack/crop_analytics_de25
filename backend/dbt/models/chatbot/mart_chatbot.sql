{#
  Flat, chatbot-friendly view: one row per place, crop and year.
  Total rows are removed so the chatbot can't double count.
#}
select
    c.geography_type  as level,        -- 'county' or 'national'
    c.county_name     as county,
    c.region,
    cr.crop_name      as crop,
    cr.crop_group,
    y.year,
    f.area_ha,
    f.harvest_ton,
    f.yield_ton_ha
from {{ ref('fact_crop_yield') }} as f
join {{ ref('dim_counties') }} as c  on f.county_key = c.county_key
join {{ ref('dim_crops') }}    as cr on f.crop_key   = cr.crop_key
join {{ ref('dim_years') }}    as y  on f.year_key   = y.year_key
where cr.crop_name not in (
        'Spannmål totalt',
        'Slåttervall, total vallskörd',
        'Slåttervall, återväxt'
      )
  and not (cr.crop_name = 'Rågvete' and y.year >= 2015)