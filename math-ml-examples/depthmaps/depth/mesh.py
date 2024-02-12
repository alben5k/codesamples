import pathlib

import numpy as np
import trimesh
from depth.geometry import depth_to_point_cloud, create_triangle_grid


def depth_to_mesh(depth: np.array, intrinsics: np.array = None) -> trimesh.Trimesh:
    """Create a mesh from the depth image.
    Args:
        depth (np.array): The depth image
        intrinsics (np.array): The camera intrinsics, used to adjust the points from camera space to world space
    Returns:
        A trimesh object
    """
    # depth = np.rot90(depth, 3)  # Y Up
    # Create the point cloud
    point_cloud = depth_to_point_cloud(depth, intrinsics)
    verts = point_cloud.reshape(-1, 3)
    # Create the mesh
    mesh = trimesh.Trimesh(vertices=verts, faces=create_triangle_grid(*depth.shape))
    return mesh


def output_depth_mesh(depth: np.array, output_path: pathlib.Path):
    """Save the depth image to the output path."""
    mesh = depth_to_mesh(depth)
    mesh.export(str(output_path))
