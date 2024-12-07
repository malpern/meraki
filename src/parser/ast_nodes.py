from dataclasses import dataclass
from typing import List, Dict, Optional, Union
from enum import Enum

class CommentType(Enum):
    LINE = "line"
    INLINE = "inline"
    MULTILINE = "multiline"

@dataclass
class Comment:
    type: CommentType
    text: str
    line_number: int
    end_line: Optional[int] = None
    associated_code_line: Optional[int] = None

@dataclass
class ASTNode:
    line_number: int
    comments: List[Comment]

@dataclass
class Modifier(ASTNode):
    name: str
    keys: List[str]

@dataclass
class Action(ASTNode):
    command: str

@dataclass
class KeyBinding(ASTNode):
    key_combination: str
    key: str
    timeout: Optional[int]
    action: Optional[Action] = None
    nested_bindings: Optional[Dict[str, 'KeyBinding']] = None

@dataclass
class MerakiAST:
    modifiers: Dict[str, Modifier]
    keybindings: List[KeyBinding]
    comments: List[Comment] 