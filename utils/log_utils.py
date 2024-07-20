import logging


def config_log(
        log_file: str,
        level: str = 'info',
        with_prefix: bool = False,
        clear: bool = False
):
    level = logging.DEBUG if level.lower() == 'debug' else logging.INFO

    if clear:
        with open(log_file, 'w'):
            pass

    logger = logging.getLogger()
    # remove all handlers
    while len(logger.handlers) > 0:
        logger.removeHandler(logger.handlers[0])

    logger.setLevel(level)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    if with_prefix:
        formatter = logging.Formatter(
            fmt='''[%(asctime)s - %(levelname)s]: %(message)s''',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)    
    logger.addHandler(console_handler)
