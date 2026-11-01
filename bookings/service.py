from datetime import datetime, timedelta, timezone

from bookings.models import (
    BOOKINGS,
    STATUS_APPROVED,
    STATUS_CANCELLED,
    STATUS_PENDING,
    STATUS_REJECTED,
    Booking,
)
from bookings.rules import MAX_ACTIVE_BOOKINGS, MAX_BOOKING_HOURS, overlaps
from core.errors import BookingError, NotAllowedError
from core.roles import Role
from equipment.models import STATUS_IN_REPAIR
from equipment.service import get_equipment
from notifications.dispatcher import notify_booking_approved, notify_booking_rejected
from penalties.rules import LATE_CANCEL_WINDOW_HOURS, apply_late_cancel_penalty


def create_booking(student_id: int, equipment_id: int, start: datetime, end: datetime) -> Booking:
    equipment = get_equipment(equipment_id)
    if equipment.status == STATUS_IN_REPAIR:
        raise BookingError("this equipment is in repair")
    if end <= start:
        raise BookingError("the booking must end after it starts")
    if end - start > timedelta(hours=MAX_BOOKING_HOURS):
        raise BookingError(f"a booking can be at most {MAX_BOOKING_HOURS} hours")

    active = [
        b for b in BOOKINGS.values()
        if b.status in (STATUS_PENDING, STATUS_APPROVED) and b.end > datetime.now(timezone.utc)
    ]
    if sum(1 for b in active if b.student_id == student_id) >= MAX_ACTIVE_BOOKINGS:
        raise BookingError(f"a student can have at most {MAX_ACTIVE_BOOKINGS} active bookings")
    if any(b.equipment_id == equipment_id and overlaps(start, end, b.start, b.end) for b in active):
        raise BookingError("this slot overlaps another booking")

    status = STATUS_PENDING if equipment.restricted else STATUS_APPROVED
    booking = Booking(len(BOOKINGS) + 1, student_id, equipment_id, start, end, status)
    BOOKINGS[booking.id] = booking
    if status == STATUS_APPROVED:
        notify_booking_approved(booking)
    return booking


def cancel_booking(booking_id: int, student_id: int, now: datetime | None = None) -> Booking:
    now = now or datetime.now(timezone.utc)
    booking = BOOKINGS.get(booking_id)
    if booking is None or booking.student_id != student_id:
        raise BookingError("booking not found")
    if booking.start <= now:
        raise BookingError("a booking that has started cannot be cancelled")
    if booking.start - now < timedelta(hours=LATE_CANCEL_WINDOW_HOURS):
        apply_late_cancel_penalty(student_id, booking_id)
    booking.status = STATUS_CANCELLED
    return booking


def approve_booking(booking_id: int, actor_role: Role) -> Booking:
    if actor_role != Role.LAB_TECHNICIAN:
        raise NotAllowedError("only a lab technician can approve bookings")
    booking = BOOKINGS.get(booking_id)
    if booking is None or booking.status != STATUS_PENDING:
        raise BookingError("no pending booking with this id")
    booking.status = STATUS_APPROVED
    notify_booking_approved(booking)
    return booking


def reject_booking(booking_id: int, actor_role: Role, reason: str) -> Booking:
    if actor_role != Role.LAB_TECHNICIAN:
        raise NotAllowedError("only a lab technician can reject bookings")
    booking = BOOKINGS.get(booking_id)
    if booking is None or booking.status != STATUS_PENDING:
        raise BookingError("no pending booking with this id")
    booking.status = STATUS_REJECTED
    notify_booking_rejected(booking, reason)
    return booking


def list_bookings_for_student(student_id: int) -> list[Booking]:
    return sorted(
        (b for b in BOOKINGS.values() if b.student_id == student_id),
        key=lambda b: b.start,
    )
