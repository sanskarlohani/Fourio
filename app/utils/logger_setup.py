import logging
import json
import traceback
import sys
import os
from typing import Dict, Any

# --- Custom Formatter to Handle JSON and Error Tracing ---
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        
        log_record: Dict[str, Any] = {
            "time": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "msg": record.getMessage(),
        }
        
        log_record["source"] = f"{os.path.basename(record.pathname)}:{record.lineno}"
        log_record["func"] = record.funcName
        if record.exc_info:
            log_record["trace"] = traceback.format_exc(record.exc_info)
            log_record["error_msg"] = str(record.exc_info[1]) if record.exc_info[1] else log_record["msg"]
            log_record["msg"] = f"Error occurred: {log_record['error_msg']}"

        if hasattr(record, 'custom_fields'):
            log_record.update(record.custom_fields)
            
        return json.dumps(log_record)


def GetLogger(name: str = "fourio_app") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    logger.propagate = False 

    if logger.hasHandlers():
        return logger

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)

    return logger
