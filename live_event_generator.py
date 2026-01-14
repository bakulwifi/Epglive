from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7
MAX_DAYS = 2
LIVE_OFFSET_MINUTES = 5
MAX_CHANNEL_PER_MATCH = 3
JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"

PRIORITY_KEYWORDS = ["bein", "tnt", "fubo"]

# =====================
def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

def clean_title(t):
    t = re.sub(r"\(.*?\)", "", t)
    return re.sub(r"\s+", " ", t).strip()

def force_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf.split(",",1)[0] + f' {attr}="{value}",' + extinf.split(",",1)[1]

def replace_name(extinf, name):
    return extinf.split(",",1)[0] + "," + name

# =====================
def load_base_playlist_block():
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            return lines[i], lines[i+1]
    return None, None

# =====================
def load_epg_channels():
    tree = etree.parse(EPG_FILE)
    data = {}
    for ch in tree.getroot().findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            data[cid] = icon.get("src")
    return data

def channel_priority(cid):
    cid = cid.lower()
    for i,k in enumerate(PRIORITY_KEYWORDS):
        if k in cid:
            return i
    return 99

# =====================
def main():
    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=MAX_DAYS)

    epg_tree = etree.parse(EPG_FILE)
    root = epg_tree.getroot()

    epg_icons = load_epg_channels()
    base_extinf, live_url = load_base_playlist_block()

    if not base_extinf:
        print("Playlist kosong")
        return

    events = {}

    for p in root.findall("programme"):
        try:
            start = parse_time(p.get("start"))
            stop = parse_time(p.get("stop"))
            if start > limit or stop < now:
                continue

            title = clean_title(p.findtext("title",""))
            cid = p.get("channel")

            if title not in events:
                events[title] = {"start":start,"stop":stop,"channels":[]}

            if cid in epg_icons:
                events[title]["channels"].append(cid)
        except:
            continue

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for title,data in events.items():
            live_time = data["start"] - timedelta(minutes=LIVE_OFFSET_MINUTES)
            is_live = live_time <= now <= data["stop"]

            group = "LIVE EVENT" if is_live else "JADWAL EVENT"
            url = live_url if is_live else JADWAL_URL

            channels = sorted(
                set(data["channels"]),
                key=channel_priority
            )[:MAX_CHANNEL_PER_MATCH]

            for cid in channels:
                logo = epg_icons.get(cid,"")
                suffix = cid.upper()
                name = title if is_live else f"{title} ({data['start'].strftime('%H:%M')})"
                name = f"{name} ({suffix})"

                extinf = replace_name(base_extinf,name)
                extinf = force_attr(extinf,"group-title",group)
                if logo:
                    extinf = force_attr(extinf,"tvg-logo",logo)

                f.write(extinf+"\n")
                f.write(url+"\n")

    print("[OK] live.m3u generated (NON EMPTY)")

if __name__=="__main__":
    main()
