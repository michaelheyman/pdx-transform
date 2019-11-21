import os


def map_level(level):
    """Maps logging level strings to logging level codes

    :param level: The level string to be mapped.
    :return: Number that matches the logging level.
    """
    return {"critical": 50, "error": 40, "warning": 30, "info": 20, "debug": 10}.get(
        level, 10
    )


LOGGING_LEVEL = map_level(os.environ.get("LOGGING_LEVEL", "debug"))
PROCESSED_BUCKET_NAME = os.environ.get("BUCKET_NAME", "pdx-schedule-processed-data")
UNPROCESSED_BUCKET_NAME = os.environ.get("BUCKET_NAME", "pdx-schedule-unprocessed-data")
