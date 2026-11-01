from bookings.service import approve_booking, cancel_booking, create_booking, reject_booking
from bookings.waitlist import join_waitlist, leave_waitlist
from equipment.service import list_equipment

# (method, path, handler)
ROUTES = [
    ("GET", "/equipment", list_equipment),
    ("POST", "/bookings", create_booking),
    ("DELETE", "/bookings/{id}", cancel_booking),
    ("POST", "/bookings/{id}/approve", approve_booking),
    ("POST", "/bookings/{id}/reject", reject_booking),
    ("POST", "/waitlist", join_waitlist),
    ("DELETE", "/waitlist/{id}", leave_waitlist),
]
