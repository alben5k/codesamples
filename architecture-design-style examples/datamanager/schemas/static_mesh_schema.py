from dataclasses import dataclass


@dataclass
class StaticMeshSchema:
    """The schema for the static mesh data."""
    mesh_names: list[str]
    mesh_type: str
    mesh_lods: list[int]
    mesh_vertex_count: int
    mesh_surface_links: list[str]
    dcc_package: str
    dcc_version: str
    dcc_export_date: str
    