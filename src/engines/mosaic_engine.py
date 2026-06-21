from models.circle import Circle

def create_mosaic(image,layout):
 circles=[];lookup={};n=1;pitch=layout['pitch']
 for r in range(image.height):
  for c in range(image.width):
   rgb=image.getpixel((c,r))
   if rgb not in lookup: lookup[rgb]=n;n+=1
   circles.append(Circle(r,c,15+(c*pitch)+pitch/2,15+(r*pitch)+pitch/2,rgb,lookup[rgb]))
 return circles
