import argparse
from pathlib import Path

from depth.estimate_depth import get_depth
from depth.mesh import output_depth_mesh
from image.image_transforms import get_image, array_to_image


def parse_arguments():
    """Parse the arguments."""
    parser = argparse.ArgumentParser(
        description="Create depth images from the raw data"
    )
    parser.add_argument(
        "--input", type=str, required=True, help="Path to the input data"
    )
    parser.add_argument(
        "--output", type=str, default="./outputs", help="Path to the output data"
    )
    parser.add_argument(
        "--models_dir",
        type=str,
        default="./models",
        help="Directory where models will be downloaded",
    )  # Prevents users from having to look for hugging face cache files after trying the script.
    return parser.parse_args()


def main():
    """Main function to create depth images from the raw data."""
    args = parse_arguments()
    input_path = Path(args.input)
    output_path = Path(args.output)
    models_dir = Path(args.models_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Input path {input_path} does not exist")
    if not output_path.exists():
        # We can create a directory if we need to, but instead we'll just raise an error for now.
        raise FileNotFoundError(f"Output path {output_path} does not exist")
    if not models_dir.exists():
        # Same as above, we'll raise an error for now.
        raise FileNotFoundError(f"Models directory {models_dir} does not exist")

    input_image = get_image(input_path)
    depth_output = get_depth(input_image, models_dir)
    output_image = array_to_image(depth_output)
    output_image.save(output_path / f"{input_path.stem}_depth.png")
    output_depth_mesh(depth_output, output_path / f"{input_path.stem}_depth.obj")


if __name__ == "__main__":
    main()
