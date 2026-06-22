#!/usr/bin/env python3
"""
Envelope Label Generator — 6×4 Landscape, stamps.com style
Usage: python envelope_label.py
"""

from reportlab.lib.pagesizes import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
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

# ── HELPERS ──────────────────────────────────────────────────────────────────

def parse_pasted_address(text):
    """
    Parse a pasted TCGPlayer-style address block, e.g.:
        Eric Fischer
        1820 WESTERN TRAILWAY DR
        OAKLAND, FL 34787-9057
        US
    Returns a dict with name/line1/line2/city/state/zip.
    """
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    # Drop trailing "US" / "USA" line
    if lines and lines[-1].upper() in ("US", "USA", "UNITED STATES"):
        lines = lines[:-1]

    if len(lines) < 2:
        print("  ⚠️  Couldn't parse — too few lines. Falling back to manual entry.")
        return None

    name = lines[0]

    # Last remaining line should be "CITY, ST ZIP" or "CITY ST ZIP"
    city_line = lines[-1]
    city, state, zip_ = "", "", ""
    if "," in city_line:
        parts = city_line.split(",", 1)
        city = parts[0].strip()
        rest = parts[1].strip().split()
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

    # Middle lines = street address (line1 + optional line2)
    street_lines = lines[1:-1]
    line1 = street_lines[0] if street_lines else ""
    line2 = street_lines[1] if len(street_lines) > 1 else ""

    return {"name": name, "business": "", "line1": line1, "line2": line2,
            "city": city, "state": state, "zip": zip_}


def prompt_recipient():
    print("\n── Recipient Address ──")
    print("  Paste the address block from TCGPlayer (blank line when done),")
    print("  OR press Enter to type it in field by field.\n")

    first = input("  > ").strip()

    if not first:
        # Manual field-by-field
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

    # They started pasting — collect until blank line
    pasted = first + "\n"
    while True:
        line = input("  > ")
        if line.strip() == "":
            break
        pasted += line + "\n"

    result = parse_pasted_address(pasted)
    if result:
        print(f"\n  Parsed:")
        print(f"    Name:    {result['name']}")
        print(f"    Street:  {result['line1']}" + (f" / {result['line2']}" if result['line2'] else ""))
        print(f"    City:    {result['city']}, {result['state']} {result['zip']}")
        confirm = input("\n  Looks good? [Y/n]: ").strip().lower()
        if confirm in ("", "y", "yes"):
            return result
    # Fallback — shouldn't usually hit this
    print("  Please re-enter manually.")
    return prompt_recipient()


def format_city_line(addr):
    return f"{addr['city']}, {addr['state']} {addr['zip']}"


# ── PDF GENERATION ────────────────────────────────────────────────────────────

def generate_label(return_addr, recipient_addr, output_path):
    W, H = 6 * inch, 4 * inch
    c = canvas.Canvas(output_path, pagesize=(W, H))

    c.setFillColor(colors.white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ── RETURN ADDRESS — top left, small ─────────────────────────────────────
    # Name: mixed case; everything else: ALL CAPS (like stamps.com)
    ret_lines = [return_addr["name"]]
    ret_lines.append(return_addr["business"])
    ret_lines.append(return_addr["line1"].upper())
    if return_addr.get("line2"):
        ret_lines.append(return_addr["line2"].upper())
    ret_lines.append(format_city_line(return_addr).upper())

    RETURN_SIZE = 8
    LINE_H_RET  = 10.5
    rx = 0.28 * inch
    ry = H - 0.30 * inch

    c.setFont("Helvetica", RETURN_SIZE)
    c.setFillColor(colors.black)
    for line in ret_lines:
        c.drawString(rx, ry, line)
        ry -= LINE_H_RET

    # ── RECIPIENT ADDRESS — all caps, centered ────────────────────────────────
    rec_lines = [recipient_addr["name"].upper()]
    if recipient_addr.get("business"):
        rec_lines.append(recipient_addr["business"].upper())
    rec_lines.append(recipient_addr["line1"].upper())
    if recipient_addr.get("line2"):
        rec_lines.append(recipient_addr["line2"].upper())
    rec_lines.append(format_city_line(recipient_addr).upper())

    REC_FONT = "Helvetica"
    REC_SIZE = 11.5
    LINE_H_REC = 15

    c.setFont(REC_FONT, REC_SIZE)
    max_w   = max(c.stringWidth(l, REC_FONT, REC_SIZE) for l in rec_lines)
    block_x = (W - max_w) / 2
    total_h = len(rec_lines) * LINE_H_REC
    start_y = (H / 2) + (total_h / 2) - LINE_H_REC * 0.3  # slightly above center

    c.setFillColor(colors.black)
    for i, line in enumerate(rec_lines):
        c.drawString(block_x, start_y - i * LINE_H_REC, line)

    c.save()
    print(f"\n✓ Label saved to: {os.path.abspath(output_path)}")


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 48)
    print("  Envelope Label Generator  (6×4 Landscape)")
    print("=" * 48)

    # Return address — always use defaults, just confirm
    r = DEFAULT_RETURN
    print(f"\nReturn address: {r['name']} / {r.get('business','')} / {r['line1']}, {r['city']} {r['state']} {r['zip']}")
    change = input("Change return address? [y/N]: ").strip().lower()
    if change == "y":
        def ask(prompt, key):
            default = r.get(key, "")
            val = input(f"  {prompt} [{default}]: ").strip()
            return val if val else default
        r = {
            "name":     ask("Name",     "name"),
            "business": ask("Business", "business"),
            "line1":    ask("Street",   "line1"),
            "line2":    ask("Apt/Suite","line2"),
            "city":     ask("City",     "city"),
            "state":    ask("State",    "state"),
            "zip":      ask("ZIP",      "zip"),
        }

    recipient_addr = prompt_recipient()

    out = input(f"\nOutput filename [{DEFAULT_OUTPUT}]: ").strip()
    if not out:
        out = DEFAULT_OUTPUT
    if not out.endswith(".pdf"):
        out += ".pdf"

    generate_label(r, recipient_addr, out)


if __name__ == "__main__":
    main()