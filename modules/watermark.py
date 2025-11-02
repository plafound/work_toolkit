import os
import pikepdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import Color, black
from io import BytesIO

BASE = "workspace/watermark"
INPUT_DIR = os.path.join(BASE, "input")
OUTPUT_DIR = os.path.join(BASE, "output")
TEMPLATE_DIR = os.path.join(BASE, "template")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)

WMAP = {
    "A4L": "wm_a4_landscape.png",
    "A4P": "wm_a4_portrait.png",
    "F4L": "wm_f4_landscape.png",
    "F4P": "wm_f4_portrait.png",
}

A4_RATIO = 297.0 / 210.0
F4_RATIO = 330.0 / 210.0
RATIO_TOLERANCE = 0.04


def box_size(box):
    return abs(float(box[2]) - float(box[0])), abs(float(box[3]) - float(box[1]))


def detect_size(page):
    box = page.obj.get("/CropBox") or page.obj.get("/MediaBox")
    w, h = box_size(box)
    ratio = max(w, h) / (min(w, h) or 1)
    if abs(ratio - A4_RATIO) <= RATIO_TOLERANCE:
        return "A4P" if h > w else "A4L"
    if abs(ratio - F4_RATIO) <= RATIO_TOLERANCE:
        return "F4P" if h > w else "F4L"
    return "A4P"


def generate_text_watermark(text, width, height):
    """Buat watermark dari teks dan kembalikan BytesIO berisi PDF"""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont("Helvetica-Bold", min(width, height) * 0.07)
    c.setFillColor(Color(0.5, 0.5, 0.5, alpha=0.2))
    c.saveState()
    c.translate(width / 2, height / 2)
    c.rotate(45)
    c.drawCentredString(0, 0, text)
    c.restoreState()
    c.showPage()
    c.save()
    buf.seek(0)
    return buf


def add_watermark(page, wm_img=None, text=None):
    """Tambahkan watermark ke halaman"""
    buf = BytesIO()
    w, h = box_size(page.obj.get("/MediaBox"))
    c = canvas.Canvas(buf, pagesize=(w, h))

    if wm_img and os.path.exists(wm_img):
        # Gunakan file watermark yang sudah ada
        img = ImageReader(wm_img)
        iw, ih = img.getSize()
        ratio = iw / ih
        new_w, new_h = (w, w / ratio) if ratio < w / h else (h * ratio, h)
        c.drawImage(wm_img, (w - new_w) / 2, (h - new_h) / 2, new_w, new_h, mask='auto')
    else:
        # Buat watermark dari teks
        wm_buf = generate_text_watermark(text or "WATERMARK", w, h)
        wm_pdf = pikepdf.Pdf.open(wm_buf)
        page.add_overlay(wm_pdf.pages[0])
        return  # langsung return, overlay sudah ditambahkan

    c.showPage()
    c.save()
    buf.seek(0)
    wm_pdf = pikepdf.Pdf.open(buf)
    page.add_overlay(wm_pdf.pages[0])


def run_watermark():
    print("=== WATERMARK PDF ===")

    files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    if not files:
        print("❌ Tidak ada file PDF di folder input.")
        return

    # Cek apakah template ada
    has_template = any(os.path.exists(os.path.join(TEMPLATE_DIR, f)) for f in WMAP.values())
    text_wm = None
    if not has_template:
        text_wm = input("Masukkan teks watermark (contoh: DOKUMEN RAHASIA): ").strip() or "WATERMARK"

    for f in files:
        inp, outp = os.path.join(INPUT_DIR, f), os.path.join(OUTPUT_DIR, f)
        with pikepdf.open(inp) as pdf:
            for p in pdf.pages:
                sz = detect_size(p)
                wm_file = os.path.join(TEMPLATE_DIR, WMAP[sz])
                add_watermark(p, wm_file if has_template else None, text=text_wm)
            pdf.save(outp)
        print("✅", f)

    print("\nSelesai! File hasil ada di folder output.")