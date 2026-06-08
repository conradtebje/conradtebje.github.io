"""
Portfolio PDF builder — Conrad Tebje
A3 landscape, ReportLab + Lato
"""

from reportlab.lib.pagesizes import A3, landscape
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader
from PIL import Image
import io, os, textwrap

# ─── Setup ──────────────────────────────────────────────────────────────────

BASE = os.path.dirname(os.path.abspath(__file__))
OUT  = os.path.join(BASE, "Conrad_Tebje_Portfolio.pdf")

W, H = landscape(A3)   # 1190.55 x 841.89 pt

# Register Lato
FONTS = {
    "light":    "/usr/share/fonts/truetype/lato/Lato-Light.ttf",
    "regular":  "/usr/share/fonts/truetype/lato/Lato-Regular.ttf",
    "medium":   "/usr/share/fonts/truetype/lato/Lato-Medium.ttf",
    "semibold": "/usr/share/fonts/truetype/lato/Lato-Semibold.ttf",
    "bold":     "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "black":    "/usr/share/fonts/truetype/lato/Lato-Black.ttf",
    "thin":     "/usr/share/fonts/truetype/lato/Lato-Thin.ttf",
    "italic":   "/usr/share/fonts/truetype/lato/Lato-Italic.ttf",
    "lightitalic": "/usr/share/fonts/truetype/lato/Lato-LightItalic.ttf",
}

for name, path in FONTS.items():
    pdfmetrics.registerFont(TTFont(f"Lato-{name}", path))

# Colours (R, G, B) 0–1
GREEN      = (0.118, 0.239, 0.157)
GREEN_MID  = (0.176, 0.329, 0.212)
GREEN_LIGHT= (0.290, 0.478, 0.353)
RUST       = (0.659, 0.361, 0.102)
RUST_LIGHT = (0.788, 0.478, 0.227)
WHITE      = (0.965, 0.957, 0.937)
GREY       = (0.910, 0.898, 0.871)
DARK       = (0.055, 0.055, 0.055)
MID        = (0.290, 0.290, 0.290)
LIGHT_TEXT = (0.478, 0.478, 0.478)

# ─── Helpers ────────────────────────────────────────────────────────────────

def img_path(*parts):
    return os.path.join(BASE, *parts)

def set_fill(c, rgb):
    c.setFillColorRGB(*rgb)

def set_stroke(c, rgb):
    c.setStrokeColorRGB(*rgb)

def rect(c, x, y, w, h, fill_rgb=None, stroke=False):
    if fill_rgb:
        set_fill(c, fill_rgb)
    if stroke:
        c.rect(x, y, w, h, fill=1 if fill_rgb else 0, stroke=1)
    else:
        c.rect(x, y, w, h, fill=1 if fill_rgb else 0, stroke=0)

