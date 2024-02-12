These are code snippets and a partial implementation of a database agnostic data system using dataclasses. 
The system is was designed using SOLID design principles and built with an abstraction layer to allow users to build 
their own database storage and search strategies and plug them into the system in a modular way.

Here is how the system uses SOLID in its design:
1. Single Responsibility Principle (SRP):
    1. The `DataManager` class is responsible for managing the data and the storage and search strategies.
   2. The `StorageStrategy` class is responsible for managing the storage of the data.
   3. The `SearchStrategy` class is responsible for managing the search of the data.
   4. The `config_table` function is responsible for loading the configuration of the data from a file.
   5. The json schemas are responsible for validating the configurations that users provide.
   6. The various `schemas` are responsible for defining and validating data.
2. Open/Closed Principle (OCP):
    1. The `abstract_storage_strategy` and `abstract_search_strategy` classes allow users to extend the way they communicate with their databases without modifying our API.
3. Liskov Substitution Principle (LSP):
    1. The `StorageStrategy` and `SearchStrategy` classes are designed to be interchangeable with any other class that implements the same interface.
4. Interface Segregation Principle (ISP):
    1. The `StorageStrategy` and `SearchStrategy` classes are designed to be modular and allow users to insert their own strategies that they may use.
5. Dependency Inversion Principle (DIP):
    1. All the classes are designed to depend on abstractions and not on concretions. This allows users to extend the system without modifying our API. 