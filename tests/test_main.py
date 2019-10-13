import mock
import pytest
from tests import mocks
from cloud_storage import main


def test_get_instructors_returns_unique_instructors():
    contents = mocks.contents
    # contents = [
    #     {"instructor": "Mark P Jones"},
    #     {"instructor": "David D Ely"},
    #     {"instructor": "Wuchan Feng"},
    #     {"instructor": "Mark Morrissey"},
    #     {"instructor": "TBD"},
    #     {"instructor": "Chris Gilmore"},
    #     {"instructor": "David D Ely"},
    #     {"instructor": "Katie Casamento"},
    # ]
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
