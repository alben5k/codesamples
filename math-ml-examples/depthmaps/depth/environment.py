from pathlib import Path


# We might move this to a config file later.
models = {
    "depth_anything": "LiheYoung/depth-anything-large-hf",
    "monodepth2": "nianticlabs/monodepth2",
    "midas": "intel/midas",
}


def setup_environment(model_path: Path) -> dict:
    """List models and their cache dir."""
    model_paths = {}

    for name, model in models.items():
        cache_dir = model_path / name
        if not cache_dir.exists():
            cache_dir.mkdir()

        model_paths[name] = cache_dir

    return model_paths
