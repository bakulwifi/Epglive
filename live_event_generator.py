from lxml import etree
from datetime import datetime, timedelta
import re

EPG_FILE = "epg.xml"
PLAYLIST_FILE = "playlist.m3u"
OUTPUT_FILE = "live.m3u"

TZ = 7  # WIB
MAX_DAYS = 2  # hari ini + besok
JADWAL_URL = "https://bwifi.my.id/hls/video.m3u8"
LIVE_OFFSET_MINUTES = 5  # ⬅️ PINDAH LIVE 5 MENIT SEBELUM START

# =====================
def parse_time(t):
    return datetime.strptime(t[:14], "%Y%m%d%H%M%S") + timedelta(hours=TZ)

def clean_title(title):
    title = re.sub(r"\(.*?\)", "", title)
    return re.sub(r"\s+", " ", title).strip()

def replace_attr(extinf, attr, value):
    if f'{attr}="' in extinf:
        return re.sub(rf'{attr}="[^"]*"', f'{attr}="{value}"', extinf)
    return extinf

def replace_name(extinf, name):
    return extinf.split(",", 1)[0] + "," + name

# =====================
# ambil SATU blok playlist asli (LIVE)
# =====================
def load_live_block():
    with open(PLAYLIST_FILE, encoding="utf-8", errors="ignore") as f:
        lines = [l.strip() for l in f if l.strip()]
    for i in range(len(lines)):
        if lines[i].startswith("#EXTINF"):
            return lines[i], lines[i + 1]
    return None, None

# =====================
# ambil icon dari epg
# =====================
def load_epg_icons():
    icons = {}
    tree = etree.parse(EPG_FILE)
    for ch in tree.getroot().findall("channel"):
        cid = ch.get("id")
        icon = ch.find("icon")
        if cid and icon is not None and icon.get("src"):
            icons[cid] = icon.get("src")
    return icons

# =====================
def main():
    tree = etree.parse(EPG_FILE)
    root = tree.getroot()
    now = datetime.utcnow() + timedelta(hours=TZ)
    limit = now + timedelta(days=MAX_DAYS)

    epg_icons = load_epg_icons()
    live_extinf, live_url = load_live_block()

    if not live_extinf:
        print("Playlist kosong")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")

        for p in root.findall("programme"):
            try:
                start = parse_time(p.get("start"))
                stop = parse_time(p.get("stop"))

                if start > limit or stop < now:
                    continue

                title = clean_title(p.findtext("title", "MATCH"))
                channel_id = p.get("channel")
                logo = epg_icons.get(channel_id, "")

                live_time = start - timedelta(minutes=LIVE_OFFSET_MINUTES)

                # ===== JADWAL =====
                if now < live_time:
                    name = f"{title} ({start.strftime('%H:%M')})"
                    group = "JADWAL EVENT"
                    extinf = replace_name(live_extinf, name)
                    extinf = replace_attr(extinf, "group-title", group)
                    if logo:
                        extinf = replace_attr(extinf, "tvg-logo", logo)

                    f.write(extinf + "\n")
                    f.write(JADWAL_URL + "\n")

                # ===== LIVE (5 menit sebelum) =====
                elif live_time <= now <= stop:
                    name = title
                    group = "LIVE EVENT"
                    extinf = replace_name(live_extinf, name)
                    extinf = replace_attr(extinf, "group-title", group)
                    if logo:
                        extinf = replace_attr(extinf, "tvg-logo", logo)

                    f.write(extinf + "\n")
                    f.write(live_url + "\n")

            except:
                continue

    print("[DONE] live.m3u (jadwal → live 5 menit sebelum)")

if __name__ == "__main__":
    main()
