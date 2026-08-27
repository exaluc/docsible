"""CLI option groups for document_role command."""

from .content import add_content_options
from .framing import add_framing_options
from .generation import add_generation_options
from .output import add_output_options
from .paths import add_path_options
from .recommendations import add_recommendation_options
from .repository import add_repository_options
from .resolution import resolve_role_command_options
from .templates import add_template_options

__all__ = [
    "add_path_options",
    "add_output_options",
    "add_content_options",
    "add_template_options",
    "add_generation_options",
    "add_repository_options",
    "add_recommendation_options",
    "add_framing_options",
    "resolve_role_command_options",
]
