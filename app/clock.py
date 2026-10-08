"""All 'today' logic uses India time so a server running in UTC does not roll the day over at 5:30 am."""
from datetime import date, datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))


def now() -> datetime:
    return datetime.now(IST)


def today() -> date:
    return now().date()


def parse(d: str | None) -> date | None:
    return date.fromisoformat(d) if d else None


def season_of(d: date | None) -> str:
    """Indian cropping seasons by planting month: kharif Jun-Oct, rabi Nov-Feb, summer Mar-May."""
    if not d:
        return ""
    return "kharif" if 6 <= d.month <= 10 else "rabi" if d.month in (11, 12, 1, 2) else "summer"
