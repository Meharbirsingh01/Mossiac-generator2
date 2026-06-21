import svgwrite
MM_TO_PX=3.7795275591

def export_svg(circles,out,w,h,d):
 dwg=svgwrite.Drawing(out,size=(f'{w}mm',f'{h}mm'));r=(d/2)*MM_TO_PX;fs=max(6,r*0.9)
 for c in circles:
  x=c.x_mm*MM_TO_PX;y=c.y_mm*MM_TO_PX
  dwg.add(dwg.circle(center=(x,y),r=r,fill='white',stroke='black',stroke_width=0.6))
  dwg.add(dwg.text(str(c.number),insert=(x,y+fs*0.32),text_anchor='middle',font_size=fs,font_family='Arial'))
 dwg.save()
