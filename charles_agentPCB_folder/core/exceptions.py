"""
Custom exceptions for the PCB design system
"""


class PCBDesignException(Exception):
    """Base exception for all PCB design errors"""
    pass


class AgentException(PCBDesignException):
    """Exception raised by agents"""
    def __init__(self, message: str, agent_name: str = None, details: dict = None):
        super().__init__(message)
        self.agent_name = agent_name
        self.details = details or {}


class ValidationException(PCBDesignException):
    """Exception for validation errors"""
    def __init__(self, message: str, field: str = None, errors: list = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class PartNotFoundException(PCBDesignException):
    """Exception when part is not found"""
    def __init__(self, part_id: str, message: str = None):
        super().__init__(message or f"Part not found: {part_id}")
        self.part_id = part_id


class CompatibilityException(PCBDesignException):
    """Exception for compatibility issues"""
    def __init__(self, message: str, part1: str = None, part2: str = None, issues: list = None):
        super().__init__(message)
        self.part1 = part1
        self.part2 = part2
        self.issues = issues or []


class CacheException(PCBDesignException):
    """Exception for cache operations"""
    pass


class OrchestrationException(PCBDesignException):
    """Exception during design orchestration"""
    def __init__(self, message: str, step: str = None, design_state: dict = None):
        super().__init__(message)
        self.step = step
        self.design_state = design_state or {}

