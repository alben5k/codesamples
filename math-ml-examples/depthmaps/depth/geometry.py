import numpy as np


def create_triangle_grid(height: int, width: int) -> np.array:
    """Create an array of indices representing vertices of triangles in a grid.

    Args:
        height (int): The height of the grid
        width (int): The width of the grid

    Returns:
        A 2D numpy array of indices with shape (2(height-1)(width-1) x 3)
    """
    # Create the grid
    x, y = np.meshgrid(np.arange(width - 1), np.arange(height - 1), indexing="ij")
    # Each square is made of two triangles with vertices a,b,c and d,c,b
    a = y * width + x
    b = (y + 1) * width + x
    c = y * width + x + 1
    d = (y + 1) * width + x + 1
    triangles = np.array([a, b, c, d, c, b])
    triangles = np.transpose(triangles, (1, 2, 0)).reshape(
        (width - 1) * (height - 1) * 2, 3
    )
    return triangles


def simple_intrinsics(height: int, width: int) -> np.array:
    """Create a simple camera intrinsics matrix.

    Args:
        height (int): The height of the image
        width (int): The width of the image

    Returns:
        A 3x3 numpy array representing the camera intrinsics
    """
    # For now assume a pinhole camera with fov of 55 degrees and central principal point
    fov_x = 63.5
    # Y is calculated from the aspect ratio
    fov_y = fov_x * (height / width)
    near_z = 0.00001
    far_z = 10000
    fx = width / (2 * np.tan(np.radians(fov_x) / 2))
    fy = height / (2 * np.tan(np.radians(fov_y) / 2))
    cx = width / 2
    cy = height / 2
    z_clipping = (far_z + near_z) / (far_z - near_z)
    return np.array([[fx, 0, cx], [0, fy, cy], [0, 0, z_clipping]])


def depth_to_point_cloud(
    depth: np.array, intrinsics: np.array = None, use_simple: bool = False
) -> np.array:
    """Create a point cloud from the depth image.

    Args:
        depth (np.array): The depth image
        intrinsics (np.array): The camera intrinsics, used to adjust the points from camera space to world space
        use_simple (bool): If True, use a simple intrinsics matrix instead of the real camera intrinsics
    Returns:
        A 3xN numpy array of points
    """
    # Depth is a 2D array where each value is the distance from the camera
    # We can create a point cloud by assuming the camera is at (0,0,0) and the image plane is at z=1
    # Then we can use the depth values to calculate the x and y values
    # We can then use the camera intrinsics to convert the x and y values to the correct scale
    # Finally we can stack the x and y values with the depth values to create the point cloud
    height, width = depth.shape

    x = np.arange(width)
    y = np.arange(height)
    grid = np.stack(np.meshgrid(x, y), -1)
    coord = np.concatenate(
        (grid, np.ones_like(grid)[:, :, [0]]), axis=-1
    )  # Add an axis for depth
    coord = coord.astype(np.float32)

    # Depth is the distance from the camera, so we need to invert it
    depth = 255.0 - depth

    if intrinsics is not None or use_simple:
        # The real camera is looking through a lens and the depth map is calculated
        # from a flat plane. If we ignore the lens and just use the depth map as the z value we'll get a distorted image
        # when we apply virtual camera intrinsics. To fix this we need to reverse the real camera intrinsics to get the
        # correct x and y values for the depth map. This is what we're doing here.
        depth = depth[None]  # Add z axis
        if intrinsics is None:
            intrinsics = simple_intrinsics(height=height, width=width)

        intrinsics_inverted = np.linalg.inv(intrinsics)
        # We can use einsum to multiply the intrinsics by the coordinate grid
        # This will give us the x and y values in camera space
        # this is equivalent to
        # for i in range(height):
        #    for j in range(width):
        #        coord[i, j] = np.dot(intrinsics_inverted, coord[i, j])
        point_cloud = np.einsum("ij,klj->kli", intrinsics_inverted, coord)
    else:
        # This calculation is good for converting a depth map to real 3d space for reconstruction such as a 3d print,
        # cnc, or an arbitrary camera. The shape will be correct but the depth will be very flat.
        point_cloud = coord.copy()
        for i in range(height):
            for j in range(width):
                point_cloud[i, j] = [j, i, depth[i, j]]

    # This gives us a cloud with the points in the wrong orientation so we need to flip them around.
    # Invert y and z to get correct order of points for trimesh reconstruction.
    point_cloud[:, :, 1] *= -1
    point_cloud[:, :, 2] *= -1

    # These points are giant, so we need to scale them down, we pick .1 arbitrarily
    point_cloud = point_cloud * 0.1

    point_cloud = point_cloud.reshape(-1, 3)

    return point_cloud
