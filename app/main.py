import json
from collections import OrderedDict
from datetime import datetime

from google.cloud import storage

from app import config
from app.logger import logger
from app.ratemyprofessors import RateMyProfessors


def get_latest_blob():
    """ Gets the latest blob found in the unprocessed bucket

    Return:
        Blob: A blob representing the object in the bucket
    """
    storage_client = storage.Client()
    bucket_name = config.UNPROCESSED_BUCKET_NAME
    bucket = storage_client.lookup_bucket(bucket_name)

    if bucket is None:
        logger.critical("Bucket does not exist. Exiting program.")
        return None

    blobs = list(storage_client.list_blobs(bucket_name))
    logger.debug(f"blobs {blobs}")
    latest_blob = max(blobs, key=lambda x: x.name, default=None)

    return latest_blob


def get_instructors(contents):
    """ Extract a set of the instructors from the JSON bucket contents

    Parameters:
        contents (Dictionary): The dictionary representing the JSON contents
                               of the bucket

    Return:
        Set: A set of the instructors found in contents, with 'TBD' as the
             name of missing instructors
    """
    instructors = set()
    for term in contents:
        for discipline in term:
            instructors.add(discipline.get("instructor", "TBD"))

    return instructors


def get_instructor(instructor):
    """ This is only here until I can figure out how to
    mock this call in the unit tests
    """
    return RateMyProfessors.get_instructor(instructor)


def rate_instructors(instructors):
    """ Rate instructors according to their RateMyProfessor information

    Parameters:
        instructors (Set): Set of instructors to rate

    Returns:
        List: List of dictionaries of instructor information
    """
    assert isinstance(instructors, set)
    rated = OrderedDict()

    for instructor in instructors:
        try:
            first_name, last_name, rating, rmp_id = get_instructor(instructor)
            rated[instructor] = {
                "fullName": instructor,
                "firstName": first_name,
                "lastName": last_name,
                "rating": rating,
                "rmpId": rmp_id,
            }
        except ValueError:
            logger.info(
                f"RateMyProfessors found no record of instructor '{instructor}'"
            )
            rated[instructor] = {"fullName": instructor}

    return rated


def inject_rated_instructors(contents, rated_instructors):
    """ Add rated instructors back to the instructor dictionary

    Parameters:
        contents (List):          List of dictionaries representing instructors
        rated_instructors (Dict): Dictionary of instructors and their information

    Returns:
        List: The `contents` with the instructors field replaced with the
              instructor in `instructors`
    """
    assert isinstance(contents, list)
    for term in contents:
        for course in term:
            instructor_name = course["instructor"]

            if instructor_name in rated_instructors.keys():
                course["instructor"] = rated_instructors[instructor_name]

    return contents


def get_current_timestamp():
    return datetime.now().timestamp()


def generate_filename():
    """ Generates a filename to be put into a Storage bucket.

    Returns:
        String: A filename in the format epoc.json
        Example:
            137281912.json
    """
    date_format = "%Y%m%d%H%M%S"
    timestamp = get_current_timestamp()
    date = datetime.fromtimestamp(timestamp).strftime(date_format)

    return f"{date}.json"


def upload_to_bucket(contents):
    """
    Uploads contents to Cloud Storage bucket.

    Parameters:
        contents (Object): The contents to put in the bucket (JSON)
    """
    assert isinstance(contents, (dict, list))
    storage_client = storage.Client()
    bucket_name = config.PROCESSED_BUCKET_NAME
    bucket = storage_client.lookup_bucket(bucket_name)

    if bucket is None:
        bucket = storage_client.create_bucket(bucket_name)
        logger.info("Bucket {} created.".format(bucket.name))
    else:
        logger.info("Bucket {} already exists.".format(bucket.name))

    filename = generate_filename()

    lambda_filename = write_lambda_file(filename, contents)

    blob = bucket.blob(filename)
    # uploads the file in the cloud function to cloud storage
    blob.upload_from_filename(lambda_filename)

    logger.info("File {} uploaded to {}.".format(filename, bucket_name))


def write_lambda_file(filename, contents):
    """ Saves content to lambda filename.

    Saves contents to a filename and writes them to a /tmp/ directory in the Cloud Function.
    Cloud Functions only have write access to their /tmp/ directory.

    Parameters:
        filename (String): The filename to write the data to.
        contents (Object): The contents to put in the bucket.
    """
    lambda_filename = f"/tmp/{filename}"

    with open(lambda_filename, "w") as outfile:
        json.dump(contents, outfile)

    logger.debug(f"file: {outfile}")

    return lambda_filename


def run():
    latest_blob = get_latest_blob()
    contents = latest_blob.download_as_string()
    try:
        contents_json = json.loads(contents)
    except json.decoder.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}")
        exit()

    instructors = get_instructors(contents_json)
    logger.info(f"Found {len(instructors)} unique instructors")
    rated_instructors = rate_instructors(instructors)

    processed_data = inject_rated_instructors(contents_json, rated_instructors)
    upload_to_bucket(processed_data)
