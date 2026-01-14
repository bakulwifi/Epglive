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
def norm(s):
    s = s.lower()
    s = re.sub(r"(hd|fhd|uhd|sd)", "", s)
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return s.strip()

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
# LOAD PLAYLIST BLOK PER CHANNEL
# =====================
def load_playlist_blocks():
    blocks = {}
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            ch_name = norm(lines[i].split(",")[-1])
            blocks[ch_name] = (lines[i], lines[i+1])
    return blocks

# =====================
# LOAD EPG CHANNEL + ICON
# =====================
def load_epg_channels():
    tree = etree.parse(EPG_FILE)
    data = {}
    for ch in tree.getroot().findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            data[cid] = {
                "norm": norm(cid),
                "logo": icon.get("src")
            }
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

    epg_tree = etree.parse(EPG_FILE)
    epg_root = epg_tree.getroot()

    playlist_blocks = load_playlist_blocks()
    epg_channels = load_epg_channels()

    events = {}

    for p in epg_root.findall("programme"):
        try:
            start = parse_time(p.get("start"))
            stop = parse_time(p.get("stop"))
            if start > limit or stop < now:
                continue

            title = clean_title(p.findtext("title",""))
            cid = p.get("channel")

            if title not in events:
                events[title] = {"start":start,"stop":stop,"channels":[]}

            if cid in epg_channels:
                events[title]["channels"].append(cid)
        except:
            continue

    with open(OUTPUT_FILE,"w",encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for title,data in events.items():
            live_time = data["start"] - timedelta(minutes=LIVE_OFFSET_MINUTES)
            now_state = "jadwal" if now < live_time else "live"

            channels = sorted(
                set(data["channels"]),
                key=channel_priority
            )[:MAX_CHANNEL_PER_MATCH]

            for cid in channels:
                epg_ch = epg_channels[cid]
                block = playlist_blocks.get(epg_ch["norm"])
                if not block:
                    continue  # ❗ tanpa playlist cocok → skip

                extinf,url = block
                name = title if now_state=="live" else f"{title} ({data['start'].strftime('%H:%M')})"
                group = "LIVE EVENT" if now_state=="live" else "JADWAL EVENT"
                final_url = url if now_state=="live" else JADWAL_URL

                extinf = replace_name(extinf,name)
                extinf = force_attr(extinf,"group-title",group)
                extinf = force_attr(extinf,"tvg-logo",epg_ch["logo"])

                f.write(extinf+"\n")
                f.write(final_url+"\n")

    print("[OK] Logo FIXED & mapping valid")

if __name__=="__main__":
    main()
