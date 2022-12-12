import importlib.resources
from textwrap import TextWrapper

from hagadias import constants
from hagadias.helpers import iter_qud_colors, strip_newstyle_qud_colors
from PIL import Image, ImageFont, ImageDraw

from bot.shared import gameroot
game_colors = gameroot.get_colors()


QUD_WHITE = constants.QUD_COLORS['y']
QUD_YELLOW = constants.QUD_COLORS['W']
QUD_VIRIDIAN = constants.QUD_COLORS['k']
# this font file is now used from hagadias' assets dir instead of being included
font_path = importlib.resources.files("hagadias") / 'assets' / 'SourceCodePro-Bold.ttf'
FONT = ImageFont.truetype(str(font_path), 28)
CHARSIZE = (17, 26)
MAXW = 48
MINW = 13
MAXH = 20
PAD = 10
innerpad = (CHARSIZE[0] * 2, CHARSIZE[1] * 2)
ABSINNERPAD = (innerpad[0] + PAD, innerpad[1] + PAD)
POPUPCLASSIC, DIALOGUECLASSIC = 1, 2


class DrawException(Exception):
    """Custom exception for drawing errors."""
    def __init__(self, message):
        self.message = message


def drawttf(saying, bordertype='-popupclassic', dialog_title='') -> Image:
    """Main function for drawing the message box."""
    if dialog_title is None:
        dialog_title = ''
    if bordertype is None:
        bordertype = '-p'
    # first, wrap and split the plaintext, then reassemble with colours
    plain_saying = strip_newstyle_qud_colors(saying)
    wrapper = TextWrapper(width=MAXW, max_lines=MAXH, replace_whitespace=False)
    paragraphs = plain_saying.split('\n')
    text_lines = []
    for paragraph in paragraphs:
        text_lines.extend(wrapper.fill(paragraph).split('\n'))
    # we will use the plain text wrapped by TextWrapper to count real characters on each line,
    # then draw those characters using the parsed-out per-character color codes:
    plain_text_for_sizing = '\n'.join(text_lines)
    sayingdim = FONT.getsize_multiline(plain_text_for_sizing, spacing=-1)
    # determine border type
    border_kind = determineborder(bordertype)
    # determine image dimensions
    base_pxwidth = MINW * CHARSIZE[0]
    text_pxwidth = sayingdim[0]
    title_pxwidth = (FONT.getsize(f'[ {dialog_title} ]')[0] if
                     border_kind == DIALOGUECLASSIC else 0)
    pxwidth = max(base_pxwidth, text_pxwidth, title_pxwidth)
    pad_pxwidth = pxwidth + (2 * ABSINNERPAD[0])
    pad_pxheight = sayingdim[1] + (2 * ABSINNERPAD[1])
    imgdim = (pad_pxwidth, pad_pxheight)
    # create and draw image
    image = Image.new(mode='RGBA', size=imgdim, color=QUD_VIRIDIAN)
    draw = ImageDraw.Draw(image)
    drawborder(border_kind, draw, imgdim, PAD, CHARSIZE, dialog_title)
    if border_kind == POPUPCLASSIC:
        leftx = (imgdim[0] - text_pxwidth) / 2  # center text if popup
    else:
        leftx = (imgdim[0] - pxwidth) / 2
    if leftx < ABSINNERPAD[0]:
        leftx = ABSINNERPAD[0]
    cur_x = leftx
    cur_y = ABSINNERPAD[1] - 4
    chars_colors = iter_qud_colors(saying, game_colors)
    for line in text_lines:
        for tracking, (char, code) in zip(line, chars_colors):
            # fast-forward if necessary to skip whitespace that was deleted by TextWrapper
            while char != tracking:
                try:
                    char, code = next(chars_colors)
                except StopIteration:
                    break
            if code is None:
                color = constants.QUD_COLORS['y']
            else:
                color = constants.QUD_COLORS[code]
            draw.text((cur_x, cur_y), char, font=FONT, fill=color)
            cur_x += CHARSIZE[0]
        cur_x = leftx
        cur_y += CHARSIZE[1]
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


def determineborder(kind):
    if any(kind == t for t in ['-popupclassic', '-p']):
        return POPUPCLASSIC
    elif any(kind == t for t in ['-dialogueclassic', '-d']):
        return DIALOGUECLASSIC
    else:
        raise DrawException("There was no border of that type.")


def drawborder(kind, draw, imgdim, padding, charsize, title):
    """Draw the border over an image. Accepts multiple border types."""
    if kind == POPUPCLASSIC:
        return drawpopupclassic(draw, imgdim, padding, charsize)
    elif kind == DIALOGUECLASSIC:
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
        plain_title = strip_newstyle_qud_colors(title)
        textdim = FONT.getsize(f'[ {plain_title} ]')
        draw.rectangle([(charsize[0] * 2 + padding, 0),
                        (charsize[0] * 2 + padding + textdim[0], textdim[1] + padding)],
                       fill=QUD_VIRIDIAN)
        draw.text((charsize[0] * 2 + padding, 0), '[', font=FONT, fill=QUD_WHITE)
        draw.text((charsize[0] + padding + textdim[0], 0), ']', font=FONT, fill=QUD_WHITE)
        cur_x = charsize[0] * 2 + padding + FONT.getsize('[ ')[0]
        if plain_title != title:
            for char, code in iter_qud_colors(title, game_colors):
                if code is None:
                    color = constants.QUD_COLORS['y']
                else:
                    color = constants.QUD_COLORS[code]
                draw.text((cur_x, 0), char, font=FONT, fill=color)
                cur_x += CHARSIZE[0]
        else:
            # didn't use any color shaders
            draw.text((charsize[0] * 2 + padding + FONT.getsize('[ ')[0], 0),
                      title, font=FONT, fill=QUD_YELLOW)
    return draw
