def assign_numbers(circles):

    color_map = {}

    current = 1

    for circle in circles:

        rgb = circle["rgb"]

        if rgb not in color_map:

            color_map[rgb] = current
            current += 1

        circle["number"] = color_map[rgb]

    return circles