import os
from pathlib import Path
from pikepdf import Pdf
from PIL import Image, ImageOps
import fitz  # PyMuPDF
import tempfile

# ========================
#   FOLDER SETUP
# ========================
INPUT_DIR = Path("workspace/compress/input")
OUTPUT_DIR = Path("workspace/compress/output")
INPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ========================
#   COMPRESS PDF (ASLI)
# ========================
def compress_images_in_pdf(input_path, output_path, level=5):
    """
    level 1 = kualitas tinggi (kompres sedikit)
    level 9 = kualitas rendah (kompres maksimal)
    """
    quality = max(10, 100 - (level * 10))  # misal level 5 → kualitas 50%

    doc = fitz.open(input_path)
    temp_pdf = fitz.open()

    for page_index in range(len(doc)):
        page = doc.load_page(page_index)
        pix = page.get_pixmap(dpi=150)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_img:
            img_path = tmp_img.name

        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.save(img_path, quality=quality, optimize=True)

        img_doc = fitz.open(img_path)
        rect = img_doc[0].rect
        pdfbytes = img_doc.convert_to_pdf()
        img_pdf = fitz.open("pdf", pdfbytes)

        new_page = temp_pdf.new_page(width=rect.width, height=rect.height)
        new_page.show_pdf_page(rect, img_pdf, 0)

        img_doc.close()
        os.remove(img_path)

    temp_pdf.save(output_path)
    temp_pdf.close()
    doc.close()


def compress_pdf_menu():
    pdf_files = list(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print("⚠️  Tidak ada file PDF di folder input.")
        input("\nTekan ENTER untuk kembali...")
        return

    print("=== KOMPRESS PDF ===")
    print("Level kompresi (1 = ringan, 9 = maksimal): ", end="")

    try:
        level = int(input().strip())
        if not (1 <= level <= 9):
            raise ValueError
    except ValueError:
        print("❌ Level tidak valid. Gunakan angka 1–9.")
        input("\nTekan ENTER untuk kembali...")
        return

    for file in pdf_files:
        outpath = OUTPUT_DIR / file.name
        print(f"🔧 Mengompres: {file.name} (level {level})...")

        try:
            compress_images_in_pdf(file, outpath, level)
            print(f"✅ {file.name} selesai → {outpath.name}")
        except Exception as e:
            print(f"❌ Gagal kompres {file.name}: {e}")

    input("\nTekan ENTER untuk kembali...")


# ========================
#       COMPRESS IMAGE
# ========================
def compress_images(max_kb, auto_resize):
    print("\nMemulai kompres gambar...\n")

    image_files = sorted([
        f for f in INPUT_DIR.iterdir()
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ])

    if not image_files:
        print("⚠️ Tidak ada file gambar di folder input.")
        input("\nTekan ENTER untuk kembali...")
        return

    for file in image_files:
        in_path = file
        # default output name = same filename; but if we convert PNG->JPG we rename
        out_name = file.name
        out_path = OUTPUT_DIR / out_name

        try:
            img = Image.open(in_path)

            # Apply EXIF orientation so image is upright (fix auto-rotate issues)
            try:
                img = ImageOps.exif_transpose(img)
            except Exception:
                # fallback: ignore if exif not present or error
                pass

            # If PNG has alpha -> convert to RGB and change extension to .jpg
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
                out_name = file.stem + ".jpg"
                out_path = OUTPUT_DIR / out_name

            quality = 95
            step = 5
            width, height = img.size
            last_size_kb = None

            # Loop compress: quality first, with optional auto-resize between iterations
            while True:
                # prepare image to save (maybe resized)
                if auto_resize and (width > 300 or height > 300):
                    # only downscale when necessary to help reach target size
                    tmp_img = img.resize((width, height), Image.LANCZOS)
                else:
                    tmp_img = img

                # Save to out_path with current quality
                tmp_img.save(out_path, "JPEG", quality=quality, optimize=True)
                size_kb = os.path.getsize(out_path) // 1024
                last_size_kb = size_kb

                # stop conditions
                if size_kb <= max_kb or quality <= 20:
                    break

                # reduce quality
                quality -= step

                # if quality is low and still too large, reduce resolution for next loop
                if quality <= 30 and auto_resize:
                    width = int(width * 0.9)
                    height = int(height * 0.9)
                    if width < 50 or height < 50:
                        # prevent too tiny
                        break

            print(f"✅ {out_name} → {last_size_kb} KB")

        except Exception as e:
            print(f"❌ Gagal memproses {file.name}: {e}")


def compress_image_menu():
    # First: check if there are image files BEFORE asking user for inputs
    image_files_exist = any(
        True for f in INPUT_DIR.iterdir() if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
    )
    if not image_files_exist:
        print("⚠️ Tidak ada file gambar di folder input.")
        input("\nTekan ENTER untuk kembali...")
        return

    print("=== COMPRESS IMAGE ===\n")

    # Target ukuran
    try:
        max_kb = int(input("Masukkan target ukuran (KB): ").strip())
    except:
        print("❌ Input tidak valid.")
        input("\nTekan ENTER untuk kembali...")
        return

    print("\nMode Resize:")
    print("1. Auto Resize (mengecilkan resolusi jika perlu)")
    print("2. Keep Resolution (hanya menurunkan kualitas)")

    mode = input("\nPilih mode: ").strip()
    auto_resize = (mode == "1")

    compress_images(max_kb, auto_resize)
    input("\nTekan ENTER untuk kembali...")


# ========================
#       MENU COMPRESS
# ========================
def run_compress():
    while True:
        os.system("cls" if os.name == "nt" else "clear")
        print("=== COMPRESS MENU ===\n")
        print("1. Compress PDF")
        print("2. Compress Image")
        print("0. Kembali")

        choice = input("\nPilih menu: ").strip()

        if choice == "1":
            compress_pdf_menu()

        elif choice == "2":
            compress_image_menu()

        elif choice == "0":
            return

        else:
            input("Pilihan tidak valid. Tekan ENTER...")