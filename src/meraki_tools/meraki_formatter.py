from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class FormattingOptions:
    """Configuration options for the formatter."""
    indent_size: int = 4
    max_line_length: int = 80
    align_comments: bool = True


class MerakiFormatter:
    def __init__(self, options: Optional[FormattingOptions] = None):
        self.options = options or FormattingOptions()
    
    def format_string(self, content: str) -> str:
        """Format a Meraki config string according to style rules."""
        lines = content.splitlines()
        formatted_lines = []
        
        # Track indentation level for nested blocks
        indent_level = 0
        in_block = False
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                formatted_lines.append("")
                continue
            
            # Handle block start/end
            if "{" in stripped:
                formatted = self._format_line(stripped, indent_level)
                formatted_lines.append(formatted)
                indent_level += 1
                in_block = True
                continue
                
            if "}" in stripped:
                indent_level -= 1
                formatted = " " * (self.options.indent_size * indent_level) + "}"
                formatted_lines.append(formatted)
                in_block = False
                continue
            
            # Format the line with proper indentation
            formatted = self._format_line(stripped, indent_level)
            formatted_lines.append(formatted)
        
        return "\n".join(formatted_lines)
    
    def _format_line(self, line: str, indent_level: int) -> str:
        """Format a single line with proper indentation and spacing."""
        # Split into components
        if "=" in line:  # Modifier definition
            return self._format_modifier_def(line, indent_level)
        elif ":" in line:  # Keybinding or nested binding
            if "-" in line and not line.startswith("h") and not line.startswith("t"):  # Regular keybinding
                return self._format_keybinding(line, indent_level)
            else:  # Nested binding
                return self._format_nested_binding(line, indent_level)
        else:  # Comment or other
            return " " * (self.options.indent_size * indent_level) + line.strip()
    
    def _format_modifier_def(self, line: str, indent_level: int) -> str:
        """Format a modifier definition line."""
        # Split into components and handle comments
        parts = line.split("#", 1)
        definition = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""
        
        # Split definition into name and keys
        name, keys = definition.split("=", 1)
        # Split keys and add + between them
        key_parts = [k.strip() for k in keys.split("+")]
        keys = " + ".join(key_parts)
        
        formatted = (
            " " * (self.options.indent_size * indent_level) +
            f"{name.strip()} = {keys}"
        )
        
        if comment:
            if self.options.align_comments:
                # Fixed alignment for comments
                return f"{formatted:<40}# {comment}"
            else:
                return formatted + "  # " + comment
        else:
            return formatted
    
    def _format_keybinding(self, line: str, indent_level: int) -> str:
        """Format a keybinding line."""
        # Split into components and handle comments
        parts = line.split("#", 1)
        binding = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""
        
        # Split binding into modifier, key, and action
        mod_key, action = binding.split(":", 1)
        mod, key = mod_key.split("-", 1)
        
        formatted = (
            " " * (self.options.indent_size * indent_level) +
            f"{mod.strip()} - {key.strip()} : {action.strip()}"
        )
        
        if comment:
            if self.options.align_comments:
                # Fixed alignment for comments
                return f"{formatted:<40}# {comment}"
            else:
                return formatted + "  # " + comment
        else:
            return formatted
    
    def _format_nested_binding(self, line: str, indent_level: int) -> str:
        """Format a nested binding line."""
        # Split into components and handle comments
        parts = line.split("#", 1)
        binding = parts[0].strip()
        comment = parts[1].strip() if len(parts) > 1 else ""
        
        # Split binding into key and action
        key, action = binding.split(":", 1)
        
        formatted = (
            " " * (self.options.indent_size * indent_level) +
            f"{key.strip()} : {action.strip()}"
        )
        
        if comment:
            if self.options.align_comments:
                # Fixed alignment for comments
                return f"{formatted:<40}# {comment}"
            else:
                return formatted + "  # " + comment
        else:
            return formatted