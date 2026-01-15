from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7
LIVE_OFFSET_MINUTES = 5
MAX_DAYS = 2
JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"

# =========================
def parse_time(t):
    for fmt in ("%Y%m%d%H%M%S", "%Y%m%dT%H%M%S"):
        try:
            return datetime.strptime(t[:len(fmt)], fmt) + timedelta(hours=TZ)
        except:
            pass
    return None

def clean_title(t):
    t = re.sub(r"\(.*?\)", "", t)
    return re.sub(r"\s+", " ", t).strip()

def normalize(s):
    s = s.lower()
    s = re.sub(r"(hd|fhd|uhd|sd)", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())

def force_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf.replace("#EXTINF", f'#EXTINF {attr}="{value}"', 1)

def replace_name(extinf, name):
    return extinf.split(",", 1)[0] + "," + name

# =========================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            blocks.append({
                "raw_extinf": lines[i],
                "url": lines[i + 1],
                "name": normalize(lines[i].split(",")[-1])
            })
    return blocks

def find_matching_block(epg_name, blocks):
    epg_words = set(epg_name.split()[:3])
    for b in blocks:
        if epg_words & set(b["name"].split()):
            return b
    return blocks[0] if blocks else None

# =========================
def load_epg_channels(root):
    data = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            data[cid] = {
                "short": normalize(cid),
                "logo": icon.get("src")
            }
    return data

# =========================
def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    epg_channels = load_epg_channels(root)
    playlist_blocks = load_playlist_blocks()

    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=MAX_DAYS)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            start = parse_time(p.get("start", ""))
            stop = parse_time(p.get("stop", ""))
            if not start or not stop:
                continue
            if start > limit or stop < now:
                continue

            title = clean_title(p.findtext("title"))
            cid = p.get("channel", "")
            ch = epg_channels.get(cid)
            if not title or not ch:
                continue

            is_live = (start - timedelta(minutes=LIVE_OFFSET_MINUTES)) <= now <= stop
            display_name = f"{title} ({start.strftime('%H:%M')}) {cid}"

            if is_live:
                block = find_matching_block(ch["short"], playlist_blocks)
                if not block:
                    continue

                extinf = block["raw_extinf"]
                extinf = replace_name(extinf, display_name)
                extinf = force_attr(extinf, "group-title", "LIVE EVENT")
                extinf = force_attr(extinf, "tvg-logo", ch["logo"])

                f.write(extinf + "\n")
                f.write(block["url"] + "\n")

            else:
                f.write(
                    f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" '
                    f'tvg-logo="{ch["logo"]}" group-title="JADWAL EVENT",{display_name}\n'
                )
                f.write(JADWAL_URL + "\n")

    print("[OK] LIVE pakai BLOK UTUH, JADWAL placeholder")

if __name__ == "__main__":
    main()
