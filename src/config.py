"""Static configuration: URLs, slot priorities, and CSS selectors.

Selectors below were discovered by running `scripts/discover_selectors.py`
against the live PolyU booking system on 2026-05-09. If the UI changes,
re-run discovery, inspect `artifacts/*.html`, and update the values here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Callable

_HOST = "https://www40.polyu.edu.hk"


@dataclass(frozen=True)
class Site:
    """One PolyU booking deployment. Staff and students use different J2EE
    context roots on the same host (`starspossfbns` vs `starspossfbstud`);
    every endpoint below hangs off `/<base_path>/secure/ui_make_book/`."""
    base_path: str

    @property
    def _prefix(self) -> str:
        return f"{_HOST}/{self.base_path}/secure/ui_make_book/"

    @property
    def login_url(self) -> str:
        return self._prefix + "make_book.do"

    @property
    def make_book_url(self) -> str:
        return self._prefix + "make_book.do"

    @property
    def make_book_submit_url(self) -> str:
        return self._prefix + "make_book_submit.do"

    @property
    def make_book_result_url(self) -> str:
        return self._prefix + "make_book_result.do"

    @property
    def timetable_url(self) -> str:
        return self._prefix + "timetable.json"


STAFF_SITE = Site("starspossfbns")
STUDENT_SITE = Site("starspossfbstud")

# Legacy aliases (staff site). Kept for scripts/ and tests; new code should
# take a Site explicitly.
LOGIN_URL = STAFF_SITE.login_url
SUBMIT_URL = STAFF_SITE.make_book_submit_url

# --- Tennis activity HTTP-API constants (derived from artifacts/http_trace.json) ---
# These are the form-field values PolyU's booking POSTs require for the Tennis
# activity. They are stable across runs — captured from a real booking and
# unchanged for the lifetime of PolyU's current booking system. Re-confirm by
# running scripts/capture_http.py if a booking starts failing with 4xx/5xx.

TIMETABLE_URL = STAFF_SITE.timetable_url
MAKE_BOOK_URL = STAFF_SITE.make_book_url
MAKE_BOOK_SUBMIT_URL = STAFF_SITE.make_book_submit_url
MAKE_BOOK_RESULT_URL = STAFF_SITE.make_book_result_url

TENNIS_DATA_SET_ID = 18
TENNIS_ACTV_ID = 10
TENNIS_CTR_ID = 1
TENNIS_CENTER_NAME = "Shaw Sports Complex"
TENNIS_FACILITIES = {
    10: "Tennis Court No. 1",
    11: "Tennis Court No. 2",
}

# Try in this order. Stop after first successful booking.
SLOT_PRIORITY: tuple[tuple[time, time], ...] = (
    (time(18, 30), time(19, 30)),
    (time(19, 30), time(20, 30)),
)

# Tuesdays are a rest day — no court is booked at all (owner's preference),
# so the booker short-circuits to a no-op success when target_date is Tuesday.
_REST_WEEKDAYS: frozenset[int] = frozenset({1})  # Mon=0, Tue=1, ...

# On weekends, also try the late-evening slots as lower-priority fallbacks
# (appended after SLOT_PRIORITY, so 18:30/19:30 still win by rank).
_WEEKEND_WEEKDAYS: frozenset[int] = frozenset({5, 6})  # Sat=5, Sun=6
_WEEKEND_EXTRA_SLOTS: tuple[tuple[time, time], ...] = (
    (time(20, 30), time(21, 30)),
    (time(21, 30), time(22, 30)),
)


def slot_priority_for(target_date: date) -> tuple[tuple[time, time], ...]:
    """Return SLOT_PRIORITY with weekday-specific adjustments applied.

    Returns an empty tuple on rest weekdays so the booker can skip the run;
    appends _WEEKEND_EXTRA_SLOTS on Saturdays and Sundays.
    """
    if target_date.weekday() in _REST_WEEKDAYS:
        return ()
    if target_date.weekday() in _WEEKEND_WEEKDAYS:
        return SLOT_PRIORITY + _WEEKEND_EXTRA_SLOTS
    return SLOT_PRIORITY


# --- Student account: one-off dual booking on specific dates ---
# The student account books alongside the staff account ONLY when the target
# date is in STUDENT_TARGET_DATES; every other day it is skipped entirely.
# Once the dates have passed, the set can simply be emptied.
STUDENT_TARGET_DATES: frozenset[date] = frozenset({
    date(2026, 9, 18),
    date(2026, 9, 19),
    date(2026, 9, 20),
})
STUDENT_SLOT_PRIORITY: tuple[tuple[time, time], ...] = (
    (time(18, 30), time(19, 30)),
    (time(19, 30), time(20, 30)),
    (time(20, 30), time(21, 30)),
    (time(21, 30), time(22, 30)),
)


def student_slot_priority_for(target_date: date) -> tuple[tuple[time, time], ...]:
    if target_date in STUDENT_TARGET_DATES:
        return STUDENT_SLOT_PRIORITY
    return ()


@dataclass(frozen=True)
class Account:
    """A login identity plus the site it lives on and its slot rule.

    `slot_priority(target_date)` returning an empty tuple means the account
    sits this run out.
    """
    name: str
    site: Site
    username_env: str
    password_env: str
    slot_priority: Callable[[date], tuple[tuple[time, time], ...]]


STAFF_ACCOUNT = Account(
    name="staff",
    site=STAFF_SITE,
    username_env="POLYU_USERNAME",
    password_env="POLYU_PASSWORD",
    slot_priority=slot_priority_for,
)
STUDENT_ACCOUNT = Account(
    name="student",
    site=STUDENT_SITE,
    username_env="POLYU_STUDENT_USERNAME",
    password_env="POLYU_STUDENT_PASSWORD",
    slot_priority=student_slot_priority_for,
)
# Order matters only for logging; the accounts book concurrently.
ACCOUNTS: tuple[Account, ...] = (STAFF_ACCOUNT, STUDENT_ACCOUNT)

TRIGGER_TIME_HKT = time(8, 30, 0)


class _Pending:
    """Sentinel marking a selector that has not yet been filled in."""

    def __repr__(self) -> str:  # pragma: no cover - debug aid only
        return "PENDING_DISCOVERY"

    def __bool__(self) -> bool:
        return False


PENDING_DISCOVERY = _Pending()


def require(value: object, name: str) -> str:
    if isinstance(value, _Pending) or value is None:
        raise RuntimeError(
            f"Selector {name!r} is not configured. "
            f"Run scripts/discover_selectors.py and fill it into src/config.py."
        )
    assert isinstance(value, str)
    return value


@dataclass(frozen=True)
class Selectors:
    # Login form (POSS j_security_check)
    login_username: str | _Pending = 'input[name="j_username"]'
    login_password: str | _Pending = 'input[name="j_password"]'
    login_submit: str | _Pending = 'button[type="submit"][name="buttonAction"]'

SELECTORS = Selectors()
