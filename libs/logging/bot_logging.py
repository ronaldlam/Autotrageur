import logging
import logging.handlers
import os
from datetime import datetime
from queue import Queue


class AutotrageurBackgroundLogger:
    """Encapsulates the Background Logger for the Autotrageur Bot.

    Utilizes the Builder pattern to add each component of the Background
    Logger."""
    def set_stream_handler(self, stream_format):
        """Sets the stream handler of the background loggger.

        Outputs any INFO level logs, and levels and above, to a specified file.

        Args:
            stream_format (logging.Formatter): A formatter to be used for the
                StreamHandler.

        Returns:
            AutotrageurBackgroundLogger: The Logger with the set StreamHandler.
        """
        self.stream_handler = logging.StreamHandler()
        self.stream_handler.setLevel(logging.INFO)
        self.stream_handler.setFormatter(stream_format)
        return self

    def set_file_handler(self, logfile_name, file_format):
        """Sets the file handler of the background logger.

        Outputs any DEBUG level logs, and levels above, to a specified file.

        Args:
            logfile_name (str): The name of the logfile to be written to.
            file_format (logging.Formatter): A formatter to be used for the
                FileHandler.

        Returns:
            AutotrageurBackgroundLogger: The Logger with the set FileHandler.
        """
        # BackupCount is arbitrarily large, will generate approx 3tb of
        # files before rollover. We rely on external scripts to archive the
        # logs.
        self.file_handler = logging.handlers.TimedRotatingFileHandler(
            logfile_name, when='H', interval=4, backupCount=100000)
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(file_format)
        return self

    def set_queue_handler(self, queue):
        """Sets the queue handler of the background logger.

        Uses a queue and is necessary for background logging on a separate
        thread.

        Args:
            queue (Queue): The queue associated with the QueueHandler.

        Returns:
            AutotrageurBackgroundLogger: The Logger with the set QueueHandler.
        """
        self.queue = queue
        self.queue_handler = logging.handlers.QueueHandler(queue)
        return self

    def build(self):
        """Final step in building the background logger.

        Sets the queue listener and logger object.

        Returns:
            AutotrageurBackgroundLogger: The completely built background
                logger.
        """

        # Set the QueueListener.
        self.queue_listener = logging.handlers.QueueListener(
            self.queue, self.stream_handler, self.file_handler,
            respect_handler_level=True)

        root_logger = logging.getLogger()
        # This must be set so that the logger does not filter prematurely.
        root_logger.setLevel(logging.DEBUG)
        root_logger.addHandler(self.queue_handler)
        self.logger = root_logger
        return self


def setup_background_logger():
    """Sets up the background logger object for the bot.

    Returns:
        AutotrageurBackgroundLogger: The background logger used as the parent
            logger for the bot.
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
            .set_stream_handler(stream_format)
            .set_file_handler(logfile_name, file_format)
            .set_queue_handler(queue)
            .build())

    return autotrageur_logger