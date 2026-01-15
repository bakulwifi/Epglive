import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

EPG_URL = "https://raw.githubusercontent.com/bakulwifi/Epglive/refs/heads/main/epg.xml"
PLAYLIST_INPUT = "playlist/playlist.m3u"
PLAYLIST_OUTPUT = "live.m3u"

MAX_CHANNEL_PER_EVENT = 3
WIB = timezone(timedelta(hours=7))


def normalize(name: str) -> str:
    name = name.lower()
    name = re.sub(r'\b(hd|tv|\.id)\b', '', name)
    name = re.sub(r'[^a-z0-9 ]', ' ', name)
    name = re.sub(r'\s+', ' ', name)
    return name.strip()


def first_two_words(name: str) -> str:
    parts = normalize(name).split()
    return " ".join(parts[:2]) if len(parts) >= 2 else normalize(name)


# --- LOAD PLAYLIST ---
playlist_channels = []

with open(PLAYLIST_INPUT, encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

for i in range(len(lines)):
    if lines[i].startswith("#EXTINF"):
        name = lines[i].split(",")[-1].strip()
        url = lines[i + 1].strip()
        playlist_channels.append({
            "raw_name": name,
            "key": first_two_words(name),
            "url": url
        })


# --- LOAD EPG ---
xml = requests.get(EPG_URL, timeout=30).text
root = ET.fromstring(xml)

channels = {}
for ch in root.findall("channel"):
    name = ch.findtext("display-name")
    if name:
        channels[first_two_words(name)] = name

now = datetime.now(WIB)

events = []

for p in root.findall("programme"):
    title = p.findtext("title")
    channel_name = p.attrib.get("channel")

    if not title or not channel_name:
        continue

    start = datetime.strptime(p.attrib["start"][:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).astimezone(WIB)
    stop = datetime.strptime(p.attrib["stop"][:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).astimezone(WIB)

    status = None
    if start - timedelta(minutes=5) <= now <= stop:
        status = "LIVE EVENT"
    elif now < start:
        status = "JADWAL EVENT"
    else:
        continue

    events.append({
        "title": title,
        "start": start,
        "status": status,
        "channel_key": first_two_words(channel_name)
    })


# --- BUILD PLAYLIST ---
out = ["#EXTM3U"]

for ev in events:
    matched = []
    for ch in playlist_channels:
        if ch["key"] == ev["channel_key"]:
            matched.append(ch)
        if len(matched) >= MAX_CHANNEL_PER_EVENT:
            break

    for ch in matched:
        name = f'{ev["title"]} ({ev["start"].strftime("%H:%M")} WIB) - {ch["raw_name"]}'
        out.append(f'#EXTINF:-1 group-title="{ev["status"]}",{name}')
        out.append(ch["url"])


with open(PLAYLIST_OUTPUT, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print("Playlist generated:", PLAYLIST_OUTPUT)
