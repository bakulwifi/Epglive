from lxml import etree
import requests
import gzip
from io import BytesIO

EPG_SOURCES = [
    "https://www.open-epg.com/files/indonesia2.xml.gz",
    "https://raw.githubusercontent.com/dbghelp/StarHub-TV-EPG/refs/heads/main/starhub.xml"
]

OUTPUT = "../epg.xml"

SPORT_KEYWORDS = [
    "vs", " v ", "liga", "league",
    "cup", "afc", "uefa", "fifa",
    "football", "soccer", "sport"
]

def is_sport(text):
    if not text:
        return False
    t = text.lower()
    return any(k in t for k in SPORT_KEYWORDS)

def parse_xml(data):
    return etree.parse(BytesIO(data)).getroot()

def main():
    tv = etree.Element("tv")

    channel_written = False

    for url in EPG_SOURCES:
        try:
            r = requests.get(url, timeout=30)
            data = r.content
            if url.endswith(".gz"):
                data = gzip.decompress(data)

            root = parse_xml(data)

            # channel: ambil display-name sekali saja
            if not channel_written:
                for ch in root.findall("channel"):
                    name = ch.findtext("display-name")
                    if name:
                        ch_out = etree.SubElement(tv, "channel")
                        etree.SubElement(ch_out, "display-name").text = name
                        channel_written = True
                        break

            # programme
            for p in root.findall("programme"):
                title = p.findtext("title")
                if not is_sport(title):
                    continue

                start = p.get("start")
                stop = p.get("stop")

                prog = etree.SubElement(tv, "programme")
                if start:
                    prog.set("start", start)
                if stop:
                    prog.set("stop", stop)

                etree.SubElement(prog, "title").text = title.strip()

        except Exception as e:
            print("EPG error:", url, e)

    etree.ElementTree(tv).write(
        OUTPUT,
        encoding="utf-8",
        xml_declaration=True
    )

    print("[OK] epg.xml updated (SPORT ONLY, MINIMAL)")

if __name__ == "__main__":
    main()
