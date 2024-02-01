
class DataInterfaceFactory:

    def __init__(self, config_file: str):
        """Factory class to create a DataInterface object from a configuration file

       Uses ConfigurationReader to read the configuration file and create a DataInterface object

        Args:
            config_file: path to the configuration file
        """
        self._config_file = config_file
        self._data_interface = None

    def create_data_interface(self) -> DataInterface:
        """Creates a DataInterface object from the configuration file

        Returns:
            DataInterface: the created DataInterface object
        """
        config_reader = ConfigurationReader(self._config_file)
        config = config_reader.read_config()
        self._data_interface = DataInterface(config)
        return self._data_interface