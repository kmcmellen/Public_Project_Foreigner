import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, date, timedelta
from typing import Optional, Dict, Any, List

import requests

BASE_API = "https://sandyspringsga.api.civicclerk.com/v1"
#BASE_PORTAL = "https://sandyspringsga.portal.civicclerk.com"
USER_AGENT = "Mozilla/5.0 (compatible; SandySpringsAgendaFetcher/1.0"


@dataclass
class CouncilMeeting:
    event_id: int
    event_name: str
    event_date: str             #ISO date, e.g. "2026-04-21"
    event_datetime_utc: str     #original startDateTime/eventDate
    category_name: str
    agenda_id: Optional[int]
    agenda_name: Optional[str]
    agenda_file_id: Optional[int]
    agenda_packet_file_id: Optional[int]
    minutes_file_id: Optional[int]
    meeting_type_name: Optional[str]
    published_agenda_timestamp: Optional[str]


class CivicClerkClient:
    def __init__(self, base_api: str = BASE_API):
        self.base_api = base_api.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})

    def get_events(self) ->Dict[str, Any]:
        # Fetch all paged City Council events with agendas by following @odata.nextLink.

        url = (
            f"{self.base_api}/Events/"
            "?$orderby=eventDate%20desc"
            "&$filter=categoryName%20eq%20%27City%20Council%27%20and%20hasAgenda%20eq%20true"
        )

        all_events = []
        page_num = 1

        while url:
            #print(f"DEBUG fetching page {page_num}: {url}")
            resp = self.session.get(url, timeout=60)
            resp.raise_for_status()
            data = resp.json()

            page_events = data.get("value", [])
            #print(f"DEBUG page {page_num} events: {len(page_events)}")

            all_events.extend(page_events)

            url = data.get("@odata.nextLink")
            page_num += 1

        #print(f"DEBUG total events fetched across all pages: {len(all_events)}")
        return {"value": all_events}

    @staticmethod
    def _is_council_regular(event: Dict[str, Any]) -> bool:
        """
        Identify regular City Council meetings.

        Sandy Springs appears to use 'City Council Meeting' for regular meetings,
        while Work Session/Special Called/Retreat/etc. are labeled explicitly.
        """
        name = (event.get("eventName") or "").lower()
        category = (
            event.get("categoryName")
            or event.get("eventCategoryName")
            or ""
        ).lower()

        # Must be a City Council event
        if "city council" not in category:
            return False

        #Exclude known non-regular variants
        excluded_terms = [
            "work session",
            "special",
            "retreat",
            "budget workshop",
            "executive session",
            "committee",
            "town hall",
            "canceled",
            "cancelled",
        ]
        if any(term in name for term in excluded_terms):
            return False
        #Accept plain "City Council Meeting" and also explicit "Regular"
        if "city council meeting" in name:
            return True
        if "regular" in name:
            return True

        #otherwise treat as non-regular
        return False

    @staticmethod
    def _parse_iso_date(dt_str: str) -> datetime:
        # CivicClerk uses e.g. "2020-01-07T18:30:00Z" [file:244]
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))

    def _pick_best_published_file_id(self, published_files: List[Dict[str, Any]], file_type: str
    ) -> Optional[int]:
        """
        Pick URL for a given published file type ("Agenda", "Agenda Packet",
        "Minutes".) [file:243][file:244]
        """
        candidates = [f for f in published_files if f.get("type") == file_type]
        if not candidates:
            return None

        # prefer ones whose name includes "Updated" for agenda/agendapacket. [file:243]
        if file_type in {"Agenda", "Agenda Packet"}:
            updated = [
                f for f in candidates
                if "updated" in (f.get("name") or "").lower()
            ]
            if updated:
                candidates = updated

        # If there are still multiple, keep the first by sort order
        candidates.sort(key=lambda f: f.get("sort", 0))
        fid = candidates[0].get("fileId")
        return fid if isinstance(fid, int) else None

    def get_latest_council_regular_meeting(
            self,
            target_date: Optional[date] = None,
            past_only: bool = True,
            recent_years: int = 4,
    ) -> CouncilMeeting:
        data = self.get_events()
        events = data.get("value", []) # OData response structure. [file:243][file:244]

        # --- DEBUG START ---
        #print("DEBUG sample 10 events (name, date):")
        #for e in events[:10]:
        #    print (" ", e.get("eventName"), "|", e.get("eventDate"))

        #print(f"DEBUG total events returned: {len(events)}")
        #if events:
        #    print(f"DEBUG first event keys: {list(events[0].keys())}")
        #    print(f"DEBUG first event sample: {events[0]}")
        #    recent = [e for e in events if "2026" in str(e.get("eventDate", "") or e.get("startDateTime", ""))]
        #    print(f"DEBUG events with 2026 in date: {len(recent)}")
        # --- DEBUG END ---



        now_utc = datetime.now(timezone.utc)
        #print("DEBUG now_utc:", now_utc.isoformat())

        def get_dt(e: Dict[str, Any]) -> datetime:
            raw = e.get("eventDate") or e.get("startDateTime")
            if not raw:
                return datetime(1900, 1, 1, tzinfo=timezone.utc)
            return self._parse_iso_date(raw)

        def to_local_date(e: Dict[str, Any]) -> date:
            return get_dt(e).date()

        #cutoff_date = (now_utc - timedelta(days=365 * recent_years)).date()

        base = [
            e for e in events
            if self._is_council_regular(e)
            and e.get("hasAgenda") is True
               and (not past_only or get_dt(e) <= now_utc)
              # and to_local_date(e) >= cutoff_date
        ]

        #print(f"DEBUG filtered past regular meetings: {len(base)}")
        #print(f"DEBUG top 5 filtered dates:", [e.get("eventDate") for e in base[:5]])
        #print(f"DEBUG top 5 filtered names:", [e.get("eventName") for e in base[:5]])

        if not base:
            raise RuntimeError("No suitable City Council Regular Meeting with agenda found.")

        if target_date is not None:
            same_day = [e for e in base if to_local_date(e) == target_date]
            if same_day:
                same_day.sort(key=get_dt, reverse=True)
                latest = same_day[0]
            else:
                before = [e for e in base if to_local_date(e) < target_date]
                if not before:
                    raise RuntimeError(f"No council regular meeting with agenda on or before {target_date}.")
                before.sort(key=get_dt, reverse=True)
                latest = before[0]
        else:
            base.sort(key=get_dt, reverse=True)
            latest = base[0]

        published_files = latest.get("publishedFiles") or []

        agenda_file_id = self._pick_best_published_file_id(published_files, "Agenda")
        agenda_packet_file_id = self._pick_best_published_file_id(published_files, "Agenda Packet")
        minutes_file_id = self._pick_best_published_file_id(published_files, "Minutes")

        dt = get_dt(latest)

        return CouncilMeeting(
            event_id=latest.get("id"),
            event_name=latest.get("eventName") or "",
            event_date=dt.date().isoformat(),
            event_datetime_utc=(latest.get("eventDate") or latest.get("startDateTime") or ""),
            category_name=latest.get("eventCategoryName") or latest.get("categoryName") or "",
            agenda_id=latest.get("agendaId"),
            agenda_name=latest.get("agendaName"),
            agenda_file_id=agenda_file_id,
            agenda_packet_file_id=agenda_packet_file_id,
            minutes_file_id=minutes_file_id,
            meeting_type_name=latest.get("meetingTypeName"),
            published_agenda_timestamp=latest.get("publishedAgendaTimestamp"),
        )

def build_meeting_file_url(file_id: int, plain_text: bool = False) -> str:
    """
    Build the GetMeetingFileStream URL mathcing your working training script pattern. [file:229][file:242]
    """
    plain = "true" if plain_text else "false"
    return (
        f"{BASE_API}/Meetings/"
        f"GetMeetingFileStream(fileId={file_id},plainText={plain})"
    )

def get_latest_council_agenda(target_date: Optional[str] = None) -> Dict[str, Any]:
    """
    High-level convenience: returns JSON-friendly structure with meeting metadata and fileIds (not fragile stream URLs).
    """
    client = CivicClerkClient()
    td: Optional[date] = None
    if target_date:
        td = datetime.strptime(target_date, "%Y-%m-%d").date()

    meeting = client.get_latest_council_regular_meeting(target_date=td)
    return {
        "source": "CivicClerk",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "meeting": asdict(meeting),
    }

