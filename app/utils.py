from datetime import datetime


def get_current_timestamp():
    return datetime.now().timestamp()


def generate_filename():
    """Generates a filename to be put into a Storage bucket.

    :return: A filename in the format epoc.json
    """
    date_format = "%Y%m%d%H%M%S"
    timestamp = get_current_timestamp()
    date = datetime.fromtimestamp(timestamp).strftime(date_format)

    return f"{date}.json"
