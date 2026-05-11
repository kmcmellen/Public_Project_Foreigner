# run_latest_transcript.py
import os
from get_latest_council_meeting import get_latest_council_meeting
from download_captions import download_with_ytdlp, build_output_filename
from config import OUTPUT_DIR

def main():
    video_id, title, published_at, meeting_date = get_latest_council_meeting()

    output_file = str(OUTPUT_DIR / build_output_filename(meeting_date))

    print("Latest council meeting selected:")
    print(f"  Title: {title}")
    print(f"  Video ID: {video_id}")
    print(f"  Published at: {published_at}")
    print(f"  Output file: {output_file}")

    download_with_ytdlp(video_id, output_file)

    print(f"Transcript downloaded and saved to {output_file}")

if __name__ == "__main__":
    main()
