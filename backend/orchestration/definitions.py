
from dagster import Definitions, load_assets_from_modules

from backend.orchestration.assets import crop_assets


all_assets = load_assets_from_modules([crop_assets])

defs = Definitions(
    assets=all_assets
)
