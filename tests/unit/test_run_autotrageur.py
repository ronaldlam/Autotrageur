import pytest
import logging
import logging.handlers

import run_autotrageur

def test_setup_background_logging(mocker):
    # Needs to be cached. Seems to break pytest when patched without resetting.
    original_stream_handler = logging.StreamHandler

    # Object mocks.
    stream_format = mocker.Mock()
    file_format = mocker.Mock()
    listener = mocker.Mock()

    # Function/constructor mocks.
    mocker.patch.object(logging, 'Formatter',
                        side_effect=[stream_format, file_format])
    stream_handler = mocker.patch.object(logging, 'StreamHandler')
    file_handler = mocker.patch.object(logging.handlers, 'RotatingFileHandler')
    queue_handler = mocker.patch.object(logging.handlers, 'QueueHandler')
    queue_listener = mocker.patch.object(logging.handlers, 'QueueListener',
                                         return_value=listener)
    q = mocker.patch.object(run_autotrageur, 'Queue')
    root_logger = mocker.patch.object(logging, 'getLogger')

    run_autotrageur.setup_background_logging()

    stream_handler.return_value.setLevel.assert_called_once_with(logging.INFO)
    stream_handler.return_value.setFormatter.assert_called_once_with(stream_format)
    file_handler.return_value.setLevel.assert_called_once_with(logging.DEBUG)
    file_handler.return_value.setFormatter.assert_called_once_with(file_format)
    q.assert_called_once_with(-1)
    queue_handler.assert_called_once_with(q.return_value)
    queue_listener.assert_called_once_with(
        q.return_value, stream_handler.return_value,
        file_handler.return_value, respect_handler_level=True)
    root_logger.return_value.setLevel.assert_called_once_with(logging.DEBUG)
    root_logger.return_value.addHandler.assert_called_once_with(queue_handler.return_value)

    # Reset StreamHandler
    logging.StreamHandler = original_stream_handler

