from lxml import etree
from datetime import datetime, timedelta

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"
TZ = 7  # WIB

def load_playlist_urls():
    urls = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            urls.append(lines[i+1].strip())
    return urls

def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    now = datetime.utcnow() + timedelta(hours=TZ)

    playlist_urls = load_playlist_urls()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            try:
                start = parse_time(p.get("start"))
                stop = parse_time(p.get("stop"))
                if not (start <= now <= stop):
                    continue

                title = p.findtext("title", "LIVE EVENT")

                # tampilkan event LIVE di SEMUA channel sport
                for url in playlist_urls:
                    f.write(
                        f'#EXTINF:-1 group-title="LIVE EVENT",LIVE | {title}\n'
                    )
                    f.write(url + "\n")

                break  # cukup 1 pertandingan LIVE
            except:
                continue

    print("[OK] live.m3u generated")

if __name__ == "__main__":
    main()
