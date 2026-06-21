from PIL import Image
from config import NUMBER_OF_COLORS

def reduce_colors(image):

    reduced = image.convert(
        "P",
        palette=Image.Palette.ADAPTIVE,
        colors=NUMBER_OF_COLORS
    )

    return reduced.convert("RGB")