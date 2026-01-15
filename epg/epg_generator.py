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

SPORT_KEYWORDS = [
    "vs", " v ",
    "liga", "league", "cup",
    "championship", "tournament",
    "afc", "uefa", "caf", "fifa",
    "bundesliga", "laliga", "serie",
    "premier", "proliga", "fivb",
    "padel", "tennis", "badminton",
    "volleyball", "basketball", "hockey",
    "mma", "boxing", "ufc"
]

EXCLUDE_KEYWORDS = [
    "series", "episode", "movie", "film", "drama", "show"
]

# =============================
# HELPERS
# =============================

def is_sports(title: str) -> bool:
    t = title.lower()
    if any(x in t for x in EXCLUDE_KEYWORDS):
        return False
    return any(k in t for k in SPORT_KEYWORDS)

def clean(text):
    return text.strip() if text else ""

def load_xml_from_url(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return ET.parse(io.BytesIO(r.read())).getroot()

# =============================
# MAIN
# =============================

def main():
    print("=== RUNNING SPORTS-ONLY EPG (CHANNEL-BASED) ===")

    tv_out = ET.Element("tv")

    channel_written = set()
    valid_channels = set()
    programmes_buffer = []

    # ===== PASS 1: COLLECT SPORTS PROGRAMMES =====
    for url in EPG_URLS:
        print(f"[FETCH] {url}")
        try:
            root = load_xml_from_url(url)
        except Exception as e:
            print(f"[SKIP] {url} -> {e}")
            continue

        for p in root.findall("programme"):
            title = clean(p.findtext("title"))
            if not title or not is_sports(title):
                continue

            ch_id = p.get("channel")
            if not ch_id:
                continue

            programmes_buffer.append({
                "start": p.get("start", ""),
                "stop": p.get("stop", ""),
                "channel": ch_id,
                "title": title
            })
            valid_channels.add(ch_id)

        # ===== PASS 2: WRITE CHANNELS (ONLY USED ONES) =====
        for ch in root.findall("channel"):
            cid = ch.get("id")
            if cid not in valid_channels or cid in channel_written:
                continue

            display = clean(ch.findtext("display-name"))
            if not display:
                continue

            ch_out = ET.SubElement(tv_out, "channel")
            ch_out.set("id", cid)
            ET.SubElement(ch_out, "display-name").text = display

            channel_written.add(cid)

    # ===== PASS 3: WRITE PROGRAMMES =====
    for p in programmes_buffer:
        prog = ET.SubElement(tv_out, "programme")
        prog.set("start", p["start"])
        prog.set("stop", p["stop"])
        prog.set("channel", p["channel"])

        ET.SubElement(prog, "title").text = p["title"]

    ET.ElementTree(tv_out).write(
        OUTPUT_EPG,
        encoding="utf-8",
        xml_declaration=True
    )

    print(f"[OK] Sports-only EPG generated | Channels: {len(channel_written)} | Programmes: {len(programmes_buffer)}")

# =============================
if __name__ == "__main__":
    main()
