from assets import *
import datetime
import pytz

def utc():
    return datetime.datetime.now(datetime.timezone.utc)

# noinspection PyBroadException
def convert_time(_time) -> str:
    """
    Convert time into a years, hours, minute, seconds thing.
    """
    # much better than the original one lol
    # man I suck at docstrings lol
    try:
        times = {}
        return_times = []
        time_dict = {
            "years": 31536000,
            "months": 2628000,
            "weeks": 604800,
            "days": 86400,
            "hours": 3600,
            "minutes": 60,
            "seconds": 1
        }
        for key, value in time_dict.items():
            times[str(key)] = {}
            times[str(key)]["value"] = int(_time // value)
            _time %= value

        for key, value in times.items():
            if not value['value']:
                continue

            return_times.append("{0} {1}".format(value['value'], key))

        return ' '.join(return_times) if return_times else '0 seconds'

    except Exception:
        return 'indefinitely'

def general_convert_time(_time, to_places=2) -> str:
    """
    Used to get a more readable time conversion
    """
    times = convert_time(_time).split(' ')
    return ' '.join(times[:to_places]) + (', ' if times[to_places:(to_places * 2)] else '') \
           + ' '.join(times[to_places:(to_places * 2)])

def convert_to_timestamp(_time: datetime.datetime) -> str:
    """
    Convert a regular datetime object into something resembling a discord.Embed footer.
    """
    _time = _time.replace(tzinfo=datetime.timezone.utc)

    current = utc()
    day, _day = int(current.strftime("%d")), int(_time.strftime("%d"))
    month, _month = int(current.strftime("%m")), int(_time.strftime("%m"))
    year, _year = int(current.strftime("%Y")), int(_time.strftime("%Y"))
    if month == _month and year == _year:
        est_time = _time.astimezone(pytz.timezone('America/New_York'))

        fmt = '%I:%M %p'
        if day == _day:
            return est_time.strftime(f"Today at {fmt}")

        elif day - 1 == _day:
            return est_time.strftime(f"Yesterday at {fmt}")

    return _time.strftime("%d/%m/%y")