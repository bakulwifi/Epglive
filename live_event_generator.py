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
# AMBIL ICON DARI EPG
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
# LOAD PLAYLIST BLOK ASLI
# =====================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            blocks.append((lines[i], lines[i + 1]))
            i += 2
        else:
            i += 1
    return blocks

# =====================
# EDIT EXTINF DENGAN AMAN
# =====================
def replace_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf

def replace_name(extinf, new_name):
    if "," in extinf:
        return extinf.split(",", 1)[0] + "," + new_name
    return extinf

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

                match_title = re.sub(r"\(.*?\)", "", p.findtext("title", "LIVE")).strip()
                channel_id = p.get("channel")
                logo = epg_icons.get(channel_id, "")

                for extinf, url in playlist_blocks:
                    new_extinf = extinf

                    # ganti nama channel (AMAN)
                    new_extinf = replace_name(new_extinf, match_title)

                    # ganti group-title
                    new_extinf = replace_attr(new_extinf, "group-title", "LIVE EVENT")

                    # ganti logo dari EPG
                    if logo:
                        new_extinf = replace_attr(new_extinf, "tvg-logo", logo)

                    f.write(new_extinf + "\n")
                    f.write(url + "\n")

                break  # hanya 1 event LIVE
            except:
                continue

    print("[DONE] live.m3u FIXED (clean & stable)")

if __name__ == "__main__":
    main()
