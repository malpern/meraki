import pytest
from meraki.parser import parse_config

def test_comment_between_modifiers() -> None:
    """Test parsing of comments between modifier definitions."""
    config = """
    mod1 = lcmd + lalt
    # Comment between modifiers
    mod2 = lshift + lctrl
    """
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert "# Comment between modifiers" in parsed.comments

def test_comment_before_binding() -> None:
    """Test parsing of comments before a binding."""
    config = """
    # Comment before binding
    mod1 - k : focus --app "kitty"
    """
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert "# Comment before binding" in parsed.comments

def test_nested_leader_comments() -> None:
    """Test parsing of nested comments in leader blocks."""
    config = """
    mod1 - l : {  # Outer comment
        # Inner comment 1
        h : open -a Safari;  # Inner comment 2
        # Inner comment 3
    }
    """
    parsed = parse_config(config)
    assert len(parsed.comments) == 4
    assert "# Outer comment" in parsed.comments
    assert "# Inner comment 1" in parsed.comments
    assert "# Inner comment 2" in parsed.comments
    assert "# Inner comment 3" in parsed.comments 