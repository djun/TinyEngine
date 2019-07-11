# coding=utf-8

# import logging.config
from logging.handlers import RotatingFileHandler
from logging import getLogger, StreamHandler, Formatter, INFO, DEBUG
import os
import json


def get_logger(name=None, stream_log_level=INFO, file_log_level=DEBUG, encoding='utf-8', log_dir=''):

    logger = getLogger(name)
    # if not logger.hasHandlers():
    if len(logger.handlers) <= 0:
        stream_handler = StreamHandler()
        stream_handler.setLevel(stream_log_level)
        log_path = os.path.abspath(os.path.join(log_dir, r'log.txt' if name is None else r'log_' + name + '.txt'))
        rotate_handler = RotatingFileHandler(log_path, 'a', maxBytes=1024 * 1024 * 10, backupCount=99,
                                             encoding=encoding)
        rotate_handler.setLevel(file_log_level)

        datefmt_str = '%Y-%m-%d %H:%M:%S'
        format_str = '[%(asctime)s][%(levelname)s][%(filename)s - %(lineno)d]%(message)s'
        format_simple_str = '[%(asctime)s][%(levelname)s]%(message)s'
        formatter = Formatter(format_str, datefmt_str)
        formatter_simple = Formatter(format_simple_str, datefmt_str)
        rotate_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter_simple)

        logger.addHandler(stream_handler)
        logger.addHandler(rotate_handler)
        logger.setLevel(DEBUG)

    return logger


def load_config(file_name, encoding='utf-8'):
    with open(file_name, 'r', encoding=encoding) as fp:
        config = json.load(fp)
    if isinstance(config, dict):
        return config
    else:
        return dict()


def save_config(config, file_name, encoding='utf-8'):
    if isinstance(config, dict):
        with open(file_name, 'w+', encoding=encoding) as fp:
            # 2018-3-26：新增sort_keys=True、indent=2
            json.dump(config, fp, ensure_ascii=False, sort_keys=True, indent=2)
