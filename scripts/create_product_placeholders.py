"""
Create placeholder product images so /static/images/products/*.jpg exist.
Run from project root: python scripts/create_product_placeholders.py
Uses data/seed_data/product_images_placeholder.csv for filenames and alt_text.
"""
import csv
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Install Pillow: pip install Pillow")
    raise SystemExit(1)

# Project root (parent of scripts/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SEED_CSV = PROJECT_ROOT / "data" / "seed_data" / "product_images_placeholder.csv"
OUT_DIR = PROJECT_ROOT / "static" / "images" / "products"

# Placeholder image size and style
W, H = 600, 600
BG = (245, 242, 240)  # off-white
TEXT_COLOR = (100, 100, 100)
ACCENT = (111, 143, 114)  # sage


def main():
    if not SEED_CSV.exists():
        print(f"Not found: {SEED_CSV}")
        return
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(SEED_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        # image_url is e.g. /static/images/products/riverside-cotton-tee_1.jpg
        url = row.get("image_url", "").strip()
        if not url:
            continue
        filename = os.path.basename(url)
        if not filename.lower().endswith(".jpg"):
            continue
        alt = (row.get("alt_text") or "Product image").strip()
        filepath = OUT_DIR / filename

        img = Image.new("RGB", (W, H), BG)
        draw = ImageDraw.Draw(img)
        # Bottom accent bar (fashion placeholder style)
        bar_h = 80
        draw.rectangle([0, H - bar_h, W, H], fill=ACCENT)
        # Text: use default font, keep it short
        label = alt.replace(" image 1", "").replace(" image 2", "").strip()
        if len(label) > 28:
            label = label[:25] + "..."
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except OSError:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
            except OSError:
                font = ImageFont.load_default()
        # Center text in upper area
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        tx = (W - tw) // 2
        ty = (H - bar_h - th) // 2
        draw.text((tx, ty), label, fill=TEXT_COLOR, font=font)

        img.save(filepath, "JPEG", quality=85)
        print(f"  {filename}")

    print(f"Created {len(rows)} placeholder images in {OUT_DIR}")


if __name__ == "__main__":
    main()
