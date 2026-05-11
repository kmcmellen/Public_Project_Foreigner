import re
from datetime import datetime
from googleapiclient.discovery import build
from authenticate import get_credentials
from list_videos import video_id

# City of Sandy Springs channel ID (from our YouTube Channel)
CHANNEL_ID = "UCO0tB3M4usnBgwveV0Kdc1Q"

DATE_PATTERN = re.compile(
    r'([A-Za-z]+)\s+(\d{1,2}),\s+(\d{4})'
)

def is_council_title(title: str) -> bool:
    t = title.lower()
    return "city council meeting" in t or "city council meetings" in t

def is_updated_variant(title: str) -> bool:
    return "updated" in title.lower()

def extract_meeting_date(title: str):
    """
    Try to pull 'Month Day, Year' from the title.
    Returns a date object or None.
    """
    m = DATE_PATTERN.match(title)
    if not m:
        return None
    month_name, day_str, year_str = m.groups()
    try:
        dt = datetime.strptime(
            f"{month_name} {day_str} {year_str}", "%B %d %Y"
        )
        return dt.date() # just the date
    except ValueError:
        return None

def get_latest_council_meeting():
    creds = get_credentials()
    youtube = build("youtube", "v3", credentials=creds)

    search_response = youtube.search().list(
        part="snippet",
        channelId=CHANNEL_ID,
        order="date",
        type="video",
        maxResults=50, # larger window to be safe
    ).execute()

    items = search_response.get("items", [])
    if not items:
        raise RuntimeError("No videos returned from search().")

    # candidates[meeting_date] = list videos for that meeting date
    candidates_by_date = {}

    for item in items:
        snippet = item["snippet"]
        title = snippet["title"]
        if not is_council_title(title):
            continue

        video_id = item["id"]["videoId"]
        published_at = snippet["publishedAt"]
        updated = is_updated_variant(title)
        meeting_date = extract_meeting_date(title)

        # Fallback: if we can't parse a date from title, skip (or use published_at date)

        if meeting_date is None:
            try:
                meeting_date = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                ).date()
            except Exception:
                continue

        entry = {
            "video_id": video_id,
            "title": title,
            "published_at": published_at,
            "updated": updated,
            "meeting_date": meeting_date,
        }
        candidates_by_date.setdefault(meeting_date, []).append(entry)

    if not candidates_by_date:
        raise RuntimeError("Mo recent council meeting videos found.")

    # Find the latest meeting_date
    latest_meeting_date = max(candidates_by_date.keys())
    videos_for_latest = candidates_by_date[latest_meeting_date]

    # Among videos for that date, prefer an updated variant if present
    updated_videos = [v for v in videos_for_latest if v["updated"]]
    if updated_videos:
        # If multiple updated ones, pick the latest by published_at
        updated_videos.sort(key=lambda v: v["published_at"], reverse=True)
        chosen = updated_videos[0]
    else:
        # No updated variant, pick the latest by published_at
        videos_for_latest.sort(key=lambda v: v["published_at"], reverse=True)
        chosen = videos_for_latest[0]

    return (
        chosen["video_id"],
        chosen["title"],
        chosen["published_at"],
        chosen["meeting_date"],
    )

if __name__ == "__main__":
    vid, title, ts, mdate = get_latest_council_meeting()
    print("Latest council meeting:")
    print("  Video ID:", vid)
    print("  Title:", title)
    print("  Published at:", ts)
