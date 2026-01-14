from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"
TZ = 7  # WIB

# =====================
# PARSE WAKTU
# =====================
def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

# =====================
# LOAD ICON DARI EPG
# =====================
def load_epg_icons():
    icons = {}
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None and icon.get("src"):
            icons[cid] = icon.get("src")
    return icons

# =====================
# LOAD PLAYLIST BLOK
# =====================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            blocks.append((lines[i], lines[i + 1]))
            i += 2
        else:
            i += 1
    return blocks

def clean_title(title):
    title = re.sub(r"\(.*?\)", "", title)   # hapus (SEA GAMES dll)
    title = re.sub(r"\s+", " ", title)
    return title.strip()

# =====================
# MAIN
# =====================
def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    now = datetime.utcnow() + timedelta(hours=TZ)

    epg_icons = load_epg_icons()
    playlist_blocks = load_playlist_blocks()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            try:
                start = parse_time(p.get("start"))
                stop = parse_time(p.get("stop"))
                if not (start <= now <= stop):
                    continue

                match_title = clean_title(p.findtext("title", "LIVE MATCH"))
                channel_id = p.get("channel")
                logo = epg_icons.get(channel_id, "")

                for extinf, url in playlist_blocks:
                    base = extinf.split(",", 1)[0]

                    new_extinf = (
                        f'{base} '
                        f'tvg-id="{channel_id}" '
                        f'tvg-name="{channel_id}" '
                        f'tvg-logo="{logo}" '
                        f'group-title="LIVE EVENT",'
                        f'{match_title}'
                    )

                    f.write(new_extinf + "\n")
                    f.write(url + "\n")

                break  # hanya 1 pertandingan LIVE
            except:
                continue

    print("[DONE] live.m3u (clean name + epg icon)")

if __name__ == "__main__":
    main()
