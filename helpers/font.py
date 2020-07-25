from textwrap import TextWrapper

from hagadias import constants
from PIL import Image, ImageFont, ImageDraw


QUD_WHITE = constants.QUD_COLORS['y']
QUD_YELLOW = constants.QUD_COLORS['W']
QUD_VIRIDIAN = constants.QUD_VIRIDIAN
FONT = ImageFont.truetype('helpers/SourceCodePro-Bold.ttf', 28)
CHARSIZE = (17, 26)
MAXW = 48
MINW = 13
MAXH = 20
PAD = 10
innerpad = (CHARSIZE[0] * 2, CHARSIZE[1] * 2)
ABSINNERPAD = (innerpad[0] + PAD, innerpad[1] + PAD)


class DrawException(Exception):
    """Custom exception for drawing errors."""
    def __init__(self, message):
        self.message = message


def drawttf(saying, bordertype='-popupclassic', arg='') -> Image:
    """Main function for drawing the message box."""
    # split text and wrap it
    wrapper = TextWrapper(width=MAXW, max_lines=MAXH, replace_whitespace=False)
    sayingarr = saying.split('\n')
    a = []
    for paragraph in sayingarr:
        # split further using regex?
        a.append(wrapper.fill(paragraph))
    saying = '\n'.join(a)
    sayingdim = FONT.getsize_multiline(saying, spacing=-1)

    # generate image dimensions
    tempw = sayingdim[0]
    if tempw < MINW * CHARSIZE[0]:
        tempw = MINW * CHARSIZE[0]
    imgdim = (tempw + (2 * ABSINNERPAD[0]), sayingdim[1] + (2 * ABSINNERPAD[1]))
    # generate base viridian color.
    image = Image.new(mode='RGBA', size=imgdim, color=QUD_VIRIDIAN)
    draw = ImageDraw.Draw(image)

    # print text
    temp = (imgdim[0] - sayingdim[0]) / 2
    if temp < ABSINNERPAD[0]:
        temp = ABSINNERPAD[0]
    draw.multiline_text((temp, ABSINNERPAD[1] - 4), saying, font=FONT, spacing=-1,
                        fill=QUD_WHITE)
    # draw specified border
    if bordertype is None:
        bordertype = '-popupclassic'
    if arg is None:
        arg = ''
    drawborder(bordertype, draw, imgdim, PAD, CHARSIZE, arg)
    # image post processing
    image = drawscanline(image)
    return image


def drawscanline(image: Image) -> Image:
    """Draw scanlines over top of an image."""
    lines = Image.new(mode='RGBA', size=image.size, color=(255, 255, 255, 0))
    linedraw = ImageDraw.Draw(lines)
    for i in range(0, int(image.size[1] / 6)):
        linedraw.line([(0, i * 6), (image.size[0] - 1, i * 6)], fill=(0, 0, 0, 16), width=3)
    return Image.alpha_composite(image, lines)


def drawborder(kind, draw, imgdim, padding, charsize, title):
    """Draw the border over an image. Accepts multiple border types."""
    if any(kind == t for t in ['-popupclassic', '-p']):
        return drawpopupclassic(draw, imgdim, padding, charsize)
    elif any(kind == t for t in ['-dialogueclassic', '-d']):
        return drawdialogueclassic(draw, imgdim, padding, charsize, title)
    else:
        raise DrawException("There was no border of that type.")


def drawpopupclassic(draw, imgdim, padding, charsize):
    """Draw a classic popup."""
    # v
    draw.line([(padding, padding), (padding, imgdim[1] - padding)],
              fill='#b1c9c3', width=8)
    draw.line([(imgdim[0] - padding, padding), (imgdim[0] - padding, imgdim[1] - padding)],
              fill='#b1c9c3', width=8)
    # h
    draw.line([(padding - 3, padding + 4), (imgdim[0] - padding + 4, padding + 4)],
              fill='#b1c9c3', width=12)
    draw.line([(padding - 3, imgdim[1] - padding - 4),
               (imgdim[0] - padding + 4, imgdim[1] - padding - 4)],
              fill='#b1c9c3', width=12)
    # corners
    draw.rectangle([(padding, padding + 4),
                    (padding + charsize[0], padding + charsize[1])],
                   fill='#b1c9c3')
    draw.rectangle([(padding, imgdim[1] - padding),
                    (padding + charsize[0], imgdim[1] - padding - charsize[1])],
                   fill='#b1c9c3')
    draw.rectangle([(imgdim[0] - padding, padding + 4),
                    (imgdim[0] - padding - charsize[0],
                     padding + charsize[1])], fill='#b1c9c3')
    draw.rectangle([(imgdim[0] - padding, imgdim[1] - padding),
                    (imgdim[0] - padding - charsize[0],
                     imgdim[1] - padding - charsize[1])], fill='#b1c9c3')

    # draw "press space"
    text1 = '[press space]'
    text1dim = FONT.getsize(text1)
    draw.rectangle([((imgdim[0] - text1dim[0]) / 2 - 1, imgdim[1]),
                    ((imgdim[0] + text1dim[0]) / 2 + 1, imgdim[1] - padding - charsize[1])],
                   fill='#0f3b3a')
    draw.multiline_text(((imgdim[0] - text1dim[0]) / 2, imgdim[1] - padding - charsize[1] - 5),
                        '[press      ]', font=FONT, fill='#b1c9c3')
    draw.multiline_text(((imgdim[0] - text1dim[0]) / 2 + FONT.getsize('[press ')[0],
                         imgdim[1] - padding - charsize[1] - 5), 'space', font=FONT, fill='#cfc041')
    return draw


def drawdialogueclassic(draw, imgdim, padding, charsize, title):
    """Draw classic dialogue border."""
    draw.rectangle([(padding + 1, padding + charsize[0] / 2),
                    (imgdim[0] - padding - 2, imgdim[1] - padding - 1)], outline=QUD_WHITE, width=4)
    # draw person speaking. If title isn't specified, don't draw
    if title is not None and title != '':
        textdim = FONT.getsize(f'[ {title} ]')
        draw.rectangle([(charsize[0] * 2 + padding, 0),
                        (charsize[0] * 2 + padding + textdim[0], textdim[1] + padding)],
                       fill=QUD_VIRIDIAN)
        draw.text((charsize[0] * 2 + padding, 0), '[', font=FONT, fill=QUD_WHITE)
        draw.text((charsize[0] + padding + textdim[0], 0), ']', font=FONT, fill=QUD_WHITE)
        draw.text((charsize[0] * 2 + padding + FONT.getsize('[ ')[0], 0),
                  title, font=FONT, fill=QUD_YELLOW)
    return draw
