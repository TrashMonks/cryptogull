from PIL import Image, ImageFont, ImageDraw
from textwrap import TextWrapper

font = ImageFont.truetype('SourceCodePro-Bold.ttf', 28)
imgdim = (800, 600)
charsize = (17, 26)
maxw = 48
minw = 13
maxh = 20
padding = 10
innerpadding = (charsize[0]*2, charsize[1]*2)
absinnerpadding = (innerpadding[0]+padding, innerpadding[1]+padding)


def drawttf(saying, bordertype='-popupclassic', arg=''):
    # split text and wrap it
    wrapper = TextWrapper(width=maxw, max_lines=maxh, replace_whitespace=False)
    sayingarr = saying.split('\n')
    a = []
    for paragraph in sayingarr:
        # split further using regex?
        a.append(wrapper.fill(paragraph))
    saying = '\n'.join(a)
    sayingdim = font.getsize_multiline(saying, spacing=-1)

    # generate image dimensions
    tempw = sayingdim[0]
    if tempw < minw*charsize[0]:
        tempw = minw*charsize[0]
    imgdim = (tempw+(2*absinnerpadding[0]), sayingdim[1]+(2*absinnerpadding[1]))
    # generate base viridian color.
    image = Image.new(mode='RGBA', size=imgdim, color='#0f3b3a')
    draw = ImageDraw.Draw(image)

    # print text
    temp = (imgdim[0]-sayingdim[0])/2
    if temp < absinnerpadding[0]:
        temp = absinnerpadding[0]
    draw.multiline_text((temp, absinnerpadding[1]-4), saying, font=font, spacing=-1,
                        fill='#b1c9c3')
    # draw specified border
    if bordertype is None:
        bordertype = '-popupclassic'
    if arg is None:
        arg = ''
    if drawborder(bordertype, draw, imgdim, padding, charsize, arg) is None:
        return None, "There was no border of that type."
    # image post processing
    scanline = drawscanline(imgdim)
    image = Image.alpha_composite(image, scanline)

    return image, ''


def drawscanline(imgdim):
    # Draw scanlines to multiply on top
    temp = Image.new(mode='RGBA', size=imgdim, color=(255, 255, 255, 0))
    tempdraw = ImageDraw.Draw(temp)
    for i in range(0, int(imgdim[1]/6)):
        tempdraw.line([(0, i*6), (imgdim[0]-1, i*6)], fill=(0, 0, 0, 16), width=3)
    return temp


def drawborder(type, draw, imgdim, padding, charsize, title):
    # draw border. maybe have optional border versions?
    if any(type == t for t in ['-popupclassic', '-p']):
        return drawpopupclassic(draw, imgdim, padding, charsize)
    elif any(type == t for t in ['-dialogueclassic', '-d']):
        return drawdialogueclassic(draw, imgdim, padding, charsize, title)
    else:
        print(f'There wasn\'t a bordertype with the name {type}!')
        return None


def drawpopupclassic(draw, imgdim, padding, charsize):
    # v
    draw.line([(padding, padding), (padding, imgdim[1]-padding)],
              fill='#b1c9c3', width=8)
    draw.line([(imgdim[0]-padding, padding), (imgdim[0]-padding, imgdim[1]-padding)],
              fill='#b1c9c3', width=8)
    # h
    draw.line([(padding-3, padding+4), (imgdim[0]-padding+4, padding+4)],
              fill='#b1c9c3', width=12)
    draw.line([(padding-3, imgdim[1]-padding-4), (imgdim[0]-padding+4, imgdim[1]-padding-4)],
              fill='#b1c9c3', width=12)
    # corners
    draw.rectangle([(padding, padding+4),
                    (padding+charsize[0], padding+charsize[1])],
                   fill='#b1c9c3')
    draw.rectangle([(padding, imgdim[1]-padding),
                   (padding+charsize[0], imgdim[1]-padding-charsize[1])],
                   fill='#b1c9c3')
    draw.rectangle([(imgdim[0]-padding, padding+4),
                    (imgdim[0]-padding-charsize[0],
                     padding+charsize[1])], fill='#b1c9c3')
    draw.rectangle([(imgdim[0]-padding, imgdim[1]-padding),
                   (imgdim[0]-padding-charsize[0],
                    imgdim[1]-padding-charsize[1])], fill='#b1c9c3')

    # draw "press space"
    text1 = '[press space]'
    text1dim = font.getsize(text1)
    draw.rectangle([((imgdim[0]-text1dim[0])/2 - 1, imgdim[1]),
                    ((imgdim[0]+text1dim[0])/2 + 1, imgdim[1]-padding-charsize[1])],
                   fill='#0f3b3a')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2, imgdim[1]-padding-charsize[1]-5),
                        '[press      ]', font=font, fill='#b1c9c3')
    draw.multiline_text(((imgdim[0]-text1dim[0])/2+font.getsize('[press ')[0],
                        imgdim[1]-padding-charsize[1]-5), 'space', font=font, fill='#cfc041')
    return draw


def drawdialogueclassic(draw, imgdim, padding, charsize, title):
    # draw border
    draw.rectangle([(padding+1, padding+charsize[0]/2),
                   (imgdim[0]-padding-2, imgdim[1]-padding-1)], outline='#b1c9c3', width=4)
    # draw person speaking. If title isn't specified, don't draw
    if title is not None and title != '':
        textdim = font.getsize(f'[ {title} ]')
        draw.rectangle([(charsize[0]*2+padding, 0),
                       (charsize[0]*2+padding+textdim[0], textdim[1]+padding)], fill='#0f3b3a')
        draw.text((charsize[0]*2+padding, 0), '[', font=font, fill='#b1c9c3')
        draw.text((charsize[0]+padding+textdim[0], 0), ']', font=font, fill='#b1c9c3')
        draw.text((charsize[0]*2+padding+font.getsize('[ ')[0], 0),
                  title, font=font, fill='#cfc041')
    return draw


def test():
    return drawttf("There are hostiles nearby!")

# if __name__ == '__main__':
#    test().show()
