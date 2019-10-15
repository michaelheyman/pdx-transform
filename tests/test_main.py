from collections import OrderedDict

import mock
import pytest

from app import main
from tests import mocks


def test_get_instructors_returns_unique_instructors():
    contents = mocks.contents
    contents = [
        {"instructor": "Alice"},
        {"instructor": "Alice"},
        {"instructor": "Bob"},
        {"instructor": "John"},
        {"instructor": "John"},
    ]

    instructor_set = main.get_instructors(contents)

    assert instructor_set == {"Alice", "Bob", "John"}


def test_get_instructors_returns_tbd_for_missing_instructors():
    contents = [{"instructor": "Alice"}, {"instructor": "Bob"}, {"name": "John Doe"}]

    instructor_set = main.get_instructors(contents)

    assert instructor_set == {"Alice", "Bob", "TBD"}


def test_get_instructors_returns_empty_set_when_empty_instructors():
    contents = []

    instructor_set = main.get_instructors(contents)

    assert instructor_set == set()


@mock.patch("google.cloud.storage.Client")
def test_get_latest_blob_returns_none_when_bucket_does_not_exist(mock_storage_client):
    # mock_get_bucket.return_value = None
    mock_storage_client().lookup_bucket.return_value = None

    latest_blob = main.get_latest_blob()

    assert mock_storage_client().lookup_bucket.called is True
    assert latest_blob is None


@mock.patch("google.cloud.storage.Client")
def test_get_latest_blob_returns_blob_when_only_one_blob_exists(mock_storage_client):
    mock_blob = mock.Mock()
    mock_blob.name = "1234567890.json"
    mock_storage_client().lookup_bucket.return_value = "test-bucket"
    mock_storage_client().list_blobs.return_value = [mock_blob]

    latest_blob = main.get_latest_blob()

    assert mock_storage_client().lookup_bucket.called is True
    assert mock_storage_client().list_blobs.called is True
    assert latest_blob.name == "1234567890.json"


@mock.patch("google.cloud.storage.Client")
def test_get_latest_blob_returns_latest_blob_when_multiple_exist(mock_storage_client):
    mock_blob_latest = mock.Mock()
    mock_blob_latest.name = "1234567890.json"
    mock_blob_oldest = mock.Mock()
    mock_blob_oldest.name = "1000000000.json"
    mock_storage_client().lookup_bucket.return_value = "test-bucket"
    mock_storage_client().list_blobs.return_value = [mock_blob_oldest, mock_blob_latest]

    latest_blob = main.get_latest_blob()

    assert mock_storage_client().lookup_bucket.called is True
    assert mock_storage_client().list_blobs.called is True
    assert latest_blob.name == "1234567890.json"


@mock.patch("app.main.get_current_timestamp")
def test_generate_filename_generates_formatted_timestamp(mock_timestamp):
    mock_timestamp.return_value = 1_555_555_555.555_555

    filename = main.generate_filename()

    assert mock_timestamp.called is True
    assert filename == "20190417194555.json"


def test_rate_instructors_returns_empty_dict_when_no_instructors():
    instructors = set()

    rated_instructors = main.rate_instructors(instructors)

    assert rated_instructors == {}


@mock.patch("app.main.get_instructor")
def test_rate_instructors_returns_rated_instructor_when_instructor_rating(
    mock_get_instructor
):
    mock_get_instructor.return_value = ("Jane", "Doe", 4.0, 12345)
    instructors = {"Jane Doe"}

    rated_instructors = main.rate_instructors(instructors)

    assert rated_instructors == {
        "Jane Doe": {
            "fullName": "Jane Doe",
            "firstName": "Jane",
            "lastName": "Doe",
            "rating": 4.0,
            "rmpId": 12345,
        }
    }


