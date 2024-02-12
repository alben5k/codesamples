from dataclasses import dataclass


@dataclass
class UniversalSchema:
    """The universal schema that is used to define the universal schema for the data manager."""
    asset_uuid: str
    asset_name: str
    asset_type: str
    asset_version: str
    asset_path: str
    asset_description: str
    asset_tags: list[str]
    asset_created: str
    asset_modified: str
    asset_creator: str
    asset_modifier: str
    asset_status: str
    asset_category: str
    