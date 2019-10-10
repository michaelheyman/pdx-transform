import os


def map_level(level):
    """ Maps logging level strings to logging level codes

    Parameters:
        level (String): The level string to be mapped.
    
    Returns:
        Integer: Number that matches the logging level.
    """
    return {"critical": 50, "error": 40, "warning": 30, "info": 20, "debug": 10}.get(
        level, 10
    )


BUCKET_NAME = os.environ.get("BUCKET_NAME", "processed-data")
LOGGING_LEVEL = map_level(os.environ.get("LOGGING_LEVEL", "debug"))
