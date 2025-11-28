"""
API Package
Backward compatibility re-exports for new src/ structure
"""

from src.api.server import app
from src.api.data_mapper import part_data_to_part_object
from src.api.conversation_manager import ConversationManager

__all__ = ["app", "part_data_to_part_object", "ConversationManager"]