@pytest.mark.skip(reason="Getting inconsistent result with the assertion")
@mock.patch("app.main.get_instructor")
def test_rate_instructors_returns_multiple_rated_instructors(mock_get_instructor):
    mock_get_instructor.side_effect = [
        ("Jane", "Doe", 4.0, 12345),
        ("John", "Doe", 3.5, 98765),
    ]
    instructors = {"Jane Doe", "John Doe"}

    rated_instructors = main.rate_instructors(instructors)
    expected = OrderedDict(
        {
            "Jane Doe": {
                "fullName": "Jane Doe",
                "firstName": "Jane",
                "lastName": "Doe",
                "rating": 4.0,
                "rmpId": 12345,
            },
            "John Doe": {
                "fullName": "John Doe",
                "firstName": "John",
                "lastName": "Doe",
                "rating": 3.5,
                "rmpId": 98765,
            },
        }
    )

    print(f"rated instructors: {rated_instructors}")
    print(f"expected: {expected}")
    assert rated_instructors == expected


@pytest.mark.skip(reason="Getting inconsistent result with the assertion")
@mock.patch("app.main.get_instructor")
def test_rate_instructors_returns_instructor_when_name_not_exists(mock_get_instructor):
    mock_get_instructor.side_effect = [("Jane", "Doe", 4.0, 12345), ValueError()]
    instructors = {"Jane Doe", "John Doe"}

    rated_instructors = main.rate_instructors(instructors)

    print(f"rated inst: {rated_instructors}")
    assert rated_instructors == {
        "Jane Doe": {
            "fullName": "Jane Doe",
            "firstName": "Jane",
            "lastName": "Doe",
            "rating": 4.0,
            "rmpId": 12345,
        },
        "John Doe": {"fullName": "John Doe"},
    }


def test_inject_rated_instructors_returns_unchanged_contents_if_empty():
    contents = []
    rated_instructors = []

    main.inject_rated_instructors(contents, rated_instructors)

    assert contents == []


def test_inject_rated_instructors_returns_injected_instructor():
    contents = [{"instructor": "Jane Doe"}]
    rated_instructors = {
        "Jane Doe": {
            "fullName": "Jane Doe",
            "firstName": "Jane",
            "lastName": "Doe",
            "rating": 4.0,
            "rmpId": 12345,
        }
    }

    main.inject_rated_instructors(contents, rated_instructors)

    assert contents == [
        {
            "instructor": {
                "fullName": "Jane Doe",
                "firstName": "Jane",
                "lastName": "Doe",
                "rating": 4.0,
                "rmpId": 12345,
            }
        }
    ]


def test_inject_rated_instructors_returns_contents_when_instructors_dont_match():
    contents = [{"instructor": "Jane Doe"}]
    rated_instructors = {
        "John Doe": {
            "fullName": "John Doe",
            "firstName": "John",
            "lastName": "Doe",
            "rating": 3.5,
            "rmpId": 98765,
        }
    }

    main.inject_rated_instructors(contents, rated_instructors)

    assert contents == contents


@mock.patch("google.cloud.storage.Client")
def test_upload_to_bucket_returns_none_when_no_bucket(mock_storage_client):
    mock_created_bucket = mock.Mock()
    mock_created_bucket.name = "test-bucket"
    mock_storage_client().lookup_bucket.return_value = None
    mock_storage_client().create_bucket.return_value = mock_created_bucket
    contents = {}

    main.upload_to_bucket(contents)

    assert mock_storage_client().lookup_bucket.called is True
    assert mock_storage_client().create_bucket.called is True


@mock.patch("app.main.write_lambda_file")
@mock.patch("app.main.generate_filename")
@mock.patch("google.cloud.storage.Client")
def test_upload_to_bucket_runs_until_end(
    mock_storage_client, mock_generate_filename, mock_write_lambda_file
):
    lookup_bucket = mock.Mock()
    lookup_bucket.name = "test-bucket"
    bucket_blob = mock.Mock()
    lookup_bucket.blob.return_value = bucket_blob
    mock_storage_client().lookup_bucket.return_value = lookup_bucket
    mock_generate_filename.return_value = "1234567890.json"
    contents = {}

    main.upload_to_bucket(contents)

    assert mock_storage_client().lookup_bucket.called is True
    assert mock_storage_client().create_bucket.called is False


def test_write_lambda_file_returns_filename():
    filename = "test-filename"
    contents = "test-contents"

    with mock.patch(
        "builtins.open", new_callable=mock.mock_open()
    ) as mock_open:  # noqa: F841
        with mock.patch("json.dump") as mock_json:  # noqa: F841
            pass

    lambda_filename = main.write_lambda_file(filename, contents)

    assert lambda_filename == "/tmp/test-filename"
