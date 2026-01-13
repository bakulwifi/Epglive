import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

M3U_FILE = "playlist.m3u"
LIVE_OUTPUT = "live.m3u"
URL = "https://www.livesoccertv.com/id/schedules/"
TZ = 7
LIVE_DURATION = 120  # menit

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(name):
    for w in ["HD","FHD","UHD","SD","ID","INDO","INDONESIA"]:
        name = re.sub(rf"\b{w}\b", "", name, flags=re.I)
    name = re.sub(r"[|\[\]\(\)_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()

def load_playlist():
    blocks = []
    with open(M3U_FILE, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        if line.startswith("#EXTINF"):
            name = clean(line.split(",")[-1])
            url = lines[i+1].strip()
            blocks.append((name, line, url))
    return blocks

def scrape_live():
    now = datetime.utcnow() + timedelta(hours=TZ)
    r = requests.get(URL, headers=HEADERS)
    soup = BeautifulSoup(r.text, "html.parser")
    lives = []

    for row in soup.select(".matchrow"):
        try:
            title = row.select_one(".teams").text.strip()
            time = row.select_one(".time").text.strip()
            chs = [clean(c.text) for c in row.select(".channel")]

            start = datetime.strptime(time, "%H:%M")
            start = start.replace(year=now.year, month=now.month, day=now.day)
            end = start + timedelta(minutes=LIVE_DURATION)

            if start <= now <= end:
                lives.append((title, chs))
        except:
            continue

    return lives

def generate():
    playlist = load_playlist()
    lives = scrape_live()

    with open(LIVE_OUTPUT, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for title, channels in lives:
            for ch in channels:
                for name, extinf, url in playlist:
                    if name == ch:
                        f.write(
                            f'#EXTINF:-1 group-title="LIVE EVENT",LIVE | {title}\n'
                        )
                        f.write(url + "\n")

if __name__ == "__main__":
    generate()
