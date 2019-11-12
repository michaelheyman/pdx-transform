import unittest.mock as mock

from app import utils


@mock.patch("app.utils.get_current_timestamp")
def test_generate_filename_generates_formatted_timestamp(mock_timestamp):
    mock_timestamp.return_value = 1_555_555_555.555_555

    filename = utils.generate_filename()

    assert mock_timestamp.called is True
    assert filename == "20190417194555.json"
