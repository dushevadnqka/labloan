from dataclasses import dataclass
from datetime import datetime, timezone

from core.errors import BookingError
from equipment.service import get_equipment


@dataclass
class WaitlistEntry:
    id: int
    student_id: int
    equipment_id: int
    joined_at: datetime


WAITLIST: dict[int, WaitlistEntry] = {}


def join_waitlist(student_id: int, equipment_id: int) -> WaitlistEntry:
    get_equipment(equipment_id)
    if any(e.student_id == student_id and e.equipment_id == equipment_id for e in WAITLIST.values()):
        raise BookingError("already on the waitlist for this equipment")
    entry = WaitlistEntry(len(WAITLIST) + 1, student_id, equipment_id, datetime.now(timezone.utc))
    WAITLIST[entry.id] = entry
    return entry


def leave_waitlist(entry_id: int, student_id: int) -> None:
    entry = WAITLIST.get(entry_id)
    if entry is None or entry.student_id != student_id:
        raise BookingError("waitlist entry not found")
    del WAITLIST[entry_id]


def position_in_waitlist(entry_id: int) -> int:
    entry = WAITLIST.get(entry_id)
    if entry is None:
        raise BookingError("waitlist entry not found")
    ahead = [
        e for e in WAITLIST.values()
        if e.equipment_id == entry.equipment_id and e.joined_at <= entry.joined_at
    ]
    return len(ahead)
