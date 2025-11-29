"""
Custom exceptions
"""
from typing import Optional


class PCBDesignException(Exception):
    """Base exception for PCB design errors"""
    pass


class RequirementsExtractionError(PCBDesignException):
    """Error extracting requirements from query"""
    pass


class PartSelectionError(PCBDesignException):
    """Error selecting compatible parts"""
    pass


class CompatibilityError(PCBDesignException):
    """Error checking part compatibility"""
    pass


class BOMGenerationError(PCBDesignException):
    """Error generating BOM"""
    pass

