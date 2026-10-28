"""File and calculator helpers for the Telegram bot.

This file does NOT talk to Telegram. It only turns bytes into bytes, so it is
easy to test on its own.
"""
import io
import secrets
import string

from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter

MAX_PDF_PAGES = 300


class UserError(Exception):
    """An error whose message is safe to show to the user."""


# ---------------------------------------------------------------- images
def open_image(data):
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:
        raise UserError("I could not read that image. Please send a JPG, PNG or WebP file.")
    # phones store rotation in EXIF; apply it so the picture is upright
    return ImageOps.exif_transpose(img)


def flatten(img):
    """Convert to plain RGB, putting transparent areas on a white background."""
    if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
        rgba = img.convert("RGBA")
        bg = Image.new("RGB", rgba.size, (255, 255, 255))
        bg.paste(rgba, mask=rgba.split()[-1])
        return bg
    return img.convert("RGB")


def convert_image(data, fmt, quality=90):
    """fmt is 'PNG', 'JPEG' or 'WEBP'. Returns bytes."""
    fmt = fmt.upper()
    if fmt not in ("PNG", "JPEG", "WEBP"):
        raise UserError("Unknown format.")
    img = open_image(data)
    out = io.BytesIO()
    if fmt == "JPEG":
        flatten(img).save(out, "JPEG", quality=quality, optimize=True)
    elif fmt == "WEBP":
        img.convert("RGBA" if "A" in img.getbands() else "RGB").save(out, "WEBP", quality=quality)
    else:
        img.save(out, "PNG", optimize=True)
    return out.getvalue()


def compress_image(data, max_side=1600, quality=65):
    img = flatten(open_image(data))
    img.thumbnail((max_side, max_side))
    out = io.BytesIO()
    img.save(out, "JPEG", quality=quality, optimize=True)
    return out.getvalue()


def images_to_pdf(list_of_bytes):
    if not list_of_bytes:
        raise UserError("No images to convert.")
    imgs = [flatten(open_image(b)) for b in list_of_bytes]
    out = io.BytesIO()
    imgs[0].save(out, "PDF", save_all=True, append_images=imgs[1:], resolution=150.0)
    return out.getvalue()


# ------------------------------------------------------------------ pdfs
def _reader(data):
    try:
        r = PdfReader(io.BytesIO(data))
        if r.is_encrypted:
            raise UserError("That PDF is password protected, so I cannot open it.")
        if len(r.pages) > MAX_PDF_PAGES:
            raise UserError("That PDF has more than %d pages." % MAX_PDF_PAGES)
        return r
    except UserError:
        raise
    except Exception:
        raise UserError("I could not open that PDF. It may be damaged.")


def page_count(data):
    return len(_reader(data).pages)


def merge_pdfs(list_of_bytes):
    if len(list_of_bytes) < 2:
        raise UserError("Send at least two PDFs to merge.")
    w = PdfWriter()
    for b in list_of_bytes:
        for p in _reader(b).pages:
            w.add_page(p)
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


def parse_ranges(text, max_pages):
    """'1-3, 5' -> [0, 1, 2, 4]. Raises UserError when the text is not valid."""
    out = []
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        a, _, b = part.partition("-")
        if not a.isdigit() or (b and not b.isdigit()):
            raise UserError("I did not understand the pages. Use numbers like 1-3,5")
        start = int(a)
        end = int(b) if b else start
        if start < 1 or end < start or end > max_pages:
            raise UserError("Pages must be between 1 and %d." % max_pages)
        out.extend(range(start - 1, end))
    if not out:
        raise UserError("I did not understand the pages. Use numbers like 1-3,5")
    return out


def extract_pages(data, indices):
    r = _reader(data)
    w = PdfWriter()
    for i in indices:
        w.add_page(r.pages[i])
    out = io.BytesIO()
    w.write(out)
    return out.getvalue()


# ------------------------------------------------------------ small tools
def make_qr(text):
    import qrcode  # imported here so the other tools work even without it

    if len(text) > 1000:
        raise UserError("That text is too long for a QR code.")
    img = qrcode.make(text)
    out = io.BytesIO()
    img.save(out, "PNG")
    return out.getvalue()


def make_password(length=14, symbols=True):
    if not 8 <= length <= 64:
        raise UserError("Password length must be between 8 and 64.")
    chars = "abcdefghijkmnopqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    if symbols:
        chars += "!@#$%^&*-_?"
    return "".join(secrets.choice(chars) for _ in range(length))


def percent(obtained, total):
    if total <= 0:
        raise UserError("Total marks must be more than zero.")
    return obtained / total * 100


def cgpa_to_percent(cgpa, multiplier=9.5):
    return cgpa * multiplier


def grams_needed(mol_weight, molarity, volume_ml):
    if mol_weight <= 0 or molarity < 0 or volume_ml <= 0:
        raise UserError("Please use positive numbers.")
    return molarity * mol_weight * volume_ml / 1000.0
