import requests
import gzip
from lxml import etree

EPG_OUTPUT = "epg.xml"

EPG_SOURCES = [
    # Open-EPG Indonesia
    "https://www.open-epg.com/files/indonesia2.xml.gz",

    # StarHub TV EPG
    "https://raw.githubusercontent.com/dbghelp/StarHub-TV-EPG/refs/heads/main/starhub.xml",

    # EPG.pw publik
    "https://epg.pw/xmltv/epg_ID.xml",
    "https://epg.pw/xmltv/epg.xml",
    "https://epg.pw/xmltv/epg.xml.gz",

    # EPGShare gabungan
    "http://epgshare01.online/epgshare01/epg_ripper_ALL_SOURCES1.xml.gz",
]

HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_epg(url):
    r = requests.get(url, headers=HEADERS, timeout=40)
    r.raise_for_status()
    data = r.content
    if url.endswith(".gz"):
        data = gzip.decompress(data)
    return etree.fromstring(data)

def main():
    tv = etree.Element("tv", generator_info_name="Multi Source Sports EPG")
    channel_ids = set()

    for url in EPG_SOURCES:
        try:
            root = load_epg(url)

            # channel
            for ch in root.findall("channel"):
                cid = ch.get("id")
                if cid and cid not in channel_ids:
                    channel_ids.add(cid)
                    tv.append(ch)

            # programme
            for pr in root.findall("programme"):
                tv.append(pr)

            print(f"[OK] {url}")
        except Exception as e:
            print(f"[SKIP] {url} -> {e}")

    with open(EPG_OUTPUT, "wb") as f:
        f.write(etree.tostring(
            tv,
            pretty_print=True,
            xml_declaration=True,
            encoding="UTF-8"
        ))

    print("[DONE] epg.xml updated")

if __name__ == "__main__":
    main()
