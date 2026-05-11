import argparse
import json
import os
from datetime import datetime
from config import OUTPUT_DIR

import requests

from get_latest_council_agenda import (
    get_latest_council_agenda,
    build_meeting_file_url,
)

def build_output_json_filename(meeting_date: str) -> str:
    dt = datetime.strptime(meeting_date, "%Y-%m-%d")
    return str(OUTPUT_DIR / f"civicclerk_agenda_{dt.strftime('%Y_%m_%d')}.json")

def build_output_text_filename(meeting_date: str) -> str:
    dt = datetime.strptime(meeting_date, "%Y-%m-%d")
    return str(OUTPUT_DIR / f"agenda_{dt.strftime('%Y_%m_%d')}.txt")

def build_output_pdf_filename(meeting_date: str) -> str:
    dt = datetime.strptime(meeting_date, "%Y-%m-%d")
    return str(OUTPUT_DIR / f"agenda_{dt.strftime('%Y_%m_%d')}.pdf")

def download_binary_file(url: str, output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

def main():
    parser = argparse.ArgumentParser(
        description="Fetch latest City Council Regular Meeting agenda metadata (and optional text) from CivicClerk."
    )
    parser.add_argument(
        "--date",
        help=(
            "Target meeting date in YYYY-MM-DD (usually the transcript meeting date)."
            "If omitted, uses latest past regular meeting with agenda in recent years."
        ),
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Path to write JSON metadata output.  Defaults to output/civiccleerk_agenda_YYYY_MM_DD.json.",
    )
    parser.add_argument(
        "--download-text",
        action="store_true",
        help="Also download plain-text agend using GetMeetingsFileStream(fileId=...,plainText=true).",
    )
    parser.add_argument(
        "--text-output",
        default=None,
        help="Path for plain-text agenda output.  Defaults to output/agenda_YYYY_MM_DD.txt."
    )

    parser.add_argument(
        "--download-pdf",
        action="store_true",
        default=True,
        help="Download the PDF agenda alongside the JSON metadata.",
    )

    parser.add_argument(
        "--pdf-output",
        default=None,
        help="Path for PDF agenda output.  Defaults to output/agenda_YYYY_MM_DD.pdf",
    )

    args = parser.parse_args()

    data = get_latest_council_agenda(target_date=args.date)
    meeting = data["meeting"]
    meeting_date = meeting["event_date"]

    # Build GetMeetingFileStream ULRs if we have fileIds
    agenda_file_id = meeting.get("agenda_file_id")
    agenda_text_url = (
        build_meeting_file_url(agenda_file_id, plain_text=True)
        if agenda_file_id is not None
        else None
    )
    agenda_pdf_url = (
        build_meeting_file_url(agenda_file_id, plain_text=False)
        if agenda_file_id is not None
        else None
    )

    meeting["agenda_text_url"] = agenda_text_url
    meeting["agenda_pdf_url"] = agenda_pdf_url

    # Write JSON metadata
    json_path = args.output_json or build_output_json_filename(meeting_date)
    os.makedirs(os.path.dirname(json_path), exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"Wrote JSON metadata to {json_path}")
    print(f"Meeting: {meeting['event_name']} ({meeting_date})")
    print(f"Agenda fileId: {meeting.get('agenda_file_id')}")
    print(f"Agenda text URL: {agenda_text_url}")
    print(f"Agenda PDF URL: {agenda_pdf_url}")

    # Download PDF and URL for PDF
    if args.download_pdf and agenda_pdf_url:
        pdf_path = args.pdf_output or build_output_pdf_filename(meeting_date)
        download_binary_file(agenda_pdf_url, pdf_path)
        meeting["agenda_pdf_path"] = pdf_path

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"Wrote PDF file to {pdf_path}")

    # Optionally download the plain-text agenda
    if args.download_text and agenda_text_url:
        text_path = args.text_output or build_output_text_filename(meeting_date)
        resp = requests.get(agenda_text_url, timeout=60)
        resp.raise_for_status()
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w", encoding="utf-8") as tf:
            tf.write(resp.text)
        print(f"Wrote text file to {text_path}")

if __name__ == "__main__":
    main()
