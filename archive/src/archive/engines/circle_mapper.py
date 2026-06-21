def map_circles(image):

    width, height = image.size

    circles = []

    for y in range(height):

        for x in range(width):

            color = image.getpixel((x, y))

            circles.append({

                "row": y,

                "column": x,

                "rgb": color,

                "number": 0

            })

    return circles