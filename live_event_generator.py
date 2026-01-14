import re
from lxml import etree
from datetime import datetime, timedelta

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"
TZ = 7  # WIB

def clean(name):
    for w in ["HD","FHD","UHD","SD","ID","INDO","INDONESIA"]:
        name = re.sub(rf"\b{w}\b", "", name, flags=re.I)
    name = re.sub(r"[|\[\]\(\)_\-]+", " ", name)
    return re.sub(r"\s+", " ", name).strip()

def load_playlist():
    mapping = {}
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            name = clean(lines[i].split(",")[-1])
            url = lines[i+1].strip()
            mapping[name] = url
    return mapping

def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

def main():
    playlist = load_playlist()
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    now = datetime.utcnow() + timedelta(hours=TZ)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            try:
                start = parse_time(p.get("start"))
                stop = parse_time(p.get("stop"))
                if not (start <= now <= stop):
                    continue

                title = p.findtext("title", "LIVE EVENT")
                channel = clean(p.get("channel"))

                if channel not in playlist:
                    continue

                f.write(
                    f'#EXTINF:-1 tvg-id="{channel}" tvg-name="{channel}" '
                    f'group-title="LIVE EVENT",LIVE | {title}\n'
                )
                f.write(playlist[channel] + "\n")
            except:
                continue

    print("[DONE] live.m3u updated")

if __name__ == "__main__":
    main()
