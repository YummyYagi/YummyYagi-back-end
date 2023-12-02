import time
import logging
from django.conf import settings

# 로깅 설정
logging.config.dictConfig(settings.LOGGING)

# 로거 가져오기
info_logger = logging.getLogger('info_logger')

def timing_decorator(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        info_logger.info(f"{end_time - start_time:.2f} seconds, {result}")
        return result

    return wrapper