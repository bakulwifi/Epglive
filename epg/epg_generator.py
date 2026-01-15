import xml.etree.ElementTree as ET
from datetime import datetime
import sys

# ===============================
# CONFIG
# ===============================

SOURCE_EPG = "source_epg.xml"   # file EPG mentah (gabungan)
OUTPUT_EPG = "epg.xml"

SOCCER_KEYWORDS = [
    "vs", " v ", "liga", "league", "cup",
    "football", "soccer", "afc", "uefa",
    "premier", "bundesliga", "laliga",
    "serie", "champions", "qualifier"
]

# ===============================
# HELPERS
# ===============================

def is_soccer(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SOCCER_KEYWORDS)

def clean_text(text):
    return text.strip() if text else ""

# ===============================
# MAIN
# ===============================

def main():
    print("=== RUNNING NEW SOCCER-ONLY MINIMAL EPG ===")

    try:
        tree = ET.parse(SOURCE_EPG)
    except Exception as e:
        print(f"[ERROR] Cannot open {SOURCE_EPG}: {e}")
        sys.exit(1)

    root = tree.getroot()

    # Output root
    tv = ET.Element("tv")

    # Map channel id -> display-name & icon
    channel_map = {}

    for ch in root.findall("channel"):
        display = ch.findtext("display-name")
        icon = ch.find("icon")
        icon_src = icon.get("src") if icon is not None else ""

        if display:
            channel_map[ch.get("id")] = {
                "name": clean_text(display),
                "icon": clean_text(icon_src)
            }

    # Add channels (minimal)
    for ch_id, data in channel_map.items():
        ch_el = ET.SubElement(tv, "channel")
        dn = ET.SubElement(ch_el, "display-name")
        dn.text = data["name"]

        if data["icon"]:
            ic = ET.SubElement(ch_el, "icon")
            ic.set("src", data["icon"])

    # Add programmes
    count = 0

    for p in root.findall("programme"):
        title = clean_text(p.findtext("title"))
        if not title:
            continue

        if not is_soccer(title):
            continue

        prog = ET.SubElement(tv, "programme")
        prog.set("start", p.get("start", ""))
        prog.set("stop", p.get("stop", ""))

        t = ET.SubElement(prog, "title")
        t.text = title

        count += 1

    # Write output
    ET.ElementTree(tv).write(
        OUTPUT_EPG,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"[OK] Soccer-only EPG generated: {count} programmes")

# ===============================
if __name__ == "__main__":
    main()
