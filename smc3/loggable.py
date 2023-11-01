import logging


class Loggable:
    def set_logger(self, logger: logging.Logger) -> None:
        self._logger = logger
        self.log_debug = self._logger.debug
        self.log_info = self._logger.info
        self.log_warning = self._logger.warning
        self.log_error = self._logger.error
