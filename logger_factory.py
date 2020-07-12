import logging
import pathlib

import text


def make_logger(name: str, logging_path: pathlib.Path) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logging_path.mkdir(exist_ok=True)
    handler = logging.FileHandler(str(logging_path / (text.to_filename(name) + ".txt")))
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("[%(asctime)s.%(msecs)03d] [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
