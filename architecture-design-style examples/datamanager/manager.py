class DataManager:

    def __init__(self, config_file: str):
        """Entry point for external tools to interact with the data

        providing API functions to load, access, create, store, and manage data
        and holding the necessary objects in memory.
        It offers an easily readable and accessible API that exposes all public functions
        to the user in one place.

        Args:
            config_file: path to the configuration file that defines the data objects
                to use for the current project.
        """
        self._config_file = config_file
        self._data_interface = None

