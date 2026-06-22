#!/usr/bin/env python3
"""
Envelope Label Generator — 6×4 Landscape drawn, rotated CCW for 4×6 printing
Usage:
  python envelope_label.py                  # normal, return address locked
  python envelope_label.py --change-return  # lets you edit return address
"""

from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from pypdf import PdfReader, PdfWriter
import os, sys

# ── YOUR RETURN ADDRESS (edit once, leave forever) ───────────────────────────
DEFAULT_RETURN = {
    "name":     "Jeff Tagle",
    "business": "RxRares",
    "line1":    "7 Washington Way",
    "line2":    "",
    "city":     "Swedesboro",
    "state":    "NJ",
    "zip":      "08085",
}

DEFAULT_OUTPUT = "envelope_label.pdf"

# ── ADDRESS PARSING ───────────────────────────────────────────────────────────

def parse_pasted_address(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if lines and lines[-1].upper() in ("US", "USA", "UNITED STATES"):
        lines = lines[:-1]
    if len(lines) < 2:
        return None

    name      = lines[0]
    city_line = lines[-1]
    city, state, zip_ = "", "", ""

    if "," in city_line:
        parts = city_line.split(",", 1)
        city  = parts[0].strip()
        rest  = parts[1].strip().split()
        if len(rest) >= 2:
            state = rest[0]
            zip_  = rest[1]
        elif len(rest) == 1:
            state = rest[0]
    else:
        parts = city_line.split()
        if len(parts) >= 3:
            zip_  = parts[-1]
            state = parts[-2]
            city  = " ".join(parts[:-2])

    street_lines = lines[1:-1]
    line1 = street_lines[0] if street_lines else ""
    line2 = street_lines[1] if len(street_lines) > 1 else ""

    return {"name": name, "business": "", "line1": line1, "line2": line2,
            "city": city, "state": state, "zip": zip_}

# ── PROMPTS ───────────────────────────────────────────────────────────────────

def prompt_recipient():
    print("\n── Recipient Address ──")
    print("  Paste TCGPlayer address block then hit Enter on a blank line,")
    print("  or press Enter now to type field by field.\n")

    first = input("  > ").strip()

    if not first:
        def ask(prompt):
            return input(f"  {prompt}: ").strip()
        return {
            "name":     ask("Name"),
            "business": ask("Business (optional)"),
            "line1":    ask("Street address"),
            "line2":    ask("Apt/Suite (optional)"),
            "city":     ask("City"),
            "state":    ask("State (2-letter)"),
            "zip":      ask("ZIP code"),
        }

    pasted = first + "\n"
    while True:
        line = input("  > ")
        if line.strip() == "":
            break
        pasted += line + "\n"

    result = parse_pasted_address(pasted)
    if result:
        print(f"\n  Parsed:")
        print(f"    Name:   {result['name']}")
        print(f"    Street: {result['line1']}" + (f" / {result['line2']}" if result['line2'] else ""))
        print(f"    City:   {result['city']}, {result['state']} {result['zip']}")
        confirm = input("\n  Looks good? [Y/n]: ").strip().lower()
        if confirm in ("", "y", "yes"):
            return result

    print("  Re-enter manually.")
    return prompt_recipient()


def prompt_return():
    r = DEFAULT_RETURN.copy()
    def ask(prompt, key):
        val = input(f"  {prompt} [{r.get(key,'')}]: ").strip()
        return val if val else r.get(key, "")
    print("\n── Return Address ──")
    r["name"]     = ask("Name",      "name")
    r["business"] = ask("Business",  "business")
    r["line1"]    = ask("Street",    "line1")
    r["line2"]    = ask("Apt/Suite", "line2")
    r["city"]     = ask("City",      "city")
    r["state"]    = ask("State",     "state")
    r["zip"]      = ask("ZIP",       "zip")
    return r


def format_city_line(addr):
    return f"{addr['city']}, {addr['state']} {addr['zip']}"


# ── PDF GENERATION ────────────────────────────────────────────────────────────
# Draw in landscape (6w × 4h), then rotate the page CCW so the printer
# sees a portrait 4w × 6h page and maps it correctly to a 4×6 label.

def generate_label(return_addr, recipient_addr, output_path):
    # Draw landscape: W=6", H=4"
    W, H = 6 * inch, 4 * inch
    c = canvas.Canvas(output_path, pagesize=(W, H))

    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── RETURN ADDRESS — top left ─────────────────────────────────────────────
    ret_lines = [return_addr["name"]]
    if return_addr.get("business"):
        ret_lines.append(return_addr["business"])
    ret_lines.append(return_addr["line1"])
    if return_addr.get("line2"):
        ret_lines.append(return_addr["line2"])
    ret_lines.append(format_city_line(return_addr))

    rx, ry = 0.25 * inch, H - 0.40 * inch
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.black)
    for line in ret_lines:
        c.drawString(rx, ry, line)
        ry -= 15

    # ── STAMP PLACEHOLDER — top right ────────────────────────────────────────
    sw, sh = 0.85 * inch, 0.95 * inch
    sx = W - sw - 0.20 * inch
    sy = H - sh - 0.20 * inch
    c.setStrokeColor(colors.HexColor("#999999"))
    c.setLineWidth(0.75)
    c.setDash(3, 3)
    c.rect(sx, sy, sw, sh)
    c.setDash()
    c.setStrokeColor(colors.HexColor("#CCCCCC"))
    c.setLineWidth(0.4)
    for yy in [sy + sh * 0.35, sy + sh * 0.65]:
        c.line(sx + 0.08 * inch, yy, sx + sw - 0.08 * inch, yy)
    c.setFont("Helvetica", 5.5)
    c.setFillColor(colors.HexColor("#888888"))
    c.drawCentredString(sx + sw / 2, sy + sh / 2 - 3,  "PLACE")
    c.drawCentredString(sx + sw / 2, sy + sh / 2 - 10, "STAMP")
    c.drawCentredString(sx + sw / 2, sy + sh / 2 - 17, "HERE")

    # ── RECIPIENT ADDRESS — all caps, centered ────────────────────────────────
    rec_lines = [recipient_addr["name"].upper()]
    if recipient_addr.get("business"):
        rec_lines.append(recipient_addr["business"].upper())
    rec_lines.append(recipient_addr["line1"].upper())
    if recipient_addr.get("line2"):
        rec_lines.append(recipient_addr["line2"].upper())
    rec_lines.append(format_city_line(recipient_addr).upper())

    REC_FONT, REC_SIZE, LINE_H = "Helvetica", 11.5, 15
    c.setFont(REC_FONT, REC_SIZE)
    max_w   = max(c.stringWidth(l, REC_FONT, REC_SIZE) for l in rec_lines)
    block_x = (W - max_w) / 2
    total_h = len(rec_lines) * LINE_H
    start_y = (H / 2) + (total_h / 2) - LINE_H * 0.5

    c.setFillColor(colors.black)
    for i, line in enumerate(rec_lines):
        c.drawString(block_x, start_y - i * LINE_H, line)

    c.save()


# ── ROTATE PAGE 90° CCW ───────────────────────────────────────────────────────

def rotate_pdf_ccw(path):
    reader = PdfReader(path)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(-90)
        writer.add_page(page)
    with open(path, "wb") as f:
        writer.write(f)


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    change_return = "--change-return" in sys.argv

    print("=" * 48)
    print("  Envelope Label Generator  (6×4 → rotated 4×6)")
    print("=" * 48)

    return_addr    = prompt_return() if change_return else DEFAULT_RETURN
    recipient_addr = prompt_recipient()

    out = input(f"\nOutput filename [{DEFAULT_OUTPUT}]: ").strip()
    if not out:
        out = DEFAULT_OUTPUT
    if not out.endswith(".pdf"):
        out += ".pdf"

    generate_label(return_addr, recipient_addr, out)
    rotate_pdf_ccw(out)
    print(f"\n✓ Label saved to: {os.path.abspath(out)}")


if __name__ == "__main__":
    main()