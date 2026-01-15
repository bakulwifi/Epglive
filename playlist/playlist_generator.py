import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
import re

EPG_FILE = "../epg.xml"
SOURCE_M3U = "playlist.m3u"
OUTPUT_M3U = "../live.m3u"

PLACEHOLDER_URL = "https://bwifi.my.id/hls/video.m3u8"
TIMEZONE = timezone.utc
LIVE_OFFSET_MINUTES = 5

# =========================
# UTIL
# =========================
def normalize_name(name):
    name = name.lower()
    name = re.sub(r"(hd|fhd|uhd|4k)", "", name)
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    words = name.split()
    return " ".join(words[:3])

def parse_time(t):
    return datetime.strptime(t.strip(), "%Y%m%d%H%M%S %z")

def is_soccer(title):
    keywords = [
        "liga", "league", "vs", "v ", "uefa", "ucl", "uel",
        "afc", "bundesliga", "laliga", "serie", "premier",
        "qual", "world cup", "asian cup"
    ]
    t = title.lower()
    return any(k in t for k in keywords)

# =========================
# LOAD PLAYLIST BLOK UTUH
# =========================
def load_playlist_blocks():
    with open(SOURCE_M3U, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    blocks = []
    current = []

    for line in lines:
        if line.startswith("#EXTINF"):
            if current:
                blocks.append(current)
            current = [line]
        else:
            if current:
                current.append(line)

    if current:
        blocks.append(current)

    results = []
    for block in blocks:
        info = block[0]
        url = block[-1].strip()

        name_match = re.search(r',(.+)$', info)
        name = name_match.group(1).strip() if name_match else "UNKNOWN"

        logo_match = re.search(r'tvg-logo="([^"]*)"', info)
        logo = logo_match.group(1) if logo_match else ""

        results.append({
            "raw": block,
            "name": name,
            "norm": normalize_name(name),
            "logo": logo,
            "url": url
        })

    return results

# =========================
# LOAD EPG (SPORTS ONLY)
# =========================
def load_epg():
    tree = ET.parse(EPG_FILE)
    root = tree.getroot()

    programmes = []
    for p in root.findall("programme"):
        title_el = p.find("title")
        if title_el is None:
            continue

        title = title_el.text.strip()
        if not is_soccer(title):
            continue

        start = parse_time(p.attrib["start"])
        stop = parse_time(p.attrib["stop"])
        channel = p.attrib.get("channel", "")

        icon = ""
        ch_el = root.find(f"./channel[@id='{channel}']/icon")
        if ch_el is not None:
            icon = ch_el.attrib.get("src", "")

        programmes.append({
            "title": title,
            "start": start,
            "stop": stop,
            "channel": channel,
            "norm": normalize_name(channel),
            "logo": icon
        })

    return programmes

# =========================
# MAIN
# =========================
def main():
    now = datetime.now(TIMEZONE)

    playlist_blocks = load_playlist_blocks()
    epg_events = load_epg()

    used_events = set()
    output = ["#EXTM3U\n"]

    for event in epg_events:
        is_live = now >= (event["start"] - timedelta(minutes=LIVE_OFFSET_MINUTES))
        group = "LIVE EVENT" if is_live else "JADWAL EVENT"
        event_time = event["start"].astimezone(TIMEZONE).strftime("%H:%M WIB")

        for block in playlist_blocks:
            if event["norm"] not in block["norm"]:
                continue

            stream_url = block["url"] if is_live else PLACEHOLDER_URL

            event_key = f"{event['title']}|{event_time}|{block['name']}|{stream_url}"
            if event_key in used_events:
                continue
            used_events.add(event_key)

            display_name = f"{event['title']} ({event_time}) - {block['name']}"
            logo = event["logo"] or block["logo"]

            extinf = (
                f'#EXTINF:-1 tvg-logo="{logo}" '
                f'group-title="{group}",{display_name}\n'
            )

            output.append(extinf)
            output.append(stream_url + "\n")

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.writelines(output)

    print("✔ live.m3u generated successfully")

if __name__ == "__main__":
    main()
