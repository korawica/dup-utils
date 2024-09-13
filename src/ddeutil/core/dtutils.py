# ------------------------------------------------------------------------------
# Copyright (c) 2022 Korawich Anuttra. All rights reserved.
# Licensed under the MIT License. See LICENSE in the project root for
# license information.
# ------------------------------------------------------------------------------
from __future__ import annotations

import calendar
import enum
from datetime import datetime, timedelta
from typing import (
    Literal,
    Optional,
    Union,
)
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from . import first

LOCAL_TZ: ZoneInfo = ZoneInfo("UTC")

DatetimeMode = Literal[
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "microsecond",
]
DATETIME_SET: tuple[str, ...] = (
    "year",
    "month",
    "day",
    "hour",
    "minute",
    "second",
    "microsecond",
)


def get_datetime_replace(
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> dict[str, tuple]:
    return {
        "year": (1990, 9999),
        "month": (1, 12),
        "day": (
            1,
            (calendar.monthrange(year, month)[1] if year and month else 31),
        ),
        "hour": (0, 23),
        "minute": (0, 59),
        "second": (0, 59),
        "microsecond": (0, 999999),
    }


class DatetimeDim(enum.IntEnum):
    """Datetime dimension enumerations"""

    MICROSECOND = 0
    SECOND = 1
    MINUTE = 2
    HOUR = 3
    DAY = 4
    MONTH = 5
    YEAR = 6


def now(_tz: Optional[str] = None):
    _tz: ZoneInfo = ZoneInfo(_tz) if _tz and isinstance(_tz, str) else LOCAL_TZ
    return datetime.now(_tz)


def get_date(
    fmt: str,
    *,
    _tz: Optional[str] = None,
) -> Union[datetime, datetime.date, str]:
    """
    Examples:
        >>> get_date(fmt='%Y-%m-%d')
        '2023-01-01'
    """
    _datetime: datetime = now(_tz)
    if fmt == "datetime":
        return _datetime
    elif fmt == "date":
        return _datetime.date()
    return _datetime.strftime(fmt)


def replace_date(
    dt: datetime,
    mode: DatetimeMode,
    reverse: bool = False,
) -> datetime:
    """
    Examples:
        >>> replace_date(datetime(2023, 1, 31, 13, 2, 47), mode='day')
        datetime.datetime(2023, 1, 31, 0, 0)
        >>> replace_date(datetime(2023, 1, 31, 13, 2, 47), mode='year')
        datetime.datetime(2023, 1, 1, 0, 0)
    """
    assert mode in (
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "microsecond",
    )
    replace_mapping: dict[str, tuple] = get_datetime_replace(dt.year, dt.month)
    return dt.replace(
        **{
            _.name.lower(): replace_mapping[_.name.lower()][int(reverse)]
            for _ in DatetimeDim
            if _ < DatetimeDim[mode.upper()]
        }
    )


def next_date(
    dt: datetime,
    mode: DatetimeMode,
    *,
    reverse: bool = False,
    next_value: int = 1,
) -> datetime:
    """Return the next date with specific unit mode.

    Examples:
        >>> next_date(datetime(2023, 1, 31, 0, 0, 0), mode='day')
        datetime.datetime(2023, 2, 1, 0, 0)
        >>> next_date(datetime(2023, 1, 31, 0, 0, 0), mode='month')
        datetime.datetime(2023, 2, 28, 0, 0)
        >>> next_date(datetime(2023, 1, 31, 0, 0, 0), mode='hour')
        datetime.datetime(2023, 1, 31, 1, 0)
        >>> next_date(datetime(2023, 1, 31, 0, 0, 0), mode='year')
        datetime.datetime(2024, 1, 31, 0, 0)
    """
    assert mode in (
        "year",
        "month",
        "day",
        "hour",
        "minute",
        "second",
        "microsecond",
    )
    assert -1000 <= next_value <= 1000
    return dt + relativedelta(
        **{f"{mode}s": (-next_value if reverse else next_value)}
    )


def closest_quarter(dt: datetime) -> datetime:
    """Return closest quarter datetime.

    :param dt: A datetime value that want to convert.
    :rtype: datetime

    Examples:
        >>> closest_quarter(datetime(2024, 9, 25))
        datetime.datetime(2024, 9, 30, 0, 0)
        >>> closest_quarter(datetime(2024, 2, 13))
        datetime.datetime(2023, 12, 31, 0, 0)
    """
    # NOTE: candidate list, nicely enough none of these are in February, so
    #   the month lengths are fixed
    candidates: list[datetime] = [
        datetime(dt.year - 1, 12, 31, 0),
        datetime(dt.year, 3, 31, 0),
        datetime(dt.year, 6, 30, 0),
        datetime(dt.year, 9, 30, 0),
        datetime(dt.year, 12, 31, 0),
    ]
    # NOTE: take the minimum according to the absolute distance to the target
    #   date.
    return min(candidates, key=lambda d: abs(dt - d))


def last_dom(dt: datetime) -> datetime:
    """
    :param dt:
    :rtype: datetime

    Examples:
        >>> last_dom(datetime(2024, 2, 29))
        datetime.datetime(2024, 2, 29, 0, 0)
        >>> last_dom(datetime(2024, 1, 31) + relativedelta(months=1))
        datetime.datetime(2024, 2, 29, 0, 0)
        >>> last_dom(datetime(2024, 2, 29) + relativedelta(months=1))
        datetime.datetime(2024, 3, 31, 0, 0)
    """
    # The day 28 exists in every month. 4 days later, it's always next month
    next_month = dt.replace(day=28) + timedelta(days=4)
    # subtracting the number of the current day brings us back one month
    return next_month - timedelta(days=next_month.day)


def last_doq(dt: datetime) -> datetime:
    """
    :param dt:
    :return:

    Examples:
        >>> last_doq(datetime(2024, 2, 16))
        datetime.datetime(2024, 3, 31, 0, 0)
        >>> last_doq(datetime(2024, 12, 31))
        datetime.datetime(2024, 12, 31, 0, 0)
        >>> last_doq(datetime(2024, 8, 1))
        datetime.datetime(2024, 9, 30, 0, 0)
        >>> last_doq(datetime(2024, 9, 30))
        datetime.datetime(2024, 9, 30, 0, 0)
    """
    candidates: list[datetime] = [
        datetime(dt.year - 1, 12, 31, 0),
        datetime(dt.year, 3, 31, 0),
        datetime(dt.year, 6, 30, 0),
        datetime(dt.year, 9, 30, 0),
        datetime(dt.year, 12, 31, 0),
    ]
    return first(candidates, condition=lambda x: x >= dt)


def next_date_with_freq(
    dt: datetime, freq: str, prev: bool = False
) -> datetime:
    """
    :param dt:
    :param freq:
    :param prev:
    :rtype: datetime

    Examples:
        >>> next_date_with_freq(datetime(2024, 1, 3), freq='D')
        datetime.datetime(2024, 1, 4, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 3), freq='D', prev=True)
        datetime.datetime(2024, 1, 2, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 3), freq='W')
        datetime.datetime(2024, 1, 10, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 3), freq='W', prev=True)
        datetime.datetime(2023, 12, 27, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 3), freq='M')
        datetime.datetime(2024, 2, 3, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 31), freq='M')
        datetime.datetime(2024, 2, 29, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 17), freq='Q')
        datetime.datetime(2024, 4, 17, 0, 0)
        >>> next_date_with_freq(datetime(2024, 1, 31), freq='Q')
        datetime.datetime(2024, 4, 30, 0, 0)
        >>> next_date_with_freq(datetime(2025, 12, 31), freq='Q')
        datetime.datetime(2026, 3, 31, 0, 0)
        >>> next_date_with_freq(datetime(2024, 5, 21), freq='Y')
        datetime.datetime(2025, 5, 21, 0, 0)
        >>> next_date_with_freq(datetime(2024, 5, 31), freq='Y')
        datetime.datetime(2025, 5, 31, 0, 0)
        >>> next_date_with_freq(datetime(2024, 5, 31), freq='Y', prev=True)
        datetime.datetime(2023, 5, 31, 0, 0)
    """
    assert freq in ("D", "W", "M", "Q", "Y")
    operator: int = -1 if prev else 1
    if freq == "D":
        return dt + timedelta(days=1 * operator)
    elif freq == "W":
        return dt + timedelta(days=7 * operator)
    elif freq == "M":
        if dt == last_dom(dt):
            return last_dom(dt + relativedelta(months=1 * operator))
        return dt + relativedelta(months=1 * operator)
    elif freq == "Q":
        if dt == last_dom(dt):
            return last_dom(dt + relativedelta(months=3 * operator))
        return dt + relativedelta(months=3 * operator)
    elif freq == "Y":
        if dt == last_dom(dt):
            return last_dom(dt + relativedelta(years=1 * operator))
        return dt + relativedelta(years=1 * operator)
    raise ValueError(f"The date logic does not support for frequency: {freq}")


def calc_data_date_with_freq(dt: datetime, freq: str) -> datetime:
    """
    :param dt:
    :param freq:
    :rtype: datetime

        Examples:
            >>> calc_data_date_with_freq(datetime(2024, 1, 13), freq='D')
            datetime.datetime(2024, 1, 13, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 1, 3), freq='W')
            datetime.datetime(2024, 1, 3, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 1, 3), freq='M')
            datetime.datetime(2023, 12, 31, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 1, 31), freq='M')
            datetime.datetime(2024, 1, 31, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 1, 31), freq='Q')
            datetime.datetime(2023, 12, 31, 0, 0)
            >>> calc_data_date_with_freq(datetime(2025, 12, 31), freq='Q')
            datetime.datetime(2025, 12, 31, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 12, 31), freq='Y')
            datetime.datetime(2024, 12, 31, 0, 0)
            >>> calc_data_date_with_freq(datetime(2024, 5, 31), freq='Y')
            datetime.datetime(2023, 12, 31, 0, 0)
    """
    assert freq in ("D", "W", "M", "Q", "Y")
    if freq == "D" or freq == "W":
        return dt
    elif freq == "M":
        if dt != last_dom(dt):
            return last_dom(dt) - relativedelta(months=1)
        return dt
    elif freq == "Q":
        if dt != last_doq(dt):
            return last_dom(last_doq(dt) - relativedelta(months=3))
        return dt
    elif freq == "Y":
        if dt != dt.replace(month=12, day=31):
            return dt.replace(month=12, day=31) - relativedelta(years=1)
        return dt
    raise ValueError(
        f"The calculate date logic does not support for frequency: {freq}"
    )
