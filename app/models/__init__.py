from datetime import datetime

import pytz

from app.configs import CONFIG


def current_timestamp():
    return datetime.utcnow().replace(tzinfo=pytz.utc, microsecond=0).astimezone(pytz.timezone(CONFIG.TIMEZONE))
