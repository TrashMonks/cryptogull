from PIL import Image, ImageFont, ImageDraw, ImageColor, ImageFilter, ImageOps
import math
from textwrap import TextWrapper

font = ImageFont.truetype('SourceCodePro-Bold.ttf',28)
imgdim = (800,600)
charsize = (17,24)
maxw = 48
minw = 13
maxh = 16
padding = 10
innerpadding = (charsize[0]*2, charsize[1]*2)
absinnerpadding = (innerpadding[0]+padding, innerpadding[1]+padding)
lineheight=2    

def drawttf(saying):
    #determine size of image.
    if len(saying) > maxw:
        h = math.ceil(len(saying)/maxw)
        if h > maxh:
            h = maxh
        w = maxw
    else:
        w = len(saying)
        if w < minw:
            w = minw
        h = 1
    wrapper = TextWrapper(width=w, max_lines=maxh)
    imgdim = ((w*charsize[0])+(2*absinnerpadding[0]), (h*(charsize[1]+lineheight))+(2*absinnerpadding[1]))
    # generate base viridian color.
    image = Image.new(mode='RGBA',size=imgdim, color='#0f3b3a')
    draw = ImageDraw.Draw(image)
    # split text and wrap it
    sayingarr = saying.split('\r')
    a = []
    for paragraph in sayingarr:
        #split further using regex?
        a.append(wrapper.fill(paragraph))
    saying = '\n'.join(a)
    sayingdim = font.getsize(saying)
    temp = (imgdim[0]-sayingdim[0])/2
    # print text
    draw.multiline_text((temp, absinnerpadding[1]-4), saying, font=font, spacing=-1, fill='#b1c9c3')
    # draw specified border
    drawborder('popupclassic', draw, imgdim, padding, charsize)

    # image post processing
    scanline = drawscanline(imgdim)
    image = Image.alpha_composite(image,scanline)
    # vignette?? how do
    vignette = Image.radial_gradient('L')
    vignette = vignette.resize(imgdim)
    vignette.convert('RGBA')

    
    return image

def drawscanline(imgdim):
    # Draw scanlines to multiply on top
    temp = Image.new(mode='RGBA',size=imgdim, color=(255,255,255,0))
    tempdraw = ImageDraw.Draw(temp)
    for i in range(0, int(imgdim[1]/4)):
        tempdraw.line([(0,i*4), (imgdim[0]-1,i*4)], fill=(0,0,0,32), width=2)
    return temp

def drawborder(type, draw, imgdim, padding, charsize):
    #draw border. maybe have optional border versions?
    if type == 'popupclassic':
        return drawpopupclassic(draw, imgdim, padding, charsize)
    else:
        print(f'There wasn\'t a bordertype with the name {type}!')

def drawpopupclassic(draw, imgdim, padding, charsize):
    #v
    draw.line([(padding, padding),(padding, imgdim[1]-padding)], fill='#b1c9c3', width=8 )
    draw.line([(imgdim[0]-padding, padding),(imgdim[0]-padding, imgdim[1]-padding)], fill='#b1c9c3', width=8 )
    #h
    draw.line([(padding-3, padding+4),(imgdim[0]-padding+4, padding+4)], fill='#b1c9c3', width=12)
    draw.line([(padding-3, imgdim[1]-padding-4),(imgdim[0]-padding+4, imgdim[1]-padding-4)], fill='#b1c9c3', width=12 )
    #corners
    draw.rectangle([(padding, padding+4), (padding+charsize[0],padding+charsize[1])], fill='#b1c9c3')
    draw.rectangle([(padding, imgdim[1]-padding), (padding+charsize[0],imgdim[1]-padding-charsize[1])], fill='#b1c9c3')
    draw.rectangle([(imgdim[0]-padding, padding+4), (imgdim[0]-padding-charsize[0],padding+charsize[1])], fill='#b1c9c3')
    draw.rectangle([(imgdim[0]-padding, imgdim[1]-padding), (imgdim[0]-padding-charsize[0],imgdim[1]-padding-charsize[1])], fill='#b1c9c3')

    #draw "press space"
    text1 = '[press space]'
    text1dim = font.getsize(text1)
    draw.rectangle([((imgdim[0]-text1dim[0])/2 - 1, imgdim[1]), ((imgdim[0]+text1dim[0])/2 + 1,imgdim[1]-padding-charsize[1])], fill='#0f3b3a')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2, imgdim[1]-padding-charsize[1]-5), '[press      ]', font=font, fill='#b1c9c3')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2+font.getsize('[press ')[0], imgdim[1]-padding-charsize[1]-5), 'space', font=font, fill='#cfc041')
    return draw

def test():
    return drawttf("There are hostiles nearby!")
    #return drawttf("""Qud is a strange and terrifying mesa to the northeast. Her tainted rivers breed life in {{G|all}} its motley forms; her poisoned jungles shelter priceless relics of a forgotten past.\nBut that is just the half of it, for Qud's most precious treasures -- and her most hideous children -- lie within the innumerable chrome caverns beneath the scarlet loam.\nTo ply those silver hollows -- a spry adventurer's dream! The years have wizened me beyond such foolish ambitions, but, you! Be not deterred so!""")

if __name__ == '__main__':
    test().show()