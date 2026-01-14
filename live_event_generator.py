from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB

def parse_time_any(t):
    # support banyak format
    try:
        return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)
    except:
        try:
            return datetime.strptime(t[:15], "%Y%m%dT%H%M%S") + timedelta(hours=TZ)
        except:
            return None

def clean_title(t):
    if not t:
        return None
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=2)

    count = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            start = parse_time_any(p.get("start",""))
            stop = parse_time_any(p.get("stop",""))

            if not start or not stop:
                continue

            if start > limit or stop < now:
                continue

            title = clean_title(p.findtext("title"))
            if not title:
                continue

            # TULIS DUMMY AGAR KELIHATAN
            f.write(f"#EXTINF:-1 group-title=\"DEBUG\",{title}\n")
            f.write("https://bwifi.my.id/hls/video.m3u8\n")
            count += 1

    print(f"[DEBUG] total event ditulis: {count}")

if __name__ == "__main__":
    main()
