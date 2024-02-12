from pathlib import Path

import numpy as np
import torch
from PIL import Image
from depth.environment import setup_environment, models
from transformers import AutoImageProcessor, AutoModelForDepthEstimation


def get_depth(
    image: Image, models_dir: Path, model_type: str = "depth_anything"
) -> np.array:
    """Get the depth images from the input data.

    Args:
        image: The image to depth
        models_dir: The path to the models directory
        model_type: The string name for the model type as defined by depth.environment.setup_environment(...)

    Returns:
        A 0-1 numpy array representing the depth estimation.
    """
    model_paths = setup_environment(models_dir)

    # For now we'll just use depth_anything
    model_cache = model_paths[model_type]
    model_name = models[model_type]

    image_processor = AutoImageProcessor.from_pretrained(
        model_name, cache_dir=model_cache
    )
    model = AutoModelForDepthEstimation.from_pretrained(
        model_name, cache_dir=model_cache
    )

    inputs = image_processor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        predicted_depth = outputs.predicted_depth

    prediction = torch.nn.functional.interpolate(
        predicted_depth.unsqueeze(1),
        size=image.size[::-1],
        mode="bicubic",
        align_corners=False,
    )

    # Return the numpy array
    output = prediction.squeeze().cpu().numpy()
    return output
