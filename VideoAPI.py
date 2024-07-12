import http.client
import json
import requests
import time
from Logger import SystemLogger
from OssAPI import upload_and_get_signed_key

def retry(attempts=3, delay=5, error_message=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    SystemLogger.error(f"orderId: {args[0]}, Attempt {attempt + 1}, error_message: {error_message}, Error: {str(e)}")
                    if attempt == attempts - 1:
                        if error_message:
                            message = error_message
                            #update_order_status(args[0], 4, error_message)
                        raise
                    time.sleep(delay)
        return wrapper
    return decorator

