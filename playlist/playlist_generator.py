from lxml import etree
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist/playlist.m3u"
OUTPUT_FILE = "live.m3u"

JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"

SOCCER_KEYWORDS = [
    " vs ", " v ", "football", "soccer",
    "liga", "league", "cup"
]

def is_soccer(title):
    t = title.lower()
    return any(k in t for k in SOCCER_KEYWORDS)

def load_epg():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    icons = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            icons[cid] = icon.get("src")

    programmes = []
    for p in root.findall("programme"):
        title = p.findtext("title")
        cid = p.get("channel")
        if title and cid and is_soccer(title):
            programmes.append({
                "title": title.strip(),
                "cid": cid,
                "logo": icons.get(cid, "")
            })

    return programmes

def load_playlist_blocks():
    blocks = []
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip() for l in f if l.strip()]

    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
            blocks.append({
                "extinf": lines[i],
                "url": lines[i + 1]
            })
    return blocks

def replace(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf.replace("#EXTINF", f'#EXTINF {attr}="{value}"', 1)

def rename(extinf, name):
    return extinf.split(",", 1)[0] + "," + name

def main():
    programmes = load_epg()
    blocks = load_playlist_blocks()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        # ===== LIVE EVENT =====
        epg_index = 0
        for block in blocks:
            extinf = block["extinf"]
            url = block["url"]

            if epg_index < len(programmes):
                p = programmes[epg_index]
                name = f"{p['title']} ({p['cid']})"
                logo = p["logo"]
                epg_index += 1
            else:
                name = extinf.split(",", 1)[-1]
                logo = ""

            extinf = rename(extinf, name)
            extinf = replace(extinf, "tvg-logo", logo)
            extinf = replace(extinf, "group-title", "LIVE EVENT")

            f.write(extinf + "\n")
            f.write(url + "\n")

        # ===== JADWAL EVENT =====
        for p in programmes:
            name = f"{p['title']} ({p['cid']})"
            f.write(
                f'#EXTINF:-1 tvg-id="" tvg-name="{name}" '
                f'tvg-logo="{p["logo"]}" group-title="JADWAL EVENT",{name}\n'
            )
            f.write(JADWAL_URL + "\n")

    print("[OK] live.m3u updated (SOCCER ONLY)")

if __name__ == "__main__":
    main()
