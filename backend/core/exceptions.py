"""
Custom Exceptions
Enterprise-grade exception handling
"""


class PCBDesignException(Exception):
    """Base exception for PCB design errors."""
    pass


class AgentException(PCBDesignException):
    """Exception raised by agents."""
    
    def __init__(self, message: str, agent_name: str, details: dict = None):
        super().__init__(message)
        self.agent_name = agent_name
        self.details = details or {}


class ValidationException(PCBDesignException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, errors: list = None):
        super().__init__(message)
        self.field = field
        self.errors = errors or []


class PartNotFoundException(PCBDesignException):
    """Exception when part is not found."""
    
    def __init__(self, message: str, part_id: str):
        super().__init__(message)
        self.part_id = part_id


class CompatibilityException(PCBDesignException):
    """Exception for compatibility issues."""
    
    def __init__(self, message: str, part1: str, part2: str, issues: list = None):
        super().__init__(message)
        self.part1 = part1
        self.part2 = part2
        self.issues = issues or []
