import pytest

from bookings.waitlist import WAITLIST, join_waitlist, leave_waitlist, position_in_waitlist
from core.errors import BookingError
from equipment.models import EQUIPMENT, Equipment


def setup_function():
    WAITLIST.clear()
    EQUIPMENT[3] = Equipment(3, "3D printer", "fabrication", restricted=True)


def test_students_get_positions_in_join_order():
    first = join_waitlist(10, 3)
    second = join_waitlist(11, 3)
    assert position_in_waitlist(first.id) == 1
    assert position_in_waitlist(second.id) == 2


def test_joining_twice_is_refused():
    join_waitlist(10, 3)
    with pytest.raises(BookingError):
        join_waitlist(10, 3)


def test_leaving_removes_the_entry():
    entry = join_waitlist(10, 3)
    leave_waitlist(entry.id, 10)
    assert entry.id not in WAITLIST
