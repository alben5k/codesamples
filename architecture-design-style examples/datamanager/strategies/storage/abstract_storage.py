import contextlib
import uuid
from abc import ABC, abstractmethod
from typing import Any


class AbstractStorageStrategy(ABC):
    """Abstract class for storage strategies"""

    # Concrete methods ###
    @contextlib.contextmanager
    def edit(self, asset_id: str) -> dict[str, Any]:
        """Context manager to edit data

        Args:
            asset_id: id of the asset to edit the data for

        Yields:
            dictionary containing the data
        """
        data = self.get(asset_id)
        yield data
        self.save(asset_id, data)

    @staticmethod
    def generate_id() -> str:
        """Generates a new id

        Returns:
            new id
        """
        return str(uuid.uuid4().hex)

    # Abstract methods ###

    @abstractmethod
    def delete(self, asset_id: str) -> bool:
        """Deletes the data for the given asset id

        Arguments:
            asset_id: id of the asset to delete the data for

        Returns:
            True if the data was deleted successfully, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, asset_id: str) -> dict[str, Any]:
        """Gets the data for the given asset id

        Arguments:
            asset_id: id of the asset to get the data for

        Returns:
            dictionary containing the data
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_ids(self) -> list[str]:
        """Gets all data ids

        Returns:
            list of all data ids
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, asset_id: str, data: dict[str, Any]) -> bool:
        """Saves the data for the given asset id

        Arguments:
            asset_id: id of the asset to save the data for
            data: dictionary containing the data

        Returns:
            True if the data was saved successfully, False otherwise
        """
        raise NotImplementedError
