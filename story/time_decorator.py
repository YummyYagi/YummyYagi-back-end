import time
import logging

logging.basicConfig(filename='info.log', level=logging.INFO)
info_logger = logging.getLogger('info_logger')

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        info_logger.info(f"{end_time - start_time:.2f} seconds, {result}")
        return result

    return wrapper