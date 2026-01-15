import re

INPUT = "playlist/playlist.m3u"
OUTPUT = "../live.m3u"

def main():
    with open(INPUT, encoding="utf-8", errors="ignore") as f:
        lines = [l.rstrip() for l in f if l.strip()]

    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write("#EXTM3U\n")

        for i in range(len(lines)):
            if lines[i].startswith("#EXTINF") and i + 1 < len(lines):
                extinf = re.sub(
                    r'group-title="[^"]*"',
                    'group-title="LIVE EVENT"',
                    lines[i]
                )
                out.write(extinf + "\n")
                out.write(lines[i + 1] + "\n")

    print("[PLAYLIST] live.m3u updated")

if __name__ == "__main__":
    main()
