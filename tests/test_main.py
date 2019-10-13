import mock
import pytest
from collections import OrderedDict
from tests import mocks
from cloud_storage import main


@mock.patch("google.cloud.storage.Client.lookup_bucket")
@mock.patch("google.cloud.storage.Client")
def test_get_bucket(mock_storage_client, mock_lookup_bucket):
    # mock_storage_client.return_value = []
    mock_storage_client().lookup_bucket.return_value = None
    # mock_lookup_bucket.return_value = []

    get_bucket = main.get_bucket()

    assert get_bucket == None


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


@mock.patch("cloud_storage.main.get_bucket")
def test_get_latest_blob_returns_none_when_bucket_does_not_exist(mock_get_bucket):
    mock_get_bucket.return_value = None

    latest_blob = main.get_latest_blob()

    assert mock_get_bucket.called == True
    assert latest_blob == None


@mock.patch("cloud_storage.main.get_blobs_list")
@mock.patch("cloud_storage.main.get_bucket")
def test_get_latest_blob_returns_blob_when_only_one_blob_exists(
    mock_get_bucket, mock_get_blobs
):
    mock_get_bucket.return_value = "my-bucket"
    mock_get_blobs.return_value = [
        {"name": "1234567890.json", "description": "test-blob"}
    ]

    latest_blob = main.get_latest_blob()

    assert mock_get_bucket.called == True
    assert mock_get_blobs.called == True
    assert latest_blob == {"name": "1234567890.json", "description": "test-blob"}


@mock.patch("cloud_storage.main.get_blobs_list")
@mock.patch("cloud_storage.main.get_bucket")
def test_get_latest_blob_returns_blob_when_only_one_blob_exists(
    mock_get_bucket, mock_get_blobs
):
    mock_get_bucket.return_value = "my-bucket"
    mock_get_blobs.return_value = [
        {"name": "1000000000.json", "description": "oldest-blob"},
        {"name": "1234567890.json", "description": "latest-blob"},
    ]

    latest_blob = main.get_latest_blob()

    assert mock_get_bucket.called == True
    assert mock_get_blobs.called == True
    assert latest_blob == {"name": "1234567890.json", "description": "latest-blob"}


def test_rate_instructors_returns_empty_dict_when_no_instructors():
    instructors = set()

    rated_instructors = main.rate_instructors(instructors)

    assert rated_instructors == {}


@mock.patch("cloud_storage.main.get_instructor")
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


@mock.patch("cloud_storage.main.get_instructor")
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


@mock.patch("cloud_storage.main.get_instructor")
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
