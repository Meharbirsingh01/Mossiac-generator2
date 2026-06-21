from models.circle import Circle


def create_mosaic(image, layout):
    """
    Creates one Circle object for every printable circle.
    """

    circles = []

    width, height = image.size

    pitch = layout["pitch"]

    margin = 15  # mm (same as config)

    color_lookup = {}
    next_number = 1

    for row in range(height):

        for column in range(width):

            rgb = image.getpixel((column, row))

            if rgb not in color_lookup:
                color_lookup[rgb] = next_number
                next_number += 1

            number = color_lookup[rgb]

            x_mm = margin + (column * pitch) + (pitch / 2)
            y_mm = margin + (row * pitch) + (pitch / 2)

            circle = Circle(
                row=row,
                column=column,
                x_mm=x_mm,
                y_mm=y_mm,
                rgb=rgb,
                number=number
            )

            circles.append(circle)

    return circles