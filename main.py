import config
import json
from google.cloud import storage

storage_client = storage.Client()


def get_latest_blob():
    bucket_name = config.BUCKET_NAME
    bucket = storage_client.lookup_bucket(bucket_name)

    if bucket is None:
        print("Bucket does not exist. Exiting program.")
        return None

    blobs = list(storage_client.list_blobs(config.BUCKET_NAME))
    print(f"blobs {blobs}")
    latest_blob = max(blobs, key=lambda x: x.name)

    return latest_blob


def get_instructors(contents):
    return set(map(lambda x: x.get("instructor", "TBD"), contents))


if __name__ == "__main__":
    latest_blob = get_latest_blob()
    contents = latest_blob.download_as_string()
    try:
        contents_json = json.loads(contents)
        instructors = get_instructors(contents_json)
        print(instructors)
    except json.decoder.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        exit()
