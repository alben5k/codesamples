from datamanager.strategies.search import AbstractSearchStrategy


class JsonSearchStrategy(AbstractSearchStrategy):
    """Search strategy that searches the data in json files

    The json files are the data files and all searches use the naive strategies defined in the
    abstract search strategy.
    """
    # Possible improvements: add a search index to speed up the search, this would require a
    # reindexing step when the data is updated.
    # This object is empty because the json search strategy is naive and uses the abstract search.
