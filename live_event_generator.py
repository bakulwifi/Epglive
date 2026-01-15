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

def clean_text(s):
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"(hd|fhd|uhd|sd)", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())

def first_words(s, n=3):
    return " ".join(s.split()[:n])

# =========================
def load_epg_channels(root):
    data = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        name = clean_text(cid)
        logo = icon.get("src") if icon is not None else ""
        data[cid] = {
            "name": name,
            "short": first_words(name),
            "logo": logo
        }
    return data

# =========================
def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            name = clean_text(lines[i].split(",")[-1])
            blocks.append({
                "name": name,
                "short": first_words(name),
                "extinf": lines[i],
                "url": lines[i + 1]
            })
    return blocks

def match_playlist(epg_short, playlist_blocks):
    for b in playlist_blocks:
        if any(w in b["short"] for w in epg_short.split()):
            return b
    return playlist_blocks[0] if playlist_blocks else None

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

            title = p.findtext("title")
            if not title:
                continue
            title = re.sub(r"\(.*?\)", "", title).strip()

            cid = p.get("channel", "")
            ch = epg_channels.get(cid)
            if not ch:
                continue

            is_live = (start - timedelta(minutes=LIVE_OFFSET_MINUTES)) <= now <= stop

            name = f"{title} ({start.strftime('%H:%M')}) {ch['short'].title()}"
            logo = ch["logo"]

            if is_live:
                block = match_playlist(ch["short"], playlist_blocks)
                if not block:
                    continue
                extinf = block["extinf"]
                url = block["url"]
                group = "LIVE EVENT"
            else:
                extinf = "#EXTINF:-1"
                url = JADWAL_URL
                group = "JADWAL EVENT"

            f.write(
                f'#EXTINF:-1 tvg-id="" tvg-name="{name}" '
                f'tvg-logo="{logo}" group-title="{group}",{name}\n'
            )
            f.write(url + "\n")

    print("[OK] live.m3u generated")

if __name__ == "__main__":
    main()
