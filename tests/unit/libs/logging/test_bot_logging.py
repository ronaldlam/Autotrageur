import logging
import logging.handlers

import pytest

import libs.logging.bot_logging as bot_logging
from libs.utilities import AnyStringStartingWith


@pytest.fixture(scope='function')
def autotrageur_bg_logger(mocker):
    return bot_logging.AutotrageurBackgroundLogger()

class TestAutotrageurBackgroundLogger():
    def test_set_stream_handler(self, mocker, autotrageur_bg_logger):
        # Needs to be cached. Seems to break pytest when patched without resetting.
        original_stream_handler = logging.StreamHandler
        stream_handler = mocker.Mock()
        stream_format = mocker.Mock()

        mocker.patch.object(logging, 'StreamHandler', return_value=stream_handler)

        bg_logger = autotrageur_bg_logger.set_stream_handler(stream_format)

        assert bg_logger.stream_handler is stream_handler
        stream_handler.setLevel.assert_called_once_with(logging.INFO)
        stream_handler.setFormatter.assert_called_once_with(stream_format)
        assert bg_logger is autotrageur_bg_logger

        # Reset StreamHandler
        logging.StreamHandler = original_stream_handler

    def test_set_file_handler(self, mocker, autotrageur_bg_logger):
        logfile_name = mocker.Mock()
        file_format = mocker.Mock()
        file_handler = mocker.Mock()
        file_handler_constructor = mocker.patch.object(
            logging.handlers, 'TimedRotatingFileHandler', return_value=file_handler)

        bg_logger = autotrageur_bg_logger.set_file_handler(logfile_name, file_format)

        assert bg_logger.file_handler is file_handler
        file_handler_constructor.assert_called_once_with(
            logfile_name, when='H', interval=4, backupCount=100000)
        file_handler.setLevel.assert_called_once_with(logging.DEBUG)
        file_handler.setFormatter.assert_called_once_with(file_format)
        assert bg_logger is autotrageur_bg_logger

    def test_set_queue_handler(self, mocker, autotrageur_bg_logger):
        q = mocker.Mock()
        queue_handler = mocker.Mock()
        queue_handler_constructor = mocker.patch.object(
            logging.handlers, 'QueueHandler', return_value=queue_handler)

        bg_logger = autotrageur_bg_logger.set_queue_handler(q)

        assert bg_logger.queue is q
        assert bg_logger.queue_handler is queue_handler
        queue_handler_constructor.assert_called_once_with(q)
        assert bg_logger is autotrageur_bg_logger

    def test_build(self, mocker, autotrageur_bg_logger):
        # Cache the `getLogger` method.
        original_get_logger = logging.getLogger

        queue_listener = mocker.Mock()
        root_logger = mocker.Mock()
        q = mocker.Mock()
        stream_handler = mocker.Mock()
        file_handler = mocker.Mock()
        queue_handler = mocker.Mock()
        mocker.patch.object(autotrageur_bg_logger, 'queue', q, create=True)
        mocker.patch.object(autotrageur_bg_logger, 'stream_handler', stream_handler, create=True)
        mocker.patch.object(autotrageur_bg_logger, 'file_handler', file_handler, create=True)
        mocker.patch.object(autotrageur_bg_logger, 'queue_handler', queue_handler, create=True)
        queue_listener_constructor = mocker.patch.object(
            logging.handlers, 'QueueListener', return_value=queue_listener)
        get_logger = mocker.patch.object(logging, 'getLogger', return_value=root_logger)

        bot_logger = autotrageur_bg_logger.build()

        queue_listener_constructor.assert_called_once_with(
            q, stream_handler, file_handler,
            respect_handler_level=True)

        # Gets the root logger.
        get_logger.assert_called_once_with()
        root_logger.setLevel.assert_called_once_with(logging.DEBUG)
        root_logger.addHandler.assert_called_once_with(queue_handler)
        assert bot_logger.logger is root_logger
        assert bot_logger is autotrageur_bg_logger

        # Reset the getLogger method.
        logging.getLogger = original_get_logger

def test_setup_background_logger(mocker):
    # Object mocks.
    stream_format = mocker.Mock()
    file_format = mocker.Mock()
    bg_logger = mocker.Mock()

    # Builder function/constructor mocks.
    bg_logger_constructor = mocker.patch.object(bot_logging, 'AutotrageurBackgroundLogger')
    set_stream_handler = mocker.patch.object(bot_logging.AutotrageurBackgroundLogger.return_value, 'set_stream_handler')
    set_file_handler = mocker.patch.object(set_stream_handler.return_value, 'set_file_handler')
    set_queue_handler = mocker.patch.object(set_file_handler.return_value, 'set_queue_handler')
    build = mocker.patch.object(set_queue_handler.return_value, 'build', return_value=bg_logger)

    mocker.patch.object(logging, 'Formatter',
                        side_effect=[stream_format, file_format])
    q = mocker.patch.object(bot_logging, 'Queue')

    result_logger = bot_logging.setup_background_logger()

    q.assert_called_once_with(-1)

    # Test the building of the background logger.
    bg_logger_constructor.assert_called_once_with()
    set_stream_handler.assert_called_once_with(stream_format)
    set_file_handler.assert_called_once_with(AnyStringStartingWith('logs'), file_format)
    set_queue_handler.assert_called_once_with(q.return_value)
    build.assert_called_once_with()
    assert result_logger is bg_logger
