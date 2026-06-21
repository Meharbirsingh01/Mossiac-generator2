from config import *
def calculate_layout():
 pitch=CIRCLE_DIAMETER_MM+CIRCLE_GAP_MM
 uw=PAGE_WIDTH_MM-MARGIN_LEFT_MM-MARGIN_RIGHT_MM
 uh=PAGE_HEIGHT_MM-MARGIN_TOP_MM-MARGIN_BOTTOM_MM
 return {'pitch':pitch,'columns':int(uw//pitch),'rows':int(uh//pitch)}
