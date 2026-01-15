from lxml import etree
import re

EPG_FILE = "epg.xml"
OUTPUT_FILE = "live.m3u"
URL = "https://bwifi.my.id/hls/video.m3u8"

def clean_title(t):
    if not t:
        return None
    t = re.sub(r"\(.*?\)", "", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()

def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    count = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            title = clean_title(p.findtext("title"))
            if not title:
                continue

            f.write(
                f'#EXTINF:-1 group-title="DEBUG EVENT",{title}\n'
            )
            f.write(URL + "\n")
            count += 1

    print(f"[DEBUG FINAL] total programme ditulis: {count}")

if __name__ == "__main__":
    main()
