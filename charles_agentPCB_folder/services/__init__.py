"""
Services Package
Backward compatibility re-exports for new src/ structure
"""

from src.services.streaming_service import (
    StreamingOrchestrator,
    generate_design_stream,
    refine_design_stream,
    answer_question
)

__all__ = [
    "StreamingOrchestrator",
    "generate_design_stream",
    "refine_design_stream",
    "answer_question",
]
