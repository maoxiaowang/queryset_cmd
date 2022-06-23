import datetime
import re
import typing

import pytz
from django.utils import timezone

STANDARD_FORMAT = '%Y-%m-%d %H:%M:%S'
ISO_FORMAT = '%Y-%m-%dT%H:%M:%SZ'


def str_to_datetime(date_string, fmt=STANDARD_FORMAT) -> datetime.datetime:
    """
    Support style:
    2018-12-07T06:24:24.000000
    2018-12-07T06:24:24Z
    2018-12-07 06:24:24
    2018-12-7
    ...
    """
    ds = re.findall(r'^(\d{4}-\d{2}-\d{2})[T\s]?(\d{2}:\d{2}:\d{2})?.*$', date_string)
    if not ds:
        raise ValueError('Invalid datetime string: %s' % date_string)
    year_month_day, hour_minute_second = ds[0]
    if not hour_minute_second:
        year, month, day = year_month_day.split('-')
        return datetime.datetime(year=int(year), month=int(month), day=int(day))
    else:
        date_string = '%s %s' % (year_month_day, hour_minute_second)
        return datetime.datetime.strptime(date_string, fmt)


def to_aware_datetime(dt: typing.Union[str, datetime.datetime, datetime.date], tz=None):
    """
    Make an naive datetime using a given timezone(tz)

    Notice: tz if the timezone of dt, make sure they are matched
    """
    if dt is None:
        return
    if tz is None:
        tz = timezone.get_current_timezone()
    else:
        if isinstance(tz, str):
            tz = pytz.timezone(tz)
    if isinstance(dt, (datetime.datetime, datetime.date)):
        if timezone.is_aware(dt):
            return dt
        else:
            # Asia/Shanghai, same to settings
            return timezone.make_aware(dt, timezone=tz)
    elif isinstance(dt, str):
        dt = str_to_datetime(dt)
        aware = timezone.make_aware(dt, timezone=tz)
        return aware
    raise ValueError
