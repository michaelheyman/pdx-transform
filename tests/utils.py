import asyncio


def set_async_result(mock, result):
    mock.return_value = asyncio.Future()
    mock.return_value.set_result(result)
    return mock
