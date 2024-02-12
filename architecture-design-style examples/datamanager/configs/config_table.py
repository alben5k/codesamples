from dataclasses import dataclass
from typing import Any

from datamanager.strategies.search import(
    JsonSearchStrategy,
    )
from datamanager.strategies.storage import(
    JsonStorageStrategy,
    )

@dataclass
class ConfigLookupTable:
    storage_strategies: dict[str, Any]
    search_strategies: dict[str, Any]
    schemas: dict[str, Any]

