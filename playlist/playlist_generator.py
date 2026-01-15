import re
import requests
import xml.etree.ElementTree as ET
from io import BytesIO
from datetime import datetime

# ================= CONFIG =================
EPG_URL = "https://raw.githubusercontent.com/bakulwifi/Epglive/refs/heads/main/epg.xml"
SOURCE_M3U = "playlist/playlist.m3u"
OUTPUT_M3U = "live.m3u"
GROUP_TITLE = "LIVE EVENT"
TIMEZONE = "WIB"
# ==========================================


def normalize_name(name: str) -> str:
    name = name.lower()
    name = re.sub(r'[^a-z0-9 ]', '', name)
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name


def load_epg_events():
    r = requests.get(EPG_URL, timeout=30)
    r.raise_for_status()
    tree = ET.parse(BytesIO(r.content))
    root = tree.getroot()

    events = []
    for p in root.findall("programme"):
        title_el = p.find("title")
        if title_el is None:
            continue

        channel = p.attrib.get("channel", "").strip()
        start = p.attrib.get("start", "").strip()
        title = title_el.text.strip()

        if not channel or not start or not title:
            continue

        try:
            start_dt = datetime.strptime(start[:14], "%Y%m%d%H%M%S")
            start_time = start_dt.strftime("%H:%M")
        except Exception:
            continue

        events.append({
            "channel": channel,
            "channel_key": normalize_name(channel),
            "title": title,
            "time": start_time
        })

    return events


def load_playlist_blocks():
    with open(SOURCE_M3U, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.read().splitlines()

    blocks = []
    block = []

    for line in lines:
        if line.startswith("#EXTINF"):
            if block:
                blocks.append(block)
            block = [line]
        elif block:
            block.append(line)

    if block:
        blocks.append(block)

    return blocks


def extract_channel_from_extinf(extinf: str) -> str:
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return ""


def extract_url(block):
    for l in block:
        if l.startswith("http"):
            return l.strip()
    return ""


def main():
    epg_events = load_epg_events()
    playlist_blocks = load_playlist_blocks()

    channel_map = {}
    for block in playlist_blocks:
        extinf = block[0]
        ch_name = extract_channel_from_extinf(extinf)
        if not ch_name:
            continue
        key = normalize_name(ch_name)
        channel_map.setdefault(key, []).append(block)

    output = ["#EXTM3U"]
    seen = set()

    for ev in epg_events:
        key = ev["channel_key"]
        if key not in channel_map:
            continue

        for block in channel_map[key]:
            url = extract_url(block)
            if not url:
                continue

            unique_key = f"{ev['title']}|{ev['time']}|{ev['channel']}|{url}"
            if unique_key in seen:
                continue
            seen.add(unique_key)

            extinf = (
                f'#EXTINF:-1 group-title="{GROUP_TITLE}",'
                f'{ev["title"]} ({ev["time"]} {TIMEZONE}) - {extract_channel_from_extinf(block[0])}'
            )

            output.append(extinf)
            output.append(url)

    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("\n".join(output))


if __name__ == "__main__":
    main()