def place_image(c, path, x, y, w, h, fit="cover", brightness=1.0):
    """Place an image clipped to a rectangle."""
    if not os.path.exists(path):
        rect(c, x, y, w, h, fill_rgb=DARK)
        return
    try:
        im = Image.open(path).convert("RGB")
        iw, ih = im.size
        if fit == "cover":
            scale = max(w/iw, h/ih)
            nw, nh = int(iw*scale), int(ih*scale)
            im = im.resize((nw, nh), Image.LANCZOS)
            ox = (nw - w) / 2
            oy = (nh - h) / 2
            im = im.crop((ox, oy, ox+w, oy+h))
        elif fit == "contain":
            scale = min(w/iw, h/ih)
            nw, nh = int(iw*scale), int(ih*scale)
            im = im.resize((nw, nh), Image.LANCZOS)
            bg = Image.new("RGB", (int(w), int(h)), (int(DARK[0]*255),)*3)
            px = int((w-nw)//2)
            py = int((h-nh)//2)
            bg.paste(im, (px, py))
            im = bg
        if brightness != 1.0:
            from PIL import ImageEnhance
            im = ImageEnhance.Brightness(im).enhance(brightness)
        buf = io.BytesIO()
        im.save(buf, "PNG")
        buf.seek(0)
        c.drawImage(ImageReader(buf), x, y, w, h)
    except Exception as e:
        rect(c, x, y, w, h, fill_rgb=DARK)

def overlay(c, x, y, w, h, rgb, alpha):
    c.saveState()
    c.setFillColorRGB(*rgb, alpha=alpha)
    c.rect(x, y, w, h, fill=1, stroke=0)
    c.restoreState()

def label(c, text, x, y, rgb=RUST_LIGHT, size=8, font="Lato-semibold"):
    """Small uppercase tracking label."""
    c.saveState()
    set_fill(c, rgb)
    c.setFont(font, size)
    c.drawString(x, y, text.upper())
    c.restoreState()

def rule(c, x, y, length, rgb=RUST, thickness=1.5):
    c.saveState()
    set_stroke(c, rgb)
    c.setLineWidth(thickness)
    c.line(x, y, x + length, y)
    c.restoreState()

def body_text(c, text, x, y, w, font="Lato-light", size=9.5, rgb=None,
              leading=16, max_h=None):
    """
    Wraps and draws body text. Returns the y position after last line.
    """
    if rgb is None:
        rgb = (0.7, 0.7, 0.7)
    c.saveState()
    set_fill(c, rgb)
    c.setFont(font, size)
    chars_per_line = max(int(w / (size * 0.52)), 20)
    lines = []
    for para in text.split('\n'):
        if para.strip() == '':
            lines.append('')
        else:
            wrapped = textwrap.wrap(para, width=chars_per_line)
            lines.extend(wrapped if wrapped else [''])
    cur_y = y
    for line in lines:
        if max_h and (y - cur_y) > max_h:
            break
        c.drawString(x, cur_y, line)
        cur_y -= leading
    c.restoreState()
    return cur_y

def heading(c, text, x, y, font="Lato-black", size=32, rgb=WHITE, tracking=None):
    c.saveState()
    set_fill(c, rgb)
    c.setFont(font, size)
    c.drawString(x, y, text)
    c.restoreState()

def multiline_heading(c, lines, x, y, font="Lato-black", size=32, rgb=WHITE, leading=None):
    if leading is None:
        leading = size * 1.05
    c.saveState()
    set_fill(c, rgb)
    c.setFont(font, size)
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    c.restoreState()
    return y

def chapter_num_line(c, text, x, y, rgb=RUST):
    rule(c, x, y + 4, 20, rgb)
    c.saveState()
    set_fill(c, rgb)
    c.setFont("Lato-semibold", 7.5)
    c.drawString(x + 26, y, text.upper())
    c.restoreState()

def page_number(c, n, total):
    c.saveState()
    set_fill(c, (0.3, 0.3, 0.3))
    c.setFont("Lato-light", 7)
    c.drawRightString(W - 32, 20, f"{n} / {total}")
    c.restoreState()

# ─── IMAGES ─────────────────────────────────────────────────────────────────

# Meridian
M_EXT        = img_path("screenshots2", "Screenshot 2026-05-31 154414.png")
M_REALM      = img_path("screenshots2", "Screenshot 2026-05-31 154451.png")
M_ROOFTOP    = img_path("screenshots2", "Screenshot 2026-05-31 154432.png")
M_CAFE       = img_path("screenshots2", "Screenshot 2026-05-31 154459.png")
M_DOCK       = img_path("screenshots2", "Screenshot 2026-05-31 154507.png")
M_BAR        = img_path("screenshots2", "Screenshot 2026-05-31 154530.png")
M_RECEPTION  = img_path("screenshots2", "Screenshot 2026-05-31 154519.png")
M_LECTURE    = img_path("screenshots2", "Screenshot 2026-05-31 154540.png")
M_HOTEL      = img_path("screenshots2", "Screenshot 2026-05-31 154423.png")
M_AXO        = img_path("screenshots2", "Screenshot 2026-06-01 121850.png")
M_SITE       = img_path("screenshots2", "Screenshot 2026-05-31 154253.png")
M_GF         = img_path("screenshots2", "Screenshot 2026-05-31 154307.png")
M_FF         = img_path("screenshots2", "Screenshot 2026-05-31 154320.png")
M_SF         = img_path("screenshots2", "Screenshot 2026-05-31 154328.png")
M_SECT_ANN   = img_path("screenshots2", "Screenshot 2026-05-31 154601.png")
M_SECT_W     = img_path("screenshots2", "Screenshot 2026-05-31 154402.png")
M_SECT_N     = img_path("screenshots2", "section_north.png")
M_EL_S       = img_path("screenshots2", "Screenshot 2026-05-31 154339.png")
M_EL_E       = img_path("screenshots2", "Screenshot 2026-05-31 154345.png")
M_SKETCH     = img_path("screenshots2", "sketch-07.png")

# Old Portsmouth
OP_ANALYSIS  = img_path("screenshots", "Screenshot 2026-05-31 154129.png")
OP_RENDER    = img_path("portfolio-imgs", "portfolio_page-04.png")
OP_PROCESS   = img_path("portfolio-imgs", "portfolio_page-05.png")
OP_CONTEXT   = img_path("portfolio-imgs", "portfolio_page-06.png")
OP_FLOOD     = img_path("screenshots", "flood_risk.png")

# Barnsbury
BN_COVER     = img_path("barnsbury-imgs", "page-1.png")
BN_SITE      = img_path("barnsbury-imgs", "page-2.png")
BN_DEV       = img_path("barnsbury-imgs", "page-5.png")
BN_SECT      = img_path("barnsbury-imgs", "page-6.png")
BN_PLANS     = img_path("barnsbury-imgs", "page-7.png")
BN_EXT       = img_path("barnsbury-imgs", "page-8.png")
BN_INT       = img_path("barnsbury-imgs", "page-9.png")

# Refugee Hub
RF_COVER     = img_path("refugee-imgs", "page-3.png")
RF_RENDER    = img_path("portfolio-imgs", "portfolio_page-12.png")
RF_SKETCHES  = img_path("portfolio-imgs", "portfolio_page-13.png")
RF_ARCHES    = img_path("refugee-imgs", "page-6.png")
RF_PLANS     = img_path("refugee-imgs", "page-5.png")
RF_SECTIONS  = img_path("refugee-imgs", "page-4.png")

# Dissertation
DISS_TRIPTYCH = img_path("portfolio-imgs", "portfolio_page-16.png")

# ─── PAGE BUILDERS ──────────────────────────────────────────────────────────

def cover(c, pg, total):
    """Full-bleed cover with dark overlay and name."""
    place_image(c, M_REALM, 0, 0, W, H, brightness=0.55)
    # Dark gradient overlay - simulate with layered rects
    for i, (alpha, h_pct) in enumerate([(0.2,1.0),(0.3,0.7),(0.5,0.4)]):
        overlay(c, 0, 0, W, H * h_pct, DARK, alpha)

    PAD = 56

    # Rust rule
    rule(c, PAD, 200, 36, RUST)

    # Tag line
    c.saveState()
    set_fill(c, RUST_LIGHT)
    c.setFont("Lato-semibold", 8)
    c.drawString(PAD + 46, 202, "UNDERGRADUATE PORTFOLIO  ·  2022–2026")
    c.restoreState()

    # Name
    c.saveState()
    set_fill(c, WHITE)
    c.setFont("Lato-black", 84)
    c.drawString(PAD, 88, "CONRAD")
    c.setFont("Lato-thin", 84)
    c.drawString(PAD, 8, "TEBJE")
    c.restoreState()

    # Meta strip top-right
    meta = [
        ("QUALIFICATION", "BA (Hons) Architecture"),
        ("INSTITUTION",   "University of Portsmouth"),
        ("PART",          "Part I Architectural Assistant"),
        ("YEAR",          "2026"),
    ]
    mx = W - 360
    my = H - 48
    for key, val in meta:
        c.saveState()
        set_fill(c, LIGHT_TEXT)
        c.setFont("Lato-semibold", 7)
        c.drawRightString(W - 48, my, key)
        c.restoreState()
        c.saveState()
        set_fill(c, WHITE)
        c.setFont("Lato-regular", 9.5)
        c.drawRightString(W - 48, my - 13, val)
        c.restoreState()
        my -= 40
    page_number(c, pg, total)


def contents_page(c, pg, total):
    """Contents spread with project thumbnails."""
    rect(c, 0, 0, W, H, fill_rgb=WHITE)

    PAD = 56
    y_top = H - PAD

    # Label
    rule(c, PAD, y_top - 4, 20, GREEN_MID)
    c.saveState()
    set_fill(c, GREEN_MID)
    c.setFont("Lato-semibold", 7.5)
    c.drawString(PAD + 26, y_top - 2, "CONTENTS")
    c.restoreState()

    # Project list on left
    projects = [
        ("01", "The Berm / Meridian Building", "Major Project  ·  2026"),
        ("02", "Old Portsmouth Masterplan",     "Urban Strategy  ·  2026"),
        ("03", "Barnsbury Park Nursery",         "Education  ·  2024"),
        ("04", "Refugee Hub",                    "Community  ·  2025"),
        ("05", "Dissertation",                   "Research  ·  2026"),
    ]

    list_x = PAD
    list_y = y_top - 56
    for num, title, sub in projects:
        c.saveState()
        set_fill(c, RUST)
        c.setFont("Lato-bold", 7.5)
        c.drawString(list_x, list_y, num)
        set_fill(c, DARK)
        c.setFont("Lato-bold", 12)
        c.drawString(list_x + 24, list_y, title)
        set_fill(c, LIGHT_TEXT)
        c.setFont("Lato-light", 9)
        c.drawString(list_x + 24, list_y - 14, sub)
        c.restoreState()
        # Rule under
        rule(c, list_x, list_y - 22, 340, GREY, thickness=0.5)
        list_y -= 52

    # 4 thumbnails on right (2×2 grid)
    thumb_imgs = [M_EXT, OP_ANALYSIS, BN_COVER, RF_COVER]
    thumb_labels = [
        "The Berm / Meridian Building",
        "Old Portsmouth Masterplan",
        "Barnsbury Park Nursery",
        "Refugee Hub",
    ]
    gx = 400
    thumb_w = (W - gx - PAD - 3) / 2
    thumb_h = (H - 2*PAD - 3) / 2

    for i, (img, lbl) in enumerate(zip(thumb_imgs, thumb_labels)):
        col = i % 2
        row = i // 2
        tx = gx + col * (thumb_w + 3)
        ty = H - PAD - thumb_h - row * (thumb_h + 3)
        place_image(c, img, tx, ty, thumb_w, thumb_h)
        overlay(c, tx, ty, thumb_w, 36, DARK, 0.7)
        c.saveState()
        set_fill(c, WHITE)
        c.setFont("Lato-semibold", 8)
        c.drawString(tx + 10, ty + 12, lbl.upper())
        c.restoreState()

    page_number(c, pg, total)


def chapter_title(c, pg, total, num, title_lines, subtitle, img_path_,
                  brightness=0.45):
    """Full-bleed chapter opener."""
    place_image(c, img_path_, 0, 0, W, H, brightness=brightness)
    # bottom gradient
    for alpha, h in [(0.2,H),(0.35,0.65*H),(0.55,0.4*H),(0.7,0.25*H)]:
        overlay(c, 0, 0, W, h, DARK, alpha)

    PAD = 56
    # Chapter num
    chapter_num_line(c, f"{num}  ·  {subtitle}", PAD, 198)

    # Title
    multiline_heading(c, title_lines, PAD, 148,
                      font="Lato-black", size=54, leading=52)

    # Rust accent line bottom
    rule(c, PAD, 44, 80, RUST, thickness=2)

    page_number(c, pg, total)


def spread_text_image(c, pg, total,
                      label_text, title_lines, body_paras,
                      img_path_, caption="",
                      text_side="left",
                      text_bg=DARK, text_color=(0.7,0.7,0.7),
                      title_color=WHITE, label_color=RUST_LIGHT):
    """Half-text, half-image spread."""
    split = W / 2
    PAD = 48

    if text_side == "left":
        tx, ix = 0, split
    else:
        tx, ix = split, 0

    # Backgrounds
    rect(c, tx, 0, split, H, fill_rgb=text_bg)
    place_image(c, img_path_, ix, 0, split, H)

    if caption:
        overlay(c, ix, 0, split, 30, DARK, 0.65)
        c.saveState()
        set_fill(c, LIGHT_TEXT)
        c.setFont("Lato-lightitalic", 7.5)
        c.drawString(ix + 14, 11, caption)
        c.restoreState()

    # Text content
    content_x = tx + PAD
    content_w  = split - 2 * PAD
    y = H - 64

    # Label
    rule(c, content_x, y + 4, 18, RUST)
    c.saveState()
    set_fill(c, label_color)
    c.setFont("Lato-semibold", 7.5)
    c.drawString(content_x + 24, y, label_text.upper())
    c.restoreState()
    y -= 32

    # Title
    for line in title_lines:
        c.saveState()
        set_fill(c, title_color)
        c.setFont("Lato-black", 22)
        c.drawString(content_x, y, line)
        c.restoreState()
        y -= 25
    y -= 10

    # Body
    for para in body_paras:
        y = body_text(c, para, content_x, y, content_w,
                      size=9.5, rgb=text_color, leading=15, max_h=H - 140)
        y -= 10

    page_number(c, pg, total)


def image_grid(c, pg, total, images, captions=None, bg=DARK, cols=3,
               pad=3, top_pad=0, label_top=None):
    """Grid of images filling the page."""
    rect(c, 0, 0, W, H, fill_rgb=bg)

    if label_top:
        rule(c, 48, H - 32, 18, RUST)
        c.saveState()
        set_fill(c, RUST_LIGHT)
        c.setFont("Lato-semibold", 7.5)
        c.drawString(48 + 24, H - 30, label_top.upper())
        c.restoreState()
        top_pad = 44

    n = len(images)
    rows = (n + cols - 1) // cols
    available_h = H - top_pad - pad * (rows - 1)
    available_w = W - pad * (cols - 1)
    cell_w = available_w / cols
    cell_h = available_h / rows

    for i, img in enumerate(images):
        col = i % cols
        row = i // cols
        x = col * (cell_w + pad)
        y = H - top_pad - (row + 1) * cell_h - row * pad
        place_image(c, img, x, y, cell_w, cell_h)
        if captions and i < len(captions) and captions[i]:
            overlay(c, x, y, cell_w, 24, DARK, 0.7)
            c.saveState()
            set_fill(c, LIGHT_TEXT)
            c.setFont("Lato-lightitalic", 7)
            c.drawString(x + 8, y + 7, captions[i])
            c.restoreState()

    page_number(c, pg, total)


def full_image_page(c, pg, total, img_path_, caption="", brightness=1.0):
    """Single full-bleed image page."""
    place_image(c, img_path_, 0, 0, W, H, brightness=brightness)
    if caption:
        overlay(c, 0, 0, W, 32, DARK, 0.75)
        c.saveState()
        set_fill(c, LIGHT_TEXT)
        c.setFont("Lato-lightitalic", 8)
        c.drawString(48, 11, caption)
        c.restoreState()
    page_number(c, pg, total)


def drawings_page(c, pg, total, images, captions, cols, bg=DARK,
                  section_label="Technical Drawings"):
    """Dark-background drawings page."""
    image_grid(c, pg, total, images, captions=captions, bg=bg, cols=cols,
               label_top=section_label)


def quote_page(c, pg, total, quote, attribution):
    """Full-page quote."""
    rect(c, 0, 0, W, H, fill_rgb=GREEN)
    # Subtle grid
    c.saveState()
    set_stroke(c, (1,1,1))
    c.setLineWidth(0.3)
    c.setStrokeAlpha(0.04)
    for x in range(0, int(W), 60):
        c.line(x, 0, x, H)
    for y in range(0, int(H), 60):
        c.line(0, y, W, y)
    c.restoreState()

    # Rust accent
    rule(c, W/2 - 40, H/2 + 90, 80, RUST, thickness=1.5)

    # Quote text — centered, multi-line
    lines = textwrap.wrap(f'"{quote}"', width=60)
    y = H/2 + 60 + (len(lines) - 1) * 19
    for line in lines:
        c.saveState()
        set_fill(c, (0.9, 0.9, 0.9))
        c.setFont("Lato-lightitalic", 15)
        c.drawCentredString(W/2, y, line)
        c.restoreState()
        y -= 22

    # Attribution
    c.saveState()
    set_fill(c, RUST_LIGHT)
    c.setFont("Lato-semibold", 8)
    c.drawCentredString(W/2, H/2 - 60, attribution.upper())
    c.restoreState()

    page_number(c, pg, total)


def triptych_page(c, pg, total):
    """Dissertation triptych."""
    rect(c, 0, 0, W, H, fill_rgb=WHITE)
    PAD = 56

    # Label
    rule(c, PAD, H - PAD + 6, 20, GREEN_MID)
    c.saveState()
    set_fill(c, GREEN_MID)
    c.setFont("Lato-semibold", 7.5)
    c.drawString(PAD + 26, H - PAD + 8, "DISSERTATION ARTEFACT")
    c.restoreState()

    # Title
    c.saveState()
    set_fill(c, DARK)
    c.setFont("Lato-black", 26)
    c.drawString(PAD, H - PAD - 20, "Triptych Paintings")
    c.restoreSet = c.restoreState
    c.restoreState()

    # Description
    desc = ("Three abstract paintings tracing the Tricorn Centre's emotional "
            "trajectory: from the optimism of its inception, through public "
            "rejection, to the unresolved absence left after demolition. "
            "Acrylic and mixed media, 2026.")
    body_text(c, desc, PAD, H - PAD - 54, W - 2*PAD - 200,
              size=9.5, rgb=MID, leading=14)

    # Panels
    panel_y = 40
    panel_h = H - PAD - 95 - panel_y
    panel_w = (W - 2*PAD - 2*6) / 3
    panels = [
        ("I — Brave New World",    RUST_LIGHT),
        ("II — Rejection & Rupture", MID),
        ("III — Void & Memory",      (0.5,0.5,0.5)),
    ]

    # Use triptych image (full row) if it exists, otherwise split
    if os.path.exists(DISS_TRIPTYCH):
        place_image(c, DISS_TRIPTYCH, PAD, panel_y, W - 2*PAD, panel_h, fit="contain")
    else:
        for i, (lbl, col) in enumerate(panels):
            px = PAD + i * (panel_w + 6)
            rect(c, px, panel_y, panel_w, panel_h, fill_rgb=GREY)
            c.saveState()
            set_fill(c, col)
            c.setFont("Lato-bold", 8)
            c.drawString(px + 10, panel_y + 10, lbl.upper())
            c.restoreState()

    # Panel labels underneath
    for i, (lbl, col) in enumerate(panels):
        px = PAD + i * (panel_w + 6)
        c.saveState()
        set_fill(c, MID)
        c.setFont("Lato-light", 8.5)
        c.drawString(px, panel_y - 14, lbl)
        c.restoreState()

    page_number(c, pg, total)


def dissertation_spread(c, pg, total):
    """Dissertation text spread."""
    split = W * 0.45
    rect(c, 0, 0, split, H, fill_rgb=WHITE)
    rect(c, split, 0, W - split, H, fill_rgb=DARK)

    PAD = 48
    y = H - 64

    # Label left
    rule(c, PAD, y + 4, 20, GREEN_MID)
    c.saveState()
    set_fill(c, GREEN_MID)
    c.setFont("Lato-semibold", 7.5)
    c.drawString(PAD + 26, y, "RESEARCH")
    c.restoreState()
    y -= 32

    # Title left
    for line in ["Reframing", "Brutalism"]:
        c.saveState()
        set_fill(c, DARK)
        c.setFont("Lato-black", 30)
        c.drawString(PAD, y, line)
        c.restoreState()
        y -= 34
    y -= 6

    body_text(c, "Portsmouth's Tricorn Centre opened in 1966 as one of Britain's most ambitious Brutalist buildings. By 2001 it was voted the ugliest building in the country. It was demolished in 2004.",
              PAD, y, split - 2*PAD, size=9.5, rgb=MID, leading=15)
    y -= 72

    body_text(c, "This dissertation argues that the Tricorn's failure was not inherent to its architecture, but the product of poor siting, long-term neglect, and cumulative hostile media framing. Drawing on archival newspaper research at Portsmouth History Centre, the study reconstructs how public hatred was gradually constructed over decades — until the building became a scapegoat for anxieties that had nothing to do with concrete.",
              PAD, y, split - 2*PAD, size=9.5, rgb=MID, leading=15)
    y -= 110

    body_text(c, "Demolition is so often a response to neglect rather than design. Narrative shapes the reception of a place, and once written, it is very hard to unwrite.",
              PAD, y, split - 2*PAD, size=9.5, rgb=(0.35,0.35,0.35), leading=15)

    # Right side — styled dissertation title card
    rx = split + PAD
    ry = H/2 + 80

    rule(c, rx, ry + 4, 18, RUST)
    c.saveState()
    set_fill(c, RUST_LIGHT)
    c.setFont("Lato-semibold", 7)
    c.drawString(rx + 24, ry, "DISSERTATION  ·  UNIVERSITY OF PORTSMOUTH  ·  2026")
    c.restoreState()
    ry -= 30

    for line in ["Reframing Brutalism:", "The Tricorn Centre", "and Public Perception"]:
        c.saveState()
        set_fill(c, WHITE)
        c.setFont("Lato-bold", 18)
        c.drawString(rx, ry, line)
        c.restoreState()
        ry -= 22
    ry -= 12

    body_text(c, "Conrad Tebje · BA (Hons) Architecture · 2026",
              rx, ry, W - split - 2*PAD, size=9, rgb=LIGHT_TEXT, leading=14)

    page_number(c, pg, total)


# ─── BUILD ──────────────────────────────────────────────────────────────────

TOTAL = 20

c = canvas.Canvas(OUT, pagesize=(W, H))
c.setTitle("Conrad Tebje — Undergraduate Portfolio 2026")
c.setAuthor("Conrad Tebje")
c.setSubject("Part I Architectural Assistant Portfolio")

pg = 1

# 1. Cover
cover(c, pg, TOTAL); c.showPage(); pg += 1

# 2. Contents
contents_page(c, pg, TOTAL); c.showPage(); pg += 1

# ── 01 MERIDIAN ──────────────────────────────────────────

# 3. Chapter title
chapter_title(c, pg, TOTAL,
    num="01",
    title_lines=["THE BERM /", "MERIDIAN BUILDING"],
    subtitle="Major Project · Phase 2 · 2026",
    img_path_=M_EXT,
    brightness=0.45)
c.showPage(); pg += 1

# 4. Overview spread
spread_text_image(c, pg, TOTAL,
    label_text="Overview",
    title_lines=["A building that gives back", "more than it takes"],
    body_paras=[
        "A civic maritime hub on Portsmouth's southern waterfront, occupying a historically sensitive site at The Hard — the threshold between the naval dockyard and the city.",
        "Three marine environmental charities occupy public galleries alongside a shared research workshop, wet lab, and internal dock. Visitors can observe active research directly.",
        "A green berm rises from the public realm, forming a continuous accessible roof. Materials are drawn from the industrial waterfront: GGBS concrete, corten steel, and timber. Nothing was chosen for effect alone.",
    ],
    img_path_=M_REALM,
    caption="Public realm and amphitheatre, looking south",
    text_side="left")
c.showPage(); pg += 1

# 5. Interior renders grid
image_grid(c, pg, TOTAL,
    images=[M_CAFE, M_DOCK, M_BAR, M_RECEPTION, M_LECTURE, M_HOTEL],
    captions=["Cafe and atrium","Internal dock and workshop","Bar","Reception","Lecture theatre","Residential apartment"],
    cols=3, label_top="Interior Renders")
c.showPage(); pg += 1

# 6. Concept spread
spread_text_image(c, pg, TOTAL,
    label_text="Concept & Process",
    title_lines=["Design", "Development"],
    body_paras=[
        "The design began with the ground. The berm is not a formal device — it responds to flood risk, creates a continuous public roof, and screens the dock from street noise without closing it off.",
        "Early work focused on the relationship between the research wing and the public galleries. Several configurations were tested before settling on a lateral arrangement keeping research and exhibition genuinely adjacent.",
        "The exploded axonometric shows programme layering: dock and workshop at the lowest level, research and gallery floors above, residential and hospitality stepping back, and the berm as a continuous surface tying everything together.",
    ],
    img_path_=M_AXO,
    caption="Exploded axonometric — programme layering",
    text_side="right")
c.showPage(); pg += 1

# 7. Plans grid
image_grid(c, pg, TOTAL,
    images=[M_SITE, M_GF, M_FF, M_SF],
    captions=["Site plan","Ground floor plan","First floor plan","Second floor plan"],
    cols=2, bg=(0.06, 0.06, 0.06), label_top="Plans")
c.showPage(); pg += 1

# 8. Sections grid
image_grid(c, pg, TOTAL,
    images=[M_SECT_W, M_SECT_N, M_EL_S, M_EL_E],
    captions=["West-facing section","North-facing section","South elevation","East elevation"],
    cols=2, bg=(0.06, 0.06, 0.06), label_top="Sections & Elevations")
c.showPage(); pg += 1

# ── 02 OLD PORTSMOUTH ────────────────────────────────────

# 9. Chapter title
chapter_title(c, pg, TOTAL,
    num="02",
    title_lines=["OLD PORTSMOUTH", "MASTERPLAN"],
    subtitle="Major Project · Phase 1 · Team Lead · 2026",
    img_path_=OP_ANALYSIS,
    brightness=0.4)
c.showPage(); pg += 1

# 10. Overview spread
spread_text_image(c, pg, TOTAL,
    label_text="Urban Strategy",
    title_lines=["Releasing the waterfront", "for public use"],
    body_paras=[
        "Phase 1 was a team-led masterplanning exercise for Old Portsmouth. I interpreted the brief, organised workflow, and guided key design decisions across a site encompassing the entirety of Old Portsmouth.",
        "The masterplan centred on selective removal: the SubseaCraft office building and the Wightlink terminal were identified as structures occupying prime waterfront land without contributing public value.",
        "The proposal introduced a research centre, education facility, gallery, pavilion, market space, social hub, and residential zone — a sequence of uses designed to generate activity across the full day. This phase directly shaped the site and programme for Phase 2.",
    ],
    img_path_=OP_RENDER,
    caption="Exterior concept render — initial massing study",
    text_side="left")
c.showPage(); pg += 1

# 11. Process + context grid
image_grid(c, pg, TOTAL,
    images=[OP_PROCESS, OP_CONTEXT, OP_ANALYSIS, OP_FLOOD],
    captions=["Design progression","Concept in context","Site analysis boards","Flood risk analysis"],
    cols=2, label_top="Analysis & Development")
c.showPage(); pg += 1

# ── 03 BARNSBURY ─────────────────────────────────────────

# 12. Chapter title
chapter_title(c, pg, TOTAL,
    num="03",
    title_lines=["BARNSBURY PARK", "NURSERY"],
    subtitle="Education Design · November 2024",
    img_path_=BN_COVER,
    brightness=0.45)
c.showPage(); pg += 1

# 13. Overview spread
spread_text_image(c, pg, TOTAL,
    label_text="Overview",
    title_lines=["Designed for the people", "who will actually use it"],
    body_paras=[
        "A new nursery within Barnsbury Park, Eastney — low-rise, timber-clad, sized for children rather than adults. Montessori and Waldorf Steiner pedagogy shaped the design approach.",
        "Rooms flow into each other rather than separating behind closed doors — baby area, toddler space, preschooler room, staff facilities — with a first-floor outdoor deck extending usable area without increasing the footprint.",
        "Portholes in the boundary wall sit at child height. Nooks scaled for hiding, a raised platform for movement, and a pastel ground plane suggesting play without prescribing it.",
    ],
    img_path_=BN_EXT,
    caption="Exterior — play courtyard and covered walkway",
    text_side="right",
    text_bg=WHITE,
    text_color=MID,
    title_color=DARK,
    label_color=GREEN_MID)
c.showPage(); pg += 1

# 14. Drawings grid
image_grid(c, pg, TOTAL,
    images=[BN_SITE, BN_DEV, BN_SECT, BN_PLANS, BN_INT],
    captions=["Site analysis","Design development","Technical sections","Plans & elevations","Interior renders"],
    cols=3, bg=(0.06,0.06,0.06), label_top="Documentation")
c.showPage(); pg += 1

# ── 04 REFUGEE HUB ───────────────────────────────────────

# 15. Chapter title
chapter_title(c, pg, TOTAL,
    num="04",
    title_lines=["REFUGEE HUB"],
    subtitle="Community Design · May 2025",
    img_path_=RF_COVER,
    brightness=0.4)
c.showPage(); pg += 1

# 16. Overview spread
spread_text_image(c, pg, TOTAL,
    label_text="Narrative & Concept",
    title_lines=["An oasis at the end", "of a long journey"],
    body_paras=[
        "The brief placed heavy emphasis on narrative — understanding as deeply as possible what the users of this building have been through to get here.",
        "Inspired by Francis Alÿs' Sometimes Making Something Leads to Nothing, a mapping exercise translated the refugee journey into physical form: erosion of identity along the way, roots that can grow again at the destination.",
        "A long corridor with repeating undulating arches references the journey itself. Gathering spaces face south. The residential block sits at the quietest point. Public space transitions to private space through materials: concrete to wood, open to enclosed.",
    ],
    img_path_=RF_ARCHES,
    caption="Arch corridor — public entrance sequence",
    text_side="left")
c.showPage(); pg += 1

# 17. Renders + drawings grid
image_grid(c, pg, TOTAL,
    images=[RF_RENDER, RF_SKETCHES, RF_PLANS, RF_SECTIONS],
    captions=["Exterior render","Narrative model & sketches","Floor plans & courtyard","Sections"],
    cols=2, label_top="Documentation")
c.showPage(); pg += 1

# ── 05 DISSERTATION ──────────────────────────────────────

# 18. Chapter title
chapter_title(c, pg, TOTAL,
    num="05",
    title_lines=["REFRAMING", "BRUTALISM"],
    subtitle="Dissertation · January 2026",
    img_path_=BN_SITE,   # use a textural image
    brightness=0.2)
c.showPage(); pg += 1

# 19. Dissertation spread
dissertation_spread(c, pg, TOTAL)
c.showPage(); pg += 1

# 20. Triptych
triptych_page(c, pg, TOTAL)
c.showPage(); pg += 1

c.save()
print(f"✓  Saved to {OUT}")
print(f"   {pg - 1} pages, A3 landscape")
