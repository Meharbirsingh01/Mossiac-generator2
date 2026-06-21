from PIL import Image

def resize_for_grid(image,columns,rows):
 return image.resize((columns,rows),Image.Resampling.LANCZOS)
