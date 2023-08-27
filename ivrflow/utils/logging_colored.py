import logging


class CustomFormatter(logging.Formatter):
    """Custom format to logs with custom colors"""

    # Define colors
    debug = "\x1b[37m"  # White
    info = "\x1b[32;20m"  # Green
    warning = "\x1b[33;20m"  # Yellow
    error = "\x1b[38;2;237;85;85m"  # Red
    critical = "\x1b[38;2;216;123;60m"  # Orange
    reset_color = "\x1b[0m"

    # Define format logs
    prefix = "%(asctime)s | "
    fmt = "%(levelname)s - %(message)s"
    suffix = " | %(name)s (%(filename)s:%(lineno)d)"
    FORMATS = {
        logging.DEBUG: prefix + debug + fmt + reset_color + suffix,
        logging.INFO: prefix + info + fmt + reset_color + suffix,
        logging.WARNING: prefix + warning + fmt + reset_color + suffix,
        logging.ERROR: prefix + error + fmt + reset_color + suffix,
        logging.CRITICAL: prefix + critical + fmt + reset_color + suffix,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)
