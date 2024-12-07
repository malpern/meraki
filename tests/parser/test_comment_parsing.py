import pytest
from meraki.parser import parse_config
from typing import NoReturn


def test_basic_line_comment() -> None:
    """Test parsing of a single line comment."""
    config = """# Basic comment"""
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0] == "# Basic comment"


def test_inline_comment() -> None:
    """Test parsing of an inline comment."""
    config = """mod1 = lcmd + lalt  # Inline comment"""
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0] == "# Inline comment"


def test_line_comments() -> None:
    """Test parsing of line comments."""
    config = """
    # This is a comment about modifiers
    mod1 = lcmd + lalt  # Inline comment

    # Application launching
    mod1 - m : open -a Mail.app  # Launch Mail
    """
    parsed = parse_config(config)
    
    assert len(parsed.comments) == 4
    assert '# This is a comment about modifiers' in parsed.comments
    assert '# Inline comment' in parsed.comments
    assert '# Application launching' in parsed.comments
    assert '# Launch Mail' in parsed.comments


def test_multi_line_notes() -> None:
    """Test parsing of multi-line notes with @END markers."""
    config = """
    @END This is a multi-line note
    that describes the following
    keybinding in detail. END

    mod1 - k : focus --app "kitty"
    """
    parsed = parse_config(config)
    
    assert len(parsed.notes) == 1
    assert parsed.notes[0].startswith('@END This is a multi-line note')
    assert 'keybinding in detail. END' in parsed.notes[0]


def test_comment_preservation() -> None:
    """Test that comments are preserved during parsing."""
    config = """
    # Modifier definitions
    mod1 = lcmd + lalt
    mod2 = lshift + lctrl

    # Application bindings
    mod1 - m : open -a Mail.app
    mod1 - s : open -a Safari
    """
    parsed = parse_config(config)
    
    assert len(parsed.comments) == 2
    assert '# Modifier definitions' in parsed.comments
    assert '# Application bindings' in parsed.comments
    assert len(parsed.bindings) == 2


def test_complex_config_comments() -> None:
    """Test comment parsing in a more complex configuration."""
    config = """
    # Global modifier setup
    mod1 = lcmd + lalt  # Primary modifier

    # Leader key configuration
    mod1 - l : {  # Web and productivity apps
        h : open -a Safari;     # Web browser
        t : open -a Terminal;   # Terminal emulator
        c : open -a Calendar;   # Calendar app
    }
    """
    parsed = parse_config(config)
    
    assert len(parsed.comments) == 7
    expected_comments = [
        '# Global modifier setup', 
        '# Primary modifier', 
        '# Leader key configuration', 
        '# Web and productivity apps', 
        '# Web browser', 
        '# Terminal emulator', 
        '# Calendar app'
    ]
    
    for comment in expected_comments:
        assert comment in parsed.comments 


def test_leader_block_comments() -> None:
    """Test parsing of comments in leader blocks."""
    config = """
    mod1 - l : {  # Leader block
        h : open -a Safari;  # Browser
    }
    """
    parsed = parse_config(config)
    assert len(parsed.comments) == 2
    assert "# Leader block" in parsed.comments
    assert "# Browser" in parsed.comments