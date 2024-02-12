from abc import ABC
from typing import Any, Union

from datamanager.strategies.storage import AbstractStorageStrategy


class AbstractSearchStrategy(ABC):
    # Naive patterns that work for all storage strategies, for databases that contain
    # search functionality, these should be overridden.
    def __init__(self, storage_strategy: AbstractStorageStrategy):
        """Abstract search strategy

        Args:
            storage_strategy: storage strategy to use
        """
        self._storage_strategy = storage_strategy

    # Concrete methods ###
    def _fetch_data(self, asset_id: str) -> dict[str, Any]:
        """Fetches the data for the given asset id

        Args:
            asset_id: id of the asset to fetch the data for

        Returns:
            dictionary containing the data
        """
        return self._storage_strategy.get(asset_id)

    def _get_data_id(self, data: dict[str, Any]) -> Union[str, None]:
        """Reverse lookup gets the id of the given data

        Args:
            data: dictionary containing the data

        Returns:
            id of the data or None if not found
        """
        for asset_id in self.get_all():
            if self._fetch_data(asset_id) == data:
                return asset_id
        return None

    # noinspection PyMethodMayBeStatic
    def _matches_query(self, data: dict[str, Any], query: dict[str, Any]) -> bool:
        """Checks if the given data matches the given query

        Args:
            data: dictionary containing the data
            query: dictionary containing the query

        Returns:
            True if the data matches the query, False otherwise
        """
        return all(data.get(key) == value for key, value in query.items())

    def filter(self, assets: list[str], filter_criteria: dict[str, Any]) -> list[str]:
        """Filters a list of assets by the given filter criteria

        Args:
            assets: list of asset ids to filter
            filter_criteria: dictionary containing the filter criteria

        Returns:
            filtered asset ids
        """
        filtered_assets = []
        for asset in assets:
            data = self._fetch_data(asset)
            if self._matches_query(data, filter_criteria):
                filtered_assets.append(asset)
        return filtered_assets

    def get_all(self) -> list[str]:
        """Gets all data ids

        Returns:
            all data ids
        """
        return self._storage_strategy.get_all()

    def search(self, query: dict[str, Any]) -> list[str]:
        """Searches for data objects that match the query

        Args:
            query: dictionary containing the search parameters

        Returns:
            data ids that match the query
        """
        all_data = self.get_all()
        return self.filter(all_data, query)
