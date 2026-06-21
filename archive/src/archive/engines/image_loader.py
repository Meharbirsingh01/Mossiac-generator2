from PIL import Image

def load_image(image_path):
    try:
        image = Image.open(image_path)
        print(f"Image loaded successfully!")
        print(f"Size: {image.size}")
        print(f"Mode: {image.mode}")
        return image
    except Exception as e:
        print(f"Error loading image: {e}")
        return None