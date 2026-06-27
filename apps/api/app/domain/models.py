from enum import Enum

class AgentStatus(str, Enum):
    ANALYZING = "ANALYZING"
    REJECTED = "REJECTED"
    PASSED = "PASSED"
    REGISTERED = "REGISTERED"
    PLANNING = "PLANNING"
    PR_OPEN = "PR_OPEN"
    PREVIEW_READY = "PREVIEW_READY"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    MERGED = "MERGED"
    IDLE = "IDLE"
    ERROR = "ERROR"

class NotFoundError(Exception):
    pass

class ConflictError(Exception):
    pass
