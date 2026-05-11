from googleapiclient.discovery import build
from authenticate import get_credentials

VIDEO_ID = "NjUMKBDpNiQ"

creds = get_credentials()
youtube = build("youtube", "v3", credentials=creds)

captions_response = youtube.captions().list(
    part="snippet",
    videoId=VIDEO_ID,
).execute()

for caption in captions_response["items"]:
    caption_id = caption["id"]
    lang = caption["snippet"]["language"]
    kind = caption["snippet"]["trackKind"] # "asr" = auto-generated
    print(f"Caption ID: {caption_id} | Language: {lang} | Type: {kind}")