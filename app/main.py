import json
from collections import OrderedDict

from app import storage
from app.logger import logger
from app.ratemyprofessors import RateMyProfessors


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

            if instructor_name not in rated_instructors.keys():
                course["instructor"] = {"fullName": instructor_name}
            else:
                course["instructor"] = rated_instructors[instructor_name]

    return contents


def run():
    latest_blob = storage.get_latest_blob()
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
    storage.upload_to_bucket(processed_data)
