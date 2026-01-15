import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist/playlist.m3u"
OUTPUT_FILE = "live.m3u"

SPORT_KEYWORDS = [
    "vs", "liga", "cup", "afc", "uefa", "fifa",
    "bundesliga", "laliga", "serie", "league"
]

def is_sport(title):
    t = title.lower()
    return any(k in t for k in SPORT_KEYWORDS)

def normalize_name(name):
    return " ".join(name.lower().split()[:2])

def parse_epg():
    tree = ET.parse(EPG_FILE)
    root = tree.getroot()

    channels = {}
    for ch in root.findall("channel"):
        name = ch.findtext("display-name", "").strip()
        icon = ch.find("icon")
        logo = icon.attrib.get("src", "") if icon is not None else ""
        channels[name] = logo

    events = []
    for p in root.findall("programme"):
        title = p.findtext("title", "").strip()
        if not is_sport(title):
            continue

        start = p.attrib.get("start")
        channel = p.attrib.get("channel")

        dt = datetime.strptime(start[:14], "%Y%m%d%H%M%S")
        wib = dt.replace(tzinfo=timezone.utc) + timedelta(hours=7)
        jam = wib.strftime("%H:%M WIB")

        events.append({
            "title": title,
            "time": jam,
            "channel": channel,
            "logo": channels.get(channel, "")
        })

    return events

def parse_playlist_blocks():
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    blocks = []
    current = []

    for line in lines:
        if line.startswith("#EXTINF"):
            if current:
                blocks.append(current)
            current = [line]
        elif current:
            current.append(line)

    if current:
        blocks.append(current)

    return blocks

def extract_channel_name(extinf):
    m = re.search(r",(.*)$", extinf)
    return m.group(1).strip() if m else ""

def generate():
    events = parse_epg()
    blocks = parse_playlist_blocks()

    out = ["#EXTM3U"]

    for ev in events:
        ev_key = normalize_name(ev["channel"])

        matched = 0
        for block in blocks:
            ch_name = extract_channel_name(block[0])
            if normalize_name(ch_name) == ev_key:
                new_block = []
                for i, line in enumerate(block):
                    if line.startswith("#EXTINF"):
                        new_block.append(
                            f'#EXTINF:-1 tvg-id="" tvg-logo="{ev["logo"]}" '
                            f'group-title="LIVE EVENT",'
                            f'{ev["title"]} ({ev["time"]}) - {ch_name}'
                        )
                    else:
                        new_block.append(line)

                out.extend(new_block)
                matched += 1
                if matched >= 3:
                    break

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    generate()
