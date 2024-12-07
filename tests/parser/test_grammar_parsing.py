import pytest
from lark import Lark
from meraki.parser import parse_config

def test_modifier_definition():
    """Test parsing of basic modifier definitions."""
    configs = [
        "mod1 = lcmd + lalt",
        "mod2 = lshift + lctrl",
        "mod3 = cmd + alt"
    ]
    
    for config in configs:
        parsed = parse_config(config)
        assert len(parsed.modifiers) > 0
        assert all(isinstance(mods, list) for mods in parsed.modifiers.values())

def test_simple_keybinding():
    """Test parsing of simple keybindings."""
    configs = [
        "mod1 - m : open -a Mail.app",
        "mod1 + alt - s : open -a Safari",
        "cmd - x : kill -9 process"
    ]
    
    for config in configs:
        parsed = parse_config(config)
        assert len(parsed.bindings) > 0
        assert all('key' in binding and 'action' in binding for binding in parsed.bindings)

def test_group_syntax():
    """Test parsing of group syntax."""
    configs = [
        "mod1 + { c, f, m } : open -a { Chrome, Finder, Mail }",
        "cmd + { 1, 2, 3 } : switch_desktop { 1, 2, 3 }"
    ]
    
    for config in configs:
        parsed = parse_config(config)
        group_bindings = [b for b in parsed.bindings if 'keys' in b]
        assert len(group_bindings) > 0
        assert all(len(b['keys']) == len(b['actions']) for b in group_bindings)

def test_comments():
    """Test parsing of comments."""
    config = """
    # This is a comment about modifiers
    mod1 = lcmd + lalt  # Inline comment

    # Application launching
    mod1 - m : open -a Mail.app  # Launch Mail
    """
    
    parsed = parse_config(config)
    assert len(parsed.comments) > 0
    assert all(comment.startswith('#') for comment in parsed.comments)

def test_multiline_notes():
    """Test parsing of multi-line notes."""
    config = """
    @END This is a multi-line note
    that describes the following
    keybinding in detail. END

    mod1 - k : focus --app "kitty"
    """
    
    parsed = parse_config(config)
    assert len(parsed.notes) > 0
    assert any("multi-line note" in note for note in parsed.notes)

def test_complex_config():
    """Test parsing of a more complex configuration."""
    config = """
    # Global modifier setup
    mod1 = lcmd + lalt
    mod2 = lshift + lctrl

    # Application launching
    mod1 - m : open -a Mail.app
    mod1 + { c, f, m } : open -a { Chrome, Finder, Mail }

    @END This is a note about
    the following keybindings. END
    """
    
    parsed = parse_config(config)
    assert len(parsed.modifiers) > 0
    assert len(parsed.bindings) > 0
    assert len(parsed.comments) > 0
    assert len(parsed.notes) > 0

def test_error_handling():
    """Test error handling for invalid configurations."""
    invalid_configs = [
        "mod1 = ",  # Empty modifier
        "mod1 : action",  # Missing key separator
        "mod1 - : action",  # Missing key
        "mod1 - m",  # Missing action
    ]
    
    for config in invalid_configs:
        with pytest.raises(Exception):
            parse_config(config) 