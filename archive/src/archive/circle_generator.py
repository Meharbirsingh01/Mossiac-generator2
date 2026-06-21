import svgwrite

def generate_svg(layout, output_file):

    pitch = layout["pitch"]

    radius = pitch / 2.2

    dwg = svgwrite.Drawing(output_file)

    for row in range(layout["rows"]):

        for col in range(layout["columns"]):

            x = col * pitch + pitch
            y = row * pitch + pitch

            dwg.add(
                dwg.circle(
                    center=(x * 3.7795, y * 3.7795),
                    r=radius * 3.7795,
                    fill="white",
                    stroke="black",
                    stroke_width=0.5
                )
            )

    dwg.save()