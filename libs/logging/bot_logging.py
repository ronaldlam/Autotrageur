import logging
import logging.handlers
import os
from datetime import datetime
from queue import Queue


class AutotrageurBackgroundLogger:
    def setStreamHandler(self, stream_format):
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(logging.INFO)
        self.stream_handler.setFormatter(stream_format)
        return self

    def setFileHandler(self, logfile_name, file_format):
        # BackupCount is arbitrarily large, will generate approx 3tb of
        # files before rollover. We rely on external scripts to archive the
        # logs.
        self.file_handler = logging.handlers.TimedRotatingFileHandler(
            logfile_name, when='H', interval=4, backupCount=100000)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(file_format)
        return self

    def setQueueHandler(self, queue):
        self.queue_handler = logging.handlers.QueueHandler(queue)
        return self

    def setQueueListener(self, queue):
        self.queue_listener = logging.handlers.QueueListener(
            queue, self.stream_handler, self.file_handler,
            respect_handler_level=True)
        return self

    def setLogger(self):
        root_logger = logging.getLogger()
        # This must be set so that the logger does not filter prematurely.
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self.queue_handler)
        self.logger = root_logger
        return self


def setup_background_logger():
    """Initialize logging in background thread.

    Returns:
        logging.handlers.QueueListener: The background thread listener
            that passes the log records to its handlers.
    """
    name = str(datetime.now()).replace(' ', '_').replace('.', '_').replace(':', '_')
    directory_name = 'logs/{}'.format(name)
    logfile_name = '{}/{}.log'.format(directory_name, name)

    # Intentionally unprotected. If there's another log with the same
    # timestamp, there's something wrong. Go figure it out.
    os.makedirs(directory_name)

    stream_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_format = logging.Formatter(
        "%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(funcName)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")

    queue = Queue(-1)  # no limit on size

    autotrageur_logger = (
        AutotrageurBackgroundLogger()
            .setStreamHandler(stream_format)
            .setFileHandler(logfile_name, file_format)
            .setQueueHandler(queue)
            .setQueueListener(queue)
            .setLogger())

    return autotrageur_logger
