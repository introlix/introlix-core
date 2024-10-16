import os
import sys
from introlix_api.logger import logger

def error_message_detail(error, error_detail):
    """
    Retruns the error message and error details and logs the error

    Args:
        error: error message
        error_detail: error details
    
    Returns:
        error_message: error message
    """
    _, _, exe_tb = error_detail.exc_info()
    file_name = exe_tb.tb_frame.f_code.co_filename
    line_number = exe_tb.tb_lineno
    error_message = "Error occured in file called [{0}] line number: [{1}] error message: [{2}]".format(
        file_name, line_number, str(error)
    )

    logger.info(error_message)

    return error_message

class CustomException(Exception):
    def __init__(self, error_message, error_detail):
        super().__init__(error_message)
        self.error_message = error_message_detail(error_message, error_detail=error_detail)

    def __str__(self):
        return self.error_message
    