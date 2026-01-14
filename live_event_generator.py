from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB
MAX_DAYS = 2
LIVE_OFFSET_MINUTES = 5
MAX_CHANNEL_PER_MATCH = 3

JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"

# PRIORITAS CHANNEL (URUT)
PRIORITY_KEYWORDS = [
    "bein",
    "tnt",
    "fubo"
]

# =========================
def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

def clean_title(title):
    title = re.sub(r"\(.*?\)", "", title)
    title = re.sub(r"\s+", " ", title)
    return title.strip()

def force_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf.split(",", 1)[0] + f' {attr}="{value}",' + extinf.split(",", 1)[1]

def replace_name(extinf, name):
    return extinf.split(",", 1)[0] + "," + name

# =========================
def load_playlist_blocks():
    blocks = {}
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    i = 0
    while i < len(lines):
        if lines[i].startswith("#EXTINF"):
            name = lines[i].split(",")[-1].lower()
            blocks[name] = (lines[i], lines[i + 1])
            i += 2
        else:
            i += 1
    return blocks

# =========================
def load_epg_channels():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    channels = {}

    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        logo = icon.get("src") if icon is not None else ""
        channels[cid] = logo
    return channels

# =========================
def channel_priority(channel_id):
    cid = channel_id.lower()
    for i, key in enumerate(PRIORITY_KEYWORDS):
        if key in cid:
            return i
    return len(PRIORITY_KEYWORDS)

# =========================
def main():
    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=MAX_DAYS)

    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    playlist_blocks = load_playlist_blocks()
    epg_channels = load_epg_channels()

    events = {}

    # =====================
    # KUMPULKAN MATCH
    # =====================
    for p in root.findall("programme"):
        try:
            start = parse_time(p.get("start"))
            stop = parse_time(p.get("stop"))

            if start > limit or stop < now:
                continue

            title = clean_title(p.findtext("title", "MATCH"))
            channel_id = p.get("channel")

            if title not in events:
                events[title] = {
                    "start": start,
                    "stop": stop,
                    "channels": []
                }

            if channel_id not in events[title]["channels"]:
                events[title]["channels"].append(channel_id)

        except:
            continue

    # =====================
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for title, data in events.items():
            start = data["start"]
            stop = data["stop"]

            live_time = start - timedelta(minutes=LIVE_OFFSET_MINUTES)

            # tentukan status
            if now < live_time:
                group = "JADWAL EVENT"
                url_type = "jadwal"
            elif live_time <= now <= stop:
                group = "LIVE EVENT"
                url_type = "live"
            else:
                continue

            # urutkan & batasi channel
            channels = sorted(
                data["channels"],
                key=lambda x: channel_priority(x)
            )[:MAX_CHANNEL_PER_MATCH]

            for cid in channels:
                logo = epg_channels.get(cid, "")
                extinf_base, live_url = next(iter(playlist_blocks.values()))

                if url_type == "jadwal":
                    name = f"{title} ({start.strftime('%H:%M')}) ({cid})"
                    url = JADWAL_URL
                else:
                    name = f"{title} ({cid})"
                    url = live_url

                extinf = replace_name(extinf_base, name)
                extinf = force_attr(extinf, "group-title", group)

                if logo:
                    extinf = force_attr(extinf, "tvg-logo", logo)

                f.write(extinf + "\n")
                f.write(url + "\n")

    print("[DONE] live.m3u generated successfully")

# =========================
if __name__ == "__main__":
    main()
