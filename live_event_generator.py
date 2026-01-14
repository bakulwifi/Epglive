from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB
LIVE_LOGO = None  # isi URL logo LIVE kalau mau, atau None

# =====================
# LOAD PLAYLIST BLOK
# =====================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip("\n") for l in f if l.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            extinf = lines[i]
            url = lines[i + 1]
            blocks.append((extinf, url))
            i += 2
        else:
            i += 1
    return blocks

def get_channel_name(extinf):
    # ambil nama setelah koma terakhir
    return extinf.split(",", 1)[-1].strip()

# =====================
# PARSE TIME
# =====================
def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

# =====================
# MAIN
# =====================
def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    now = datetime.utcnow() + timedelta(hours=TZ)

    playlist_blocks = load_playlist_blocks()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            try:
                start = parse_time(p.get("start"))
                stop = parse_time(p.get("stop"))
                if not (start <= now <= stop):
                    continue

                match_title = p.findtext("title", "LIVE MATCH")

                for extinf, url in playlist_blocks:
                    original_name = get_channel_name(extinf)

                    # ganti nama channel (unik per channel)
                    new_name = f"LIVE | {match_title} ({original_name})"

                    new_extinf = extinf.split(",", 1)[0] + "," + new_name

                    # ganti group
                    if 'group-title="' in new_extinf:
                        new_extinf = re.sub(
                            r'group-title="[^"]+"',
                            'group-title="LIVE EVENT"',
                            new_extinf
                        )

                    # ganti logo kalau diset
                    if LIVE_LOGO and 'tvg-logo="' in new_extinf:
                        new_extinf = re.sub(
                            r'tvg-logo="[^"]+"',
                            f'tvg-logo="{LIVE_LOGO}"',
                            new_extinf
                        )

                    f.write(new_extinf + "\n")
                    f.write(url + "\n")

                break  # cukup 1 event LIVE
            except:
                continue

    print("[DONE] live.m3u (unique channel names)")

if __name__ == "__main__":
    main()
