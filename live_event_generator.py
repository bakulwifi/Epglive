from lxml import etree
from datetime import datetime, timedelta

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB
LIVE_LOGO = "https://i.imgur.com/8M0QZ5K.png"  # ganti logo LIVE kalau mau

# =====================
# LOAD PLAYLIST (FULL BLOCK)
# =====================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f.readlines() if l.strip()]

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

# =====================
# PARSE TIME EPG
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

                title = p.findtext("title", "LIVE EVENT")

                for extinf, url in playlist_blocks:
                    # ganti NAMA + LOGO saja
                    new_extinf = extinf

                    # ganti nama channel
                    if "," in new_extinf:
                        new_extinf = new_extinf.split(",", 1)[0] + f",LIVE | {title}"

                    # ganti logo
                    if "tvg-logo" in new_extinf:
                        new_extinf = (
                            new_extinf.split('tvg-logo="')[0]
                            + f'tvg-logo="{LIVE_LOGO}" '
                            + new_extinf.split('"', 2)[2]
                        )

                    # ganti group
                    if "group-title" in new_extinf:
                        new_extinf = (
                            new_extinf.split('group-title="')[0]
                            + 'group-title="LIVE EVENT" '
                            + new_extinf.split('"', 2)[2]
                        )

                    f.write(new_extinf + "\n")
                    f.write(url + "\n")

                break  # cukup 1 event LIVE
            except:
                continue

    print("[DONE] live.m3u (full block, rename only)")

if __name__ == "__main__":
    main()
