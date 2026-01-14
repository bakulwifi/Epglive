from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB
MAX_DAYS = 2
LIVE_OFFSET_MINUTES = 5
MAX_CHANNEL_PER_MATCH = 3

JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"
LIVE_URL_DEFAULT = "https://bwifi.my.id/hls/video.m3u8"

PRIORITY_KEYWORDS = ["bein", "tnt", "fubo"]

# =====================
def parse_time_any(t):
    try:
        return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)
    except:
        try:
            return datetime.strptime(t[:15], "%Y%m%dT%H%M%S") + timedelta(hours=TZ)
        except:
            return None

def clean_title(t):
    if not t:
        return None
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def force_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return f'#EXTINF:-1 {attr}="{value}",'

# =====================
def load_epg_channels():
    tree = etree.parse(EPG_FILE)
    data = {}
    for ch in tree.getroot().findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None and icon.get("src"):
            data[cid] = icon.get("src")
    return data

def channel_priority(cid):
    c = cid.lower()
    for i,k in enumerate(PRIORITY_KEYWORDS):
        if k in c:
            return i
    return 99

# =====================
def main():
    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=MAX_DAYS)

    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    epg_icons = load_epg_channels()
    events = {}

    # kumpulkan event
    for p in root.findall("programme"):
        start = parse_time_any(p.get("start",""))
        stop = parse_time_any(p.get("stop",""))
        if not start or not stop:
            continue
        if start > limit or stop < now:
            continue

        title = clean_title(p.findtext("title"))
        if not title:
            continue

        cid = p.get("channel")
        if title not in events:
            events[title] = {"start":start,"stop":stop,"channels":[]}
        if cid and cid in epg_icons:
            events[title]["channels"].append(cid)

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for title,data in events.items():
            live_time = data["start"] - timedelta(minutes=LIVE_OFFSET_MINUTES)
            is_live = live_time <= now <= data["stop"]

            group = "LIVE EVENT" if is_live else "JADWAL EVENT"
            base_url = LIVE_URL_DEFAULT if is_live else JADWAL_URL

            channels = sorted(
                set(data["channels"]),
                key=channel_priority
            )[:MAX_CHANNEL_PER_MATCH]

            for cid in channels:
                logo = epg_icons.get(cid,"")
                name = title if is_live else f"{title} ({data['start'].strftime('%H:%M')})"
                name = f"{name} ({cid})"

                f.write(f'#EXTINF:-1 tvg-logo="{logo}" group-title="{group}",{name}\n')
                f.write(base_url + "\n")

    print("[OK] live.m3u generated (STABLE MODE)")

if __name__=="__main__":
    main()
