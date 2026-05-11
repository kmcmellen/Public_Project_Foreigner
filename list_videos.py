from googleapiclient.discovery import build

API_KEY = "AIzaSyDLevkbDjjOu_-Iz9PYnJZNXZ_iFCoZEr4"
CHANNEL_ID = "UCO0tB3M4usnBgwveV0Kdc1Q" # Sandy Springs Channel ID

youtube = build("youtube", "v3", developerKey=API_KEY)

# Get the channel's uploads playlist ID first
channel_response = youtube.channels().list(
    part="contentDetails",
    id=CHANNEL_ID
).execute()

uploads_playlist_id = channel_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

#Now list recent videos from that playlist
playlist_response = youtube.playlistItems().list(
    part="snippet",
    playlistId=uploads_playlist_id,
    maxResults=10
).execute()

for item in playlist_response["items"]:
    video_id = item["snippet"]["resourceId"]["videoId"]
    title = item["snippet"]["title"]
    published = item["snippet"]["publishedAt"]
    print(f"{published[:10]} | {video_id} | {title}")