from PIL import Image, ImageFont, ImageDraw, ImageColor, ImageFilter, ImageOps
from os import mkdir
#import numpy as np
import math
import hagadias
from textwrap import TextWrapper
font = ImageFont.truetype('SourceCodePro-Semibold.ttf',24)
imgdim = (800,600)
charsize = (14,23)
maxw = 50
minw = 13
maxh = 16
padding = 10
innerpadding = (32,38)
absinnerpadding = (innerpadding[0]+padding, innerpadding[1]+padding)
lineheight=2
scanline = Image.open('scanline.png')

def __init__():
    #mkdir("assets/characters")
    #sheet = Image.open("assets/terminal2big.bmp")
    count = 0
    

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
    # generate details like the vignetting and scalines??
    vignette = Image.radial_gradient('L')
    vignette = vignette.resize(imgdim)
    vignette.convert('RGBA')
    # scanlines (WIP)
    longscanline= scanline.resize((scanline.height,imgdim[1]))
    #imgs_comb = np.vstack( (np.asarray( i ) for i in imgs ) )
    #imgs_comb = Image.fromarray( imgs_comb)
    #imgs_comb.save( 'Trifecta_vertical.jpg' )
    print(font.getsize('█'))
    draw = ImageDraw.Draw(image)
    # draw the text that goes on top. maybe it should be before the effects r applied.
    sayingarr = saying.split('\r')
    a = []
    for paragraph in sayingarr:
        #split further using regex?
        a.append(wrapper.fill(paragraph))
    saying = '\n'.join(a)
    sayingdim = font.getsize(saying)
    temp = (imgdim[0]-sayingdim[0])/2
    draw.multiline_text((temp, absinnerpadding[1]), saying, font=font, spacing=-1, fill='#b1c9c3')
    #image = image.filter(ImageFilter.GaussianBlur(radius=1))
    #draw border. maybe have optional border versions?
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
    draw.rectangle([((imgdim[0]-text1dim[0])/2 - 2, imgdim[1]), ((imgdim[0]+text1dim[0])/2+2,imgdim[1]-padding-charsize[1])], fill='#0f3b3a')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2, imgdim[1]-padding-charsize[1]), '[press      ]', font=font, fill='#b1c9c3')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2+font.getsize('[press ')[0], imgdim[1]-padding-charsize[1]), 'space', font=font, fill='#cfc041')
    #image = ImageChops.multiply(image * vignette) <-- this is broken
    return image #???


def test():
    return drawttf("There are hot singles nearby!")
    #return drawttf("""Qud is a strange and terrifying mesa to the northeast. Her tainted rivers breed life in {{G|all}} its motley forms; her poisoned jungles shelter priceless relics of a forgotten past.\nBut that is just the half of it, for Qud's most precious treasures -- and her most hideous children -- lie within the innumerable chrome caverns beneath the scarlet loam.\nTo ply those silver hollows -- a spry adventurer's dream! The years have wizened me beyond such foolish ambitions, but, you! Be not deterred so!""")

