import re
import requests
from bs4 import BeautifulSoup
from lxml import etree
from datetime import datetime, timedelta

M3U_FILE = "playlist.m3u"
EPG_OUTPUT = "epg.xml"
URL = "https://www.livesoccertv.com/id/schedules/"
TZ = "+0700"

HEADERS = {"User-Agent": "Mozilla/5.0"}

def clean(name):
    for w in ["HD","FHD","UHD","SD","ID","INDO","INDONESIA"]:
        name = re.sub(rf"\b{w}\b", "", name, flags=re.I)
    name = re.sub(r"[|\[\]\(\)_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()

def load_channels():
    channels = set()
    with open(M3U_FILE, encoding="utf-8", errors="ignore") as f:
        for l in f:
            if l.startswith("#EXTINF"):
                channels.add(clean(l.split(",")[-1]))
    return sorted(channels)

def scrape():
    r = requests.get(URL, headers=HEADERS, timeout=20)
    soup = BeautifulSoup(r.text, "html.parser")
    data = []

    for row in soup.select(".matchrow"):
        try:
            title = row.select_one(".teams").text.strip()
            time = row.select_one(".time").text.strip()
            league = row.select_one(".competition").text.strip()
            chs = [clean(c.text) for c in row.select(".channel")]

            data.append({
                "title": title,
                "time": time,
                "league": league,
                "channels": chs
            })
        except:
            continue
    return data

def build(channels, matches):
    tv = etree.Element("tv", generator_info_name="LiveSoccerTV EPG")
    today = datetime.now()

    for ch in channels:
        c = etree.SubElement(tv, "channel", id=ch)
        etree.SubElement(c, "display-name").text = ch

    for m in matches:
        try:
            start = datetime.strptime(m["time"], "%H:%M")
            start = start.replace(year=today.year, month=today.month, day=today.day)
            stop = start + timedelta(hours=2)
        except:
            continue

        for ch in m["channels"]:
            if ch not in channels:
                continue

            p = etree.SubElement(
                tv,
                "programme",
                start=start.strftime("%Y%m%d%H%M%S ") + TZ,
                stop=stop.strftime("%Y%m%d%H%M%S ") + TZ,
                channel=ch
            )
            etree.SubElement(p, "title").text = m["title"]
            etree.SubElement(p, "desc").text = m["league"]

    return tv

def main():
    chs = load_channels()
    matches = scrape()
    tv = build(chs, matches)

    with open(EPG_OUTPUT, "wb") as f:
        f.write(etree.tostring(tv, pretty_print=True, xml_declaration=True, encoding="UTF-8"))

if __name__ == "__main__":
    main()
