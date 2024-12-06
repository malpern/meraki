from typing import Dict, List, Union, Optional
from dataclasses import dataclass
from pyparsing import (
    Word, alphas, alphanums, Forward, Group, OneOrMore,
    ZeroOrMore, Suppress, White, LineEnd, pythonStyleComment,
    delimitedList, Optional as Optional_, ParseResults,
    restOfLine, LineStart, White, stringEnd, QuotedString,
    nums, nestedExpr, originalTextFor
)

@dataclass
class ModifierDefinition:
    keys: List[str]
    comments: List[str]
    line_number: int

@dataclass
class Keybinding:
    key_combination: str
    key: str
    action: str
    comments: List[str]
    line_number: int
    timeout: Optional[int] = None
    nested_bindings: Optional[Dict[str, 'Keybinding']] = None

class MerakiParser:
    def __init__(self):
        self._setup_grammar()
    
    def _setup_grammar(self):
        # Basic elements
        modifier = Word(alphas.lower() + alphanums + "_")
        key = Word(alphas.lower())
        
        # Comments
        self.comment = pythonStyleComment.setResultsName("comment")
        
        # Timeout definition
        timeout = (
            Suppress("[") + 
            Word(nums).setResultsName("timeout") + 
            Suppress("ms") + 
            Suppress("]")
        ).setResultsName("timeout_def")
        
        # Modifier definition
        key_word = Word(alphas.lower())
        key_plus_key = (key_word("key1") + Suppress("+") + key_word("key2"))
        self.modifier_def = (
            Optional_(White()) +
            Optional_(self.comment)("leading_comment") +
            Optional_(White()) +
            modifier("name") + 
            Optional_(White()) +
            Suppress("=") + 
            Optional_(White()) +
            key_plus_key +
            Optional_(White()) +
            Optional_(self.comment)("trailing_comment") +
            Optional_(White()) +
            (LineEnd() | stringEnd)
        )
        
        # Action definition
        action = restOfLine.setResultsName("action")
        
        # Basic keybinding (without nested blocks)
        self.keybinding = (
            Optional_(White()) +
            Optional_(self.comment)("leading_comment") +
            Optional_(White()) +
            modifier("mod") +
            Optional_(White()) +
            Suppress("-") +
            Optional_(White()) +
            key("key") +
            Optional_(White()) +
            Optional_(timeout) +
            Optional_(White()) +
            Suppress(":") +
            Optional_(White()) +
            action
        )
        
        # Block keybinding
        self.block_keybinding = (
            Optional_(White()) +
            Optional_(self.comment)("leading_comment") +
            Optional_(White()) +
            modifier("mod") +
            Optional_(White()) +
            Suppress("-") +
            Optional_(White()) +
            key("key") +
            Optional_(White()) +
            Optional_(timeout) +
            Optional_(White()) +
            Suppress(":")
        )
    
    def parse_string(self, content: str) -> Dict:
        """Parse a Meraki config string and return an AST."""
        result = {
            "modifiers": {},
            "keybindings": []
        }
        
        # First pass: collect all lines and identify blocks
        lines = content.splitlines()
        current_line = 0
        
        while current_line < len(lines):
            line = lines[current_line]
            stripped = line.strip()
            if not stripped:
                current_line += 1
                continue
            
            try:
                # Try to parse as modifier definition
                parsed = self.modifier_def.parseString(stripped, parseAll=True)
                
                comments = []
                if "leading_comment" in parsed:
                    comments.append(parsed.leading_comment.strip())
                if "trailing_comment" in parsed:
                    comments.append(parsed.trailing_comment.strip())
                
                result["modifiers"][parsed.name] = {
                    "keys": [parsed.key1, parsed.key2],
                    "comments": [c for c in comments if c],
                    "line_number": current_line + 1
                }
                current_line += 1
            except Exception:
                try:
                    # Check if this is a block-style keybinding
                    if "{" in line:
                        # Parse the header
                        header = stripped.split("{")[0].strip()
                        
                        # Extract timeout if present
                        timeout = None
                        if "[" in header and "]" in header:
                            timeout_start = header.find("[") + 1
                            timeout_end = header.find("ms]")
                            if timeout_start > 0 and timeout_end > timeout_start:
                                timeout = int(header[timeout_start:timeout_end])
                                header = header[:timeout_start - 1].strip() + " : " + header[timeout_end + 3:].strip()
                        
                        # Parse the header without the timeout
                        header_parts = header.split(":")
                        if len(header_parts) >= 1:
                            binding_def = header_parts[0].strip()
                            if "-" in binding_def:
                                mod, key = binding_def.split("-", 1)
                                mod = mod.strip()
                                key = key.strip()
                                
                                # Collect the block content
                                block_lines = []
                                brace_count = line.count("{") - line.count("}")
                                base_indent = len(line) - len(line.lstrip())
                                
                                # Add any content after the opening brace
                                if "{" in line:
                                    content_after_brace = line.split("{", 1)[1].strip().rstrip("}")
                                    if content_after_brace:
                                        block_lines.append(content_after_brace)
                                
                                while brace_count > 0 and current_line + 1 < len(lines):
                                    current_line += 1
                                    next_line = lines[current_line]
                                    indent = len(next_line) - len(next_line.lstrip())
                                    stripped_next = next_line.strip()
                                    
                                    if stripped_next:
                                        if indent > base_indent or "}" in stripped_next:
                                            block_lines.append(stripped_next)
                                        brace_count += stripped_next.count("{") - stripped_next.count("}")
                                
                                binding = {
                                    "key_combination": mod,
                                    "key": key,
                                    "action": None,
                                    "comments": [],
                                    "line_number": current_line + 1,
                                    "timeout": timeout,
                                    "nested_bindings": self._parse_nested_block("\n".join(block_lines))
                                }
                                
                                result["keybindings"].append(binding)
                        current_line += 1
                    else:
                        # Try to parse as simple keybinding
                        parsed = self.keybinding.parseString(stripped)
                        
                        binding = {
                            "key_combination": parsed.mod,
                            "key": parsed.key,
                            "action": parsed.action.strip(),
                            "comments": [],
                            "line_number": current_line + 1,
                            "timeout": int(parsed.timeout_def.timeout) if "timeout_def" in parsed else None,
                            "nested_bindings": None
                        }
                        
                        result["keybindings"].append(binding)
                        current_line += 1
                except Exception as e:
                    print(f"Error parsing line {current_line + 1}: {e}")
                    print(f"Line content: {line}")
                    print(f"Stripped content: {stripped}")
                    current_line += 1
        
        return result
    
    def _parse_nested_block(self, block: str) -> Dict[str, Dict]:
        """Parse a nested block into a dictionary structure."""
        result = {}
        
        # Split the block into individual bindings
        lines = block.splitlines()
        current_line = 0
        
        while current_line < len(lines):
            line = lines[current_line].strip().rstrip(";")
            if not line:
                current_line += 1
                continue
            
            if "{" in line:
                # This is a nested block
                key = line.split(":", 1)[0].strip()
                block_lines = []
                brace_count = line.count("{") - line.count("}")
                
                # Add any content after the opening brace
                if "{" in line:
                    content_after_brace = line.split("{", 1)[1].strip().rstrip("}")
                    if content_after_brace:
                        block_lines.append(content_after_brace)
                
                while brace_count > 0 and current_line + 1 < len(lines):
                    current_line += 1
                    next_line = lines[current_line].strip()
                    if next_line:
                        block_lines.append(next_line)
                        brace_count += next_line.count("{") - next_line.count("}")
                
                result[key] = {
                    "action": None,
                    "nested_bindings": self._parse_nested_block("\n".join(block_lines))
                }
                current_line += 1
            else:
                # This is a simple binding
                try:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()
                    
                    result[key] = {
                        "action": value,
                        "nested_bindings": None
                    }
                except Exception:
                    pass
                current_line += 1
        
        return result
    
    def parse_file(self, file_path: str) -> Dict:
        """Parse a Meraki config file and return an AST."""
        with open(file_path, 'r') as f:
            content = f.read()
        return self.parse_string(content) 