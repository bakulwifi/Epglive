from lxml import etree
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"

# ======================
def norm(s):
    s = s.lower()
    s = re.sub(r"(hd|fhd|uhd|sd)", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())

def clean_title(t):
    return re.sub(r"\(.*?\)", "", t).strip()

# ======================
def load_epg(root):
    data = {}
    for ch in root.findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None:
            data[cid] = {
                "short": " ".join(norm(cid).split()[:3]),
                "logo": icon.get("src")
            }
    return data

# ======================
def load_playlist():
    blocks = []
    try:
        with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
            lines = [l.strip() for l in f if l.strip()]
        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                name = norm(lines[i].split(",")[-1])
                blocks.append({
                    "short": " ".join(name.split()[:3]),
                    "extinf": lines[i],
                    "url": lines[i + 1]
                })
    except:
        pass
    return blocks

def find_block(epg_short, blocks):
    for b in blocks:
        if set(epg_short.split()) & set(b["short"].split()):
            return b
    return None

# ======================
def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()

    epg_channels = load_epg(root)
    playlist_blocks = load_playlist()

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        total = 0
        for p in root.findall("programme"):
            title = p.findtext("title")
            cid = p.get("channel")
            if not title or cid not in epg_channels:
                continue

            title = clean_title(title)
            ch = epg_channels[cid]
            name = f"{title} {cid}"
            logo = ch["logo"]

            block = find_block(ch["short"], playlist_blocks)

            # ===== LIVE (kalau ketemu playlist)
            if block:
                extinf = block["extinf"].split(",", 1)[0] + "," + name
                extinf = re.sub(r'tvg-logo="[^"]*"', f'tvg-logo="{logo}"', extinf)
                extinf = re.sub(r'group-title="[^"]*"', 'group-title="LIVE EVENT"', extinf)
                f.write(extinf + "\n")
                f.write(block["url"] + "\n")
            else:
                # ===== JADWAL (fallback keras)
                f.write(
                    f'#EXTINF:-1 tvg-id="" tvg-name="{name}" '
                    f'tvg-logo="{logo}" group-title="JADWAL EVENT",{name}\n'
                )
                f.write(JADWAL_URL + "\n")

            total += 1

    print(f"[FINAL] total channel ditulis: {total}")

if __name__ == "__main__":
    main()
