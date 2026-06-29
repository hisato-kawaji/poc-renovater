import logging
from collections import deque
from datetime import datetime

class MemoryLogHandler(logging.Handler):
    def __init__(self, capacity=1000):
        super().__init__()
        self.logs = deque(maxlen=capacity)

    def emit(self, record):
        try:
            msg = self.format(record)
            timestamp = datetime.fromtimestamp(record.created).isoformat()
            self.logs.append({
                "timestamp": timestamp,
                "level": record.levelname,
                "message": msg,
                "logger": record.name
            })
        except Exception:
            self.handleError(record)

    def get_logs(self):
        return list(self.logs)

# Global singleton
memory_handler = MemoryLogHandler()
memory_handler.setFormatter(logging.Formatter('%(message)s'))

def setup_memory_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    logging.getLogger("app").setLevel(logging.INFO)
    
    if memory_handler not in root_logger.handlers:
        root_logger.addHandler(memory_handler)
    # Also attach to uvicorn loggers if they exist
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logger = logging.getLogger(logger_name)
        if memory_handler not in logger.handlers:
            logger.addHandler(memory_handler)
