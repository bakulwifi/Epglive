import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

# ================= CONFIG =================
EPG_URL = "https://raw.githubusercontent.com/bakulwifi/Epglive/refs/heads/main/epg.xml"
SOURCE_M3U = "playlist/playlist.m3u"

LIVE_OUT = "live.m3u"
JADWAL_OUT = "jadwal.m3u"

BWIFI_STREAM = "https://bwifi.my.id/hls/video.m3u8"
MAX_CHANNEL_PER_MATCH = 3
LIVE_OFFSET_MIN = 5

WIB = timezone(timedelta(hours=7))

SPORT_KEYWORDS = [
    "vs", "liga", "league", "cup", "final", "ucl", "afc",
    "bundesliga", "laliga", "serie", "premier", "qualifier", "champion"
]
# ==========================================


def is_sport(title: str) -> bool:
    t = title.lower()
    return any(k in t for k in SPORT_KEYWORDS)


def normalize_name(name: str) -> str:
    name = re.sub(r"[^a-z0-9 ]", "", name.lower())
    parts = name.split()
    return " ".join(parts[:2]) if len(parts) >= 2 else name


def parse_time(start: str) -> datetime:
    dt = datetime.strptime(start[:14], "%Y%m%d%H%M%S")
    return dt.replace(tzinfo=timezone.utc).astimezone(WIB)


# ---------- LOAD EPG ----------
def load_epg():
    r = requests.get(EPG_URL, timeout=30)
    r.raise_for_status()
    root = ET.fromstring(r.content)

    events = []
    for p in root.findall("programme"):
        title = p.findtext("title")
        ch = p.attrib.get("channel", "")
        start = p.attrib.get("start")

        if not title or not start:
            continue
        if not is_sport(title):
            continue

        start_wib = parse_time(start)

        events.append({
            "title": title.strip(),
            "channel": ch.strip(),
            "norm_channel": normalize_name(ch),
            "start": start_wib
        })
    return events


# ---------- LOAD PLAYLIST BLOKS ----------
def load_playlist_blocks():
    with open(SOURCE_M3U, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    blocks, buf = [], []
    for line in lines:
        if line.startswith("#EXTINF"):
            if buf:
                blocks.append(buf)
            buf = [line]
        elif buf:
            buf.append(line)
    if buf:
        blocks.append(buf)

    parsed = []
    for b in blocks:
        ext = b[0]
        name = ext.split(",")[-1].strip()
        url = b[-1].strip()
        parsed.append({
            "raw": b,
            "name": name,
            "norm": normalize_name(name),
            "url": url
        })
    return parsed


# ---------- MAIN ----------
def main():
    now = datetime.now(WIB)

    epg_events = load_epg()
    playlist = load_playlist_blocks()

    live_seen = set()
    jadwal_seen = set()

    live_out = ["#EXTM3U\n"]
    jadwal_out = ["#EXTM3U\n"]

    for ev in epg_events:
        match_key = f"{ev['title']}{ev['start']}"
        channel_count = 0

        is_live = now >= (ev["start"] - timedelta(minutes=LIVE_OFFSET_MIN))
        jam = ev["start"].strftime("%H:%M WIB")

        for pl in playlist:
            if channel_count >= MAX_CHANNEL_PER_MATCH:
                break

            if ev["norm_channel"] not in pl["norm"] and pl["norm"] not in ev["norm_channel"]:
                continue

            judul = f'{ev["title"]} ({jam}) - {pl["name"]}'

            if is_live:
                # ---- LIVE ----
                event_key = f"{match_key}{pl['name']}{pl['url']}"
                if event_key in live_seen:
                    continue

                live_out.append(f'#EXTINF:-1 group-title="LIVE EVENT",{judul}\n')
                live_out.extend(pl["raw"][1:])
                live_seen.add(event_key)
                channel_count += 1

            else:
                # ---- JADWAL ----
                event_key = f"{match_key}{pl['name']}"
                if event_key in jadwal_seen:
                    continue

                jadwal_out.append(f'#EXTINF:-1 group-title="JADWAL EVENT",{judul}\n')
                jadwal_out.append(BWIFI_STREAM + "\n")
                jadwal_seen.add(event_key)
                channel_count += 1

    with open(LIVE_OUT, "w", encoding="utf-8") as f:
        f.writelines(live_out)

    with open(JADWAL_OUT, "w", encoding="utf-8") as f:
        f.writelines(jadwal_out)

    print("SUCCESS: auto switch H-5 & max 3 channel per match")


if __name__ == "__main__":
    main()
