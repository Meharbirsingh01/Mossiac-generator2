from engines.image_loader import load_image
from engines.image_processor import resize_for_grid
from engines.color_quantizer import reduce_colors
from engines.layout_engine import calculate_layout
from engines.mosaic_engine import create_mosaic
from config import INPUT_FOLDER

def main():
    layout = calculate_layout()

    image = load_image(f"{INPUT_FOLDER}/sample.jpg")

    if image is None:
        print("Failed to load image.")
        return

    image = resize_for_grid(
        image,
        layout["columns"],
        layout["rows"]
    )

    image = reduce_colors(image)

    circles = create_mosaic(image, layout)

    print(f"\nTotal Circles: {len(circles)}\n")

    print("First 5 Circles:\n")
    for circle in circles[:5]:
        print(circle)


if __name__ == "__main__":
    main()