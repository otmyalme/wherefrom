"""
Define the exceptions raised by the application.
"""

# Import the `file` and `read` modules to make absolutely sure the exceptions defined
# therein are registered. Import the other modules for consistency.
from wherefrom.exceptions import base
from wherefrom.exceptions import file
from wherefrom.exceptions import parse
from wherefrom.exceptions import read
from wherefrom.exceptions import registry


__all__ = ["base", "file", "parse", "read", "registry"]
