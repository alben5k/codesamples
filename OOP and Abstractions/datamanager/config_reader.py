import json
import os
from dataclasses import dataclass
from pathlib import Path

from datamanager.strategies.storage.abstract_storage import AbstractStorageStrategy
from datamanager.strategies.search.abstract_search import AbstractSearchStrategy
from datamanager.schemas.abstract_schema import AbstractSchema

# Because there is a very small number of possible strategies and schemas, we'll create
# a lookup table, should we find that there are a much larger number we can use something
# like __import__ to grab the correct objects.


@dataclass
class ConfigReader:
    storageStrategy: AbstractStorageStrategy
    searchStrategy: AbstractSearchStrategy
    storagePath: str
    universalSchema: AbstractSchema
    schemas: dict[str, AbstractSchema]
    requiredEnvirons: dict[str, str]
    useUniversal: bool = True

    def __init__(self, config_file_path:str) -> None:
        """The reader that loads and createds objects to be used as defined in the configuration json.

        Args:
            config_file_path: The path to the json configuration file.
        """

        config_file_path = Path(config_file_path)
        if not config_file_path.exists():
            raise ValueError(f"The path {config_file_path} does not exist on the filesystem.")
        
        with config_file_path.open() as file:
            config_options = json.loads(file.read())

        # Just import for now, we will instantiate later but we want to seperate these
        # sections in case of bugs or if we change the way we bring them in.
        storage_module = __import__(f"{absolute_path}.strategies.storage.{config_options['storageStrategy']}")
        search_module = __import__(f"{absolute_path}.strategies.search.{config_options['searchStrategy']}")
        if "universalSchema" in config_options:
            universal_schema_module = __import__(f"{absolute_path}.schemas.{config_options['universalSchema']}")
        else:
            universal_schema_module = None
        schema_modules = {}
        for schema_name, module in config_options["schemas"]:
            schema_modules[schema_name] = __import__(f"{absolute_path}.schemas.{module}")

        # Set 1:1 values such as strings and the like. Do this section first so we can replace
        # certain values from the requiredEnvirons. We typically set things like the
        # path's root value in the environment.
        self.storagePath = config_options["storagePath"]
        self.useUniversal = config_options["useUniversal"]

        # This is where we set things from the environment, if there is anything besides path
        # that needs to be updated via an environment variable it should be above this line.
        # For example, for json files stored in perforce, we set the BRANCH_ROOT in the environment
        # which allows us to update the root path per-pipeline. In this case we replace BRANCH_ROOT
        # in the storagePath. If our configuration contains other things such as a URL
        # for a database etc. this is where we might set it, to allow us to change the service
        # location per-pipeline.
        if "requiredEnvirons" in config_options:
            self.requiredEnvirons = config_options['requiredEnvirons']
            for attr_name, values in self.requiredEnvirons:
                for value in values:
                    getattr(self, attr_name).replace("{" + value + "}", os.environ[value])

        self.storageStrategy = storage_module(self.storagePath)
        self.searchStrategy = search_module(self.storageStrategy)
        if self.useUniversal and universal_schema_module:
            self.universalSchema = universal_schema_module()
        for module_name, module in schema_modules:
            self.schemas[module_name] = module()