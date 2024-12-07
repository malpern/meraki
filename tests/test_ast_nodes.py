import pytest
from src.parser.ast_nodes import (
    CommentType,
    Comment,
    Modifier,
    Action,
    KeyBinding,
    MerakiAST
)

def test_comment_creation():
    # Test line comment
    line_comment = Comment(
        type=CommentType.LINE,
        text="Define modifiers",
        line_number=1
    )
    assert line_comment.type == CommentType.LINE
    assert line_comment.text == "Define modifiers"
    assert line_comment.line_number == 1
    assert line_comment.end_line is None
    assert line_comment.associated_code_line is None

    # Test inline comment
    inline_comment = Comment(
        type=CommentType.INLINE,
        text="Main modifier",
        line_number=2,
        associated_code_line=2
    )
    assert inline_comment.type == CommentType.INLINE
    assert inline_comment.associated_code_line == 2

def test_modifier_creation():
    comment = Comment(
        type=CommentType.INLINE,
        text="Main modifier",
        line_number=1
    )
    modifier = Modifier(
        line_number=1,
        comments=[comment],
        name="mod1",
        keys=["lcmd", "lalt"]
    )
    assert modifier.name == "mod1"
    assert len(modifier.keys) == 2
    assert modifier.comments[0].text == "Main modifier"

def test_keybinding_creation():
    # Test simple keybinding
    action = Action(line_number=3, comments=[], command="open -a Safari")
    binding = KeyBinding(
        line_number=3,
        comments=[],
        key_combination="mod1",
        key="h",
        timeout=500,
        action=action
    )
    assert binding.key_combination == "mod1"
    assert binding.key == "h"
    assert binding.timeout == 500
    assert binding.action.command == "open -a Safari"

    # Test nested keybinding
    nested = {
        "h": KeyBinding(
            line_number=4,
            comments=[],
            key_combination="mod1",
            key="h",
            timeout=None,
            action=Action(line_number=4, comments=[], command="open -a Safari")
        )
    }
    parent = KeyBinding(
        line_number=3,
        comments=[],
        key_combination="mod1",
        key="l",
        timeout=500,
        nested_bindings=nested
    )
    assert parent.nested_bindings["h"].action.command == "open -a Safari"

def test_meraki_ast_creation():
    modifier = Modifier(
        line_number=1,
        comments=[],
        name="mod1",
        keys=["lcmd", "lalt"]
    )
    binding = KeyBinding(
        line_number=3,
        comments=[],
        key_combination="mod1",
        key="h",
        timeout=500,
        action=Action(line_number=3, comments=[], command="open -a Safari")
    )
    ast = MerakiAST(
        modifiers={"mod1": modifier},
        keybindings=[binding],
        comments=[]
    )
    assert "mod1" in ast.modifiers
    assert len(ast.keybindings) == 1
    assert ast.keybindings[0].action.command == "open -a Safari" 