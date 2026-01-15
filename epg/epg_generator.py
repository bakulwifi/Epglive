import xml.etree.ElementTree as ET
import urllib.request
import io

# =============================
# CONFIG
# =============================

EPG_URLS = [
    "https://www.open-epg.com/files/indonesia2.xml",
    "https://raw.githubusercontent.com/dbghelp/StarHub-TV-EPG/main/starhub.xml"
]

OUTPUT_EPG = "epg.xml"

SOCCER_KEYWORDS = [
    "vs", " v ", "liga", "league", "cup",
    "football", "soccer", "afc", "uefa",
    "premier", "bundesliga", "laliga",
    "serie", "champions", "qualifier"
]

# =============================
# HELPERS
# =============================

def is_soccer(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SOCCER_KEYWORDS)

def clean(text):
    return text.strip() if text else ""

def load_xml_from_url(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return ET.parse(io.BytesIO(r.read())).getroot()

# =============================
# MAIN
# =============================

def main():
    print("=== RUNNING SOCCER-ONLY EPG FROM URL ===")

    tv_out = ET.Element("tv")
    channel_done = set()
    total_programme = 0

    for url in EPG_URLS:
        print(f"[FETCH] {url}")
        try:
            root = load_xml_from_url(url)
        except Exception as e:
            print(f"[SKIP] Failed load {url}: {e}")
            continue

        channel_map = {}

        for ch in root.findall("channel"):
            cid = ch.get("id")
            name = clean(ch.findtext("display-name"))
            icon = ch.find("icon")
            icon_src = icon.get("src") if icon is not None else ""

            if cid and name:
                channel_map[cid] = (name, icon_src)

                if cid not in channel_done:
                    ch_el = ET.SubElement(tv_out, "channel")
                    ET.SubElement(ch_el, "display-name").text = name
                    if icon_src:
                        ET.SubElement(ch_el, "icon").set("src", icon_src)
                    channel_done.add(cid)

        for p in root.findall("programme"):
            title = clean(p.findtext("title"))
            if not title or not is_soccer(title):
                continue

            prog = ET.SubElement(tv_out, "programme")
            prog.set("start", p.get("start", ""))
            prog.set("stop", p.get("stop", ""))

            ET.SubElement(prog, "title").text = title
            total_programme += 1

    ET.ElementTree(tv_out).write(
        OUTPUT_EPG,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"[OK] Soccer programmes: {total_programme}")

# =============================
if __name__ == "__main__":
    main()
