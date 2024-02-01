import logging
import os
from json import dumps, loads
from pathlib import Path
from typing import Any, Optional

from datamanager.strategies.storage.abstract_storage import AbstractStorageStrategy
from shared.version_control import perforce

logger = logging.getLogger(__name__)


class JsonStorageStrategy(AbstractStorageStrategy):
    def __init__(
            self,
            data_path: str,
            use_p4: Optional[bool] = True
            ):
        """Storage strategy that saves the data as json files
        Uses perforce to save the data files if use_p4 is True.
        Args:
            data_path: path where the data files are stored
            use_p4: whether to use perforce to save the data files

        Raises:
            ValueError: if the data_path is not a valid path
        """
        self.use_p4 = use_p4
        self.depot_path = None
        self.client = None
        if self.use_p4:
            self.depot_path = data_path
            self.client = perforce.get_hosted_assets_client()
            self._get_latest_all()
        else:
            self.data_path = Path(data_path)

    @staticmethod
    def _initialize_data_directory_in_perforce(path: str):
        """Initializes the data directory

        Convenience function to make a new data directory with an empty json file in perforce.
        Good way to create a valid path to set in your config file.

        Args:
            path: path to the data directory
        """
        depot_path = path
        client = perforce.get_hosted_assets_client()
        with perforce.connected(client = client):
            data_path = Path(perforce.convert_paths_to_local_path(depot_path)[0])
            filepath = str(data_path / Path("0.json"))
            exists = perforce.exists_in_depot(str(data_path))
            if exists:
                logger.warning(f"Data directory already exists: {data_path}")
                perforce.get_latest_force(str(data_path))
                perforce.get_revision(filepath, 1, force = True)
            else:
                if not os.path.exists(data_path):
                    os.makedirs(data_path)
                if not os.listdir(data_path):
                    with open(filepath, "w") as f:
                        f.write(dumps({}))
                    logger.debug("Trying to add to depot.")
                    perforce.add_to_depot(
                            list(data_path.iterdir()),
                            submit_files = True,
                            comment = "Initializing data directory",
                            error_if_exists = True,
                            )

        logger.info(f"Data directory initialized: {data_path}")

    def _get_latest_all(self):
        """Gets the latest version of the data directory from perforce

        Raises:
            ValueError: if the data_path is not a valid path
        """
        if self.use_p4:
            self.client = perforce.get_hosted_assets_client()
            with perforce.connected(client = self.client):
                self.data_path = Path(perforce.convert_paths_to_local_path(self.depot_path)[0])
                if not self.data_path.exists():
                    exists = perforce.exists_in_depot(self.depot_path)
                    if not exists:
                        raise ValueError(f'{self.data_path} is not a valid path')
                perforce.get_latest(self.depot_path + '/...')

    def delete(self, asset_id: str) -> bool:
        """Deletes the data for the given asset id

        Args:
            asset_id: id of the asset to delete the data for

        Returns:
            True if the data was deleted successfully, False otherwise
        """
        path = str(self.data_path / f"{asset_id}.json")
        if self.use_p4:
            if not os.path.exists(path):
                return False
            with perforce.connected(client = self.client):
                if not perforce.exists_in_depot(path):
                    return False
                changelist = perforce.make_changelist(
                        description = f"Deleting data for asset {asset_id}"
                        )
                perforce.mark_for_delete(path, changelist)
                try:
                    perforce.submit(changelist, description = f"Deleting data for asset {asset_id}")
                except perforce.P4Exception:
                    # If the file is already deleted, we don't care
                    logger.debug(f"Ignoring asset {asset_id} as it is not in the repo.")
                perforce.clean_empty_changelists()

        else:
            os.remove(path)
        return True

    def get(self, asset_id: str) -> dict[str, Any]:
        """Gets the data for the given asset id

        Args:
            asset_id: id of the asset to get the data for

        Returns:
            dictionary containing the data
        """
        path = self.data_path / f"{asset_id}.json"
        if self.use_p4:
            with perforce.connected(client = self.client):
                perforce.get_latest(path)
        if not os.path.exists(path):
            return {}
        with open(path, 'r') as file:
            return loads(file.read())

    def get_all_ids(self) -> list[str]:
        """Gets all data ids

        Returns:
            list of all data ids
        """
        self._get_latest_all()
        ids = []
        for path in self.data_path.glob("*.json"):
            if path.is_file():
                ids.append(str(path.stem.rstrip(".json")))
        return ids

    def save(self, asset_id: str, data: dict[str, Any]) -> bool:
        """Saves the data for the given asset id

        Args:
            asset_id: id of the asset to save the data for
            data: dictionary containing the data

        Returns:
            True if the data was saved successfully, False otherwise
        """
        current_data = self.get(asset_id)
        if current_data == data:
            if not data:
                reason = "empty"
            else:
                reason = "already up to date"
            logger.info(f"Data for asset {asset_id} is {reason}. No save necessary.")
            return True
        path = str(self.data_path / f"{asset_id}.json")

        try:
            if self.use_p4:
                with perforce.connected(client = self.client):
                    if not os.path.exists(path):
                        with open(path, 'w') as file:
                            # We want to submit an empty file to perforce so that we can
                            # normalize the process.
                            file.write(dumps({}))
                        perforce.add_to_depot(path, submit_files = True)
                    perforce.clean_empty_changelists()
                    perforce.get_latest(path)
                    description = f"Updating data for asset {asset_id}"
                    changelist = perforce.get_or_make_changelist(description = description)
                    try:
                        perforce.check_out(path, changelist, do_get_latest = True)
                    except perforce.P4ExceptionExclusivelyCheckedOut as e:
                        logger.error(
                                "Cannot save {asset_id} data because "
                                "it is exclusively checked out."
                                )
                        logger.error(f"Error: {e}")
                        return False

                    with open(path, 'w') as file:
                        file.write(dumps(data))

                    perforce.submit(
                            changelist,
                            description = description,
                            clean_up_empty_changelist = True
                            )
            else:
                with open(path, 'w') as file:
                    file.write(dumps(data))
        except IOError as e:
            logger.error(f"Error saving data: {e}")
            return False
