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

def load_icons(root):
    icons = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            icons[cid] = icon.get("src")
    return icons

def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    icons = load_icons(root)

    count = 0

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            title = clean_title(p.findtext("title"))
            cid = p.get("channel")

            if not title or cid not in icons:
                continue

            f.write(
                f'#EXTINF:-1 tvg-id="" tvg-name="{title}" '
                f'tvg-logo="{icons[cid]}" group-title="JADWAL EVENT",{title}\n'
            )
            f.write(URL + "\n")
            count += 1

    print(f"[STABLE] total ditulis: {count}")

if __name__ == "__main__":
    main()
