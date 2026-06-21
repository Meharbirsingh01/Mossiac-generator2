def create_grid(image):
    width, height = image.size

    grid = []

    for y in range(height):
        row = []

        for x in range(width):

            color = image.getpixel((x, y))

            row.append({
                "x": x,
                "y": y,
                "color": color
            })

        grid.append(row)

    return grid