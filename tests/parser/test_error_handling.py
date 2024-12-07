import pytest
from meraki.parser import parse_config, ParseError

def test_invalid_modifier_definition():
    """Test error handling for invalid modifier definitions."""
    invalid_configs = [
        "mod1 = invalid + modifier",  # Invalid modifier
        "mod1 = cmd + cmd",  # Duplicate modifiers
        "mod1 = ",  # Empty modifier definition
    ]
    
    for config in invalid_configs:
        with pytest.raises(ParseError):
            parse_config(config)

def test_malformed_keybinding():
    """Test error handling for malformed keybindings."""
    invalid_configs = [
        "mod1 : open -a Mail.app",  # Missing key separator
        "mod1 - : open -a Mail.app",  # Missing key
        "mod1 - m",  # Missing action
        "mod1 - m : ",  # Empty action
    ]
    
    for config in invalid_configs:
        with pytest.raises(ParseError):
            parse_config(config)

def test_leader_key_errors():
    """Test error handling for leader key configurations."""
    invalid_configs = [
        """
        mod1 - l : {
            h : open -a Safari;
            t : open -a Terminal;
            : missing key
        }
        """,
        """
        mod1 - l [invalid] : {
            h : open -a Safari;
        }
        """,  # Invalid timeout format
    ]
    
    for config in invalid_configs:
        with pytest.raises(ParseError):
            parse_config(config)

def test_group_syntax_errors():
    """Test error handling for group syntax."""
    invalid_configs = [
        "mod1 + { c, f, } : open -a { Chrome, Finder }",  # Trailing comma
        "mod1 + { c, f } : open -a { Chrome }",  # Mismatched group sizes
        "mod1 + { } : open -a { }",  # Empty groups
    ]
    
    for config in invalid_configs:
        with pytest.raises(ParseError):
            parse_config(config)

def test_nested_leader_key_errors():
    """Test error handling for nested leader key configurations."""
    invalid_configs = [
        """
        mod1 - l : {
            h : {
                g : open -a Chrome;  # Nested leader key not supported
            }
        }
        """,
    ]
    
    for config in invalid_configs:
        with pytest.raises(ParseError):
            parse_config(config)

def test_performance_with_large_config():
    """Test parser performance and error handling with large configurations."""
    large_config = """
    # Large configuration with many bindings
    """ + "\n".join([
        f"mod1 - {chr(97+i)} : open -a App{i}" for i in range(1000)
    ])
    
    try:
        parsed = parse_config(large_config)
        assert len(parsed['bindings']) == 1000
    except Exception as e:
        pytest.fail(f"Large config parsing failed: {e}") 