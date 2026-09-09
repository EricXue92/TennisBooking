"""Tests for weekday-specific slot priority rules in src/config.py."""
from datetime import date, time

from src.config import SLOT_PRIORITY, slot_priority_for


def test_weekday_returns_base_priority():
    # 2026-09-04 is a Friday.
    assert slot_priority_for(date(2026, 9, 4)) == SLOT_PRIORITY


def test_tuesday_is_rest_day():
    # 2026-09-01 is a Tuesday.
    assert slot_priority_for(date(2026, 9, 1)) == ()


def test_saturday_appends_late_evening_slots():
    # 2026-09-05 is a Saturday: base slots first, then 20:30 and 21:30
    # as lower-priority fallbacks.
    assert slot_priority_for(date(2026, 9, 5)) == SLOT_PRIORITY + (
        (time(20, 30), time(21, 30)),
        (time(21, 30), time(22, 30)),
    )


def test_sunday_appends_late_evening_slots():
    # 2026-09-06 is a Sunday.
    assert slot_priority_for(date(2026, 9, 6)) == SLOT_PRIORITY + (
        (time(20, 30), time(21, 30)),
        (time(21, 30), time(22, 30)),
    )


# --- Site / Account (dual-account booking) ---

def test_site_derives_urls_from_base_path():
    from src.config import Site

    site = Site("starspossfbstud")
    prefix = "https://www40.polyu.edu.hk/starspossfbstud/secure/ui_make_book/"
    assert site.login_url == prefix + "make_book.do"
    assert site.make_book_url == prefix + "make_book.do"
    assert site.make_book_submit_url == prefix + "make_book_submit.do"
    assert site.make_book_result_url == prefix + "make_book_result.do"
    assert site.timetable_url == prefix + "timetable.json"


def test_staff_site_matches_legacy_url_constants():
    from src.config import LOGIN_URL, MAKE_BOOK_SUBMIT_URL, STAFF_SITE

    assert STAFF_SITE.base_path == "starspossfbns"
    assert STAFF_SITE.login_url == LOGIN_URL
    assert STAFF_SITE.make_book_submit_url == MAKE_BOOK_SUBMIT_URL


def test_student_slots_only_on_configured_dates():
    from src.config import student_slot_priority_for

    # 2026-09-18 (Fri), 19 (Sat), 20 (Sun) are the only configured dates.
    expected = (
        (time(18, 30), time(19, 30)),
        (time(19, 30), time(20, 30)),
        (time(20, 30), time(21, 30)),
        (time(21, 30), time(22, 30)),
    )
    for d in (date(2026, 9, 18), date(2026, 9, 19), date(2026, 9, 20)):
        assert student_slot_priority_for(d) == expected
    assert student_slot_priority_for(date(2026, 9, 17)) == ()
    assert student_slot_priority_for(date(2026, 9, 21)) == ()


def test_accounts_staff_first_then_student():
    from src.config import ACCOUNTS, STAFF_SITE, STUDENT_SITE, slot_priority_for, student_slot_priority_for

    staff, student = ACCOUNTS
    assert (staff.name, staff.site, staff.username_env, staff.password_env) == (
        "staff", STAFF_SITE, "POLYU_USERNAME", "POLYU_PASSWORD")
    assert staff.slot_priority is slot_priority_for
    assert (student.name, student.site, student.username_env, student.password_env) == (
        "student", STUDENT_SITE, "POLYU_STUDENT_USERNAME", "POLYU_STUDENT_PASSWORD")
    assert student.slot_priority is student_slot_priority_for
    assert STUDENT_SITE.base_path == "starspossfbstud"
