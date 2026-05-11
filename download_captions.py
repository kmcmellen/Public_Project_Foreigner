import subprocess
import os
import re
from datetime import date

def clean_vtt_line(text):
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'&[a-z]+;', '', text)
    text = re.sub(r'\d{2}:\d{2}:\d{2}\.\d{3}', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def build_output_filename(meeting_date):
    return f"transcript_{meeting_date.strftime('%Y_%m_%d')}.txt"

def download_with_ytdlp(video_id, output_file):
    url = f"https://www.youtube.com/watch?v={video_id}"

    subprocess.run([
        "yt-dlp",
        "--write-auto-sub",
        "--sub-lang", "en",
        "--sub-format","vtt",
        "--skip-download",
        "--output", "caption_temp",
        url
    ], check=True)

    vtt_file = None
    for f in os.listdir("."):
        if f.startswith("caption_temp") and f.endswith(".vtt"):
            vtt_file = f
            break

    if not vtt_file:
        raise FileNotFoundError("No caption file found.")

    seen_lines = set()
    clean_lines = []

    with open(vtt_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("WEBVTT"):
                continue
            if "-->" in line:
                continue
            if line.startswith("align:") or line.startswith("position:"):
                continue

            cleaned = clean_vtt_line(line)
            if not cleaned:
                continue

            # Deduplicate repeated lines
            if cleaned not in seen_lines:
                seen_lines.add(cleaned)
                clean_lines.append(cleaned)

    clean_transcript = " ".join(clean_lines)

    os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(clean_transcript)

    os.remove(vtt_file)
    print(f"Transcript written to {output_file}")
    print(f"Total characters: {len(clean_transcript)}")

    return output_file

if __name__ == "__main__":
    import argparse
    from datetime import date

    parser = argparse.ArgumentParser(description="Download and clean YouTube auto-captions.")
    parser.add_argument("--video-id", required=True, help="YouTube video ID")
    parser.add_argument("--date", default=date.today().isoformat(), help="Meeting date (YYYY-MM-DD), defaults to today")
    parser.add_argument("--output-dir", default="output", help="Directory to write transcript (default: output/)")
    args = parser.parse_args()

    meeting_date = date.fromisoformat(args.date)
    filename = build_output_filename(meeting_date)
    output_path = os.path.join(args.output_dir, filename)

    download_with_ytdlp(args.video_id, output_path)