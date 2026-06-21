from PIL import Image

def resize_for_grid(image, columns, rows):
    resized = image.resize((columns, rows), Image.Resampling.LANCZOS)
    return resized