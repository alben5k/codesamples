from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image


def get_image(input_path: Union[str, Path]) -> Image:
    """Open the image from the input path.

    Args:
        input_path: The path to the input image

    """
    return Image.open(input_path)


def array_to_image(array: np.array) -> Image:
    """Create an image from a numpy array.

    Args:
        array: The numpy array to convert to an image
    """
    normalized = array / array.max()
    formatted = (normalized * 255).astype(np.uint8)
    return Image.fromarray(formatted)


def upscale_image(image: Image, size: tuple) -> Image:
    """Upscale the image to the given size.

    Args:
        image: The image to upscale
        size: The size to upscale to
    """
    # In future use GAN models to upscale the image.
    return image.resize(size, Image.BICUBIC)
