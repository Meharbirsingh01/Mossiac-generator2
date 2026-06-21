from config import *

def calculate_layout():

    usable_width = PAGE_WIDTH_MM - (2 * MARGIN_MM)
    usable_height = PAGE_HEIGHT_MM - (2 * MARGIN_MM)

    pitch = CIRCLE_DIAMETER_MM + CIRCLE_GAP_MM

    columns = int(usable_width // pitch)
    rows = int(usable_height // pitch)

    return {
        "rows": rows,
        "columns": columns,
        "pitch": pitch,
        "usable_width": usable_width,
        "usable_height": usable_height
    }