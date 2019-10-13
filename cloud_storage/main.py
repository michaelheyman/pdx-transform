from cloud_storage import config
import json
import os
from cloud_storage.ratemyprofessors import RateMyProfessors
from google.cloud import storage


def get_bucket():
    storage_client = storage.Client()
    bucket_name = config.UNPROCESSED_BUCKET_NAME
    return storage_client.lookup_bucket(bucket_name)


def get_blobs_list():
    storage_client = storage.Client()
    bucket_name = config.UNPROCESSED_BUCKET_NAME
    return list(storage_client.list_blobs(bucket_name))


def get_latest_blob():
    bucket = get_bucket()

    if bucket is None:
        print("Bucket does not exist. Exiting program.")
        return None

    blobs = get_blobs_list()
    print(f"blobs {blobs}")
    latest_blob = max(blobs, key=lambda x: x["name"], default=None)

    return latest_blob


def get_instructors(contents):
    """ Extract a set of the instructors from the JSON bucket contents

    Parameters:
        contents (Dictionary): The dictionary representing the JSON contents
                               of the bucket
    
    Return:
        Set: A set of the instructors found in contents, with 'TBD' as the
             name of missing instructors
    Example:
    { Alice, Bob }
    """
    return set([x.get("instructor", "TBD") for x in contents])


def load_local_blob():
    """ Loads the contents of a JSON file used for local testing

    Returns:
        Dictionary: A dictionary representation of the contents of the file
    """
    filename = os.path.join(os.path.dirname(__file__), "blob.json")
    with open(filename) as json_file:
        return json.loads(json_file.read())


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
            { 
                instructorName: {
                    "fullName": String,
                    "firstName": String,
                    "lastName": String,
                    "rating": Float,
                    "rmpId": Integer,
                },
                instructorName: {
                    "fullName": "TBD"   // if the instructor doesn't exist
                }
            }
    """
    assert isinstance(instructors, set)
    rated = {}

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
            print(f"RateMyProfessors found no record of instructor '{instructor}'")
            rated[instructor] = {"fullName": instructor}

    print(rated)
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
    for course in contents:
        instructor_name = course["instructor"]
        if instructor_name in rated_instructors.keys():
            course["instructor"] = rated_instructors[instructor_name]

    return contents


if __name__ == "__main__":
    latest_blob = get_latest_blob()
    contents = latest_blob.download_as_string()
    try:
        contents_json = json.loads(contents)
        # contents_json = load_local_blob()
    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        exit()

    instructors = get_instructors(contents_json)
    print(instructors)
    rated_instructors = rate_instructors(instructors)

    updated_contents = inject_rated_instructors(contents_json, rated_instructors)
