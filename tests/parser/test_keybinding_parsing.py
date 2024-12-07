import pytest
from meraki.parser import parse_config

def test_basic_keybindings():
    """Test parsing of basic keybindings with actions."""
    config = """
    mod1 - m : open -a Mail.app
    mod1 - s : open -a "Sublime Text"
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['key'] == 'm'
    assert parsed['bindings'][0]['action'] == 'open -a Mail.app'
    assert parsed['bindings'][1]['key'] == 's'
    assert parsed['bindings'][1]['action'] == 'open -a "Sublime Text"'

def test_leader_key_parsing():
    """Test parsing of leader keys with default and custom timeouts."""
    config = """
    mod1 - l : {
        h : open -a Safari;
        t : open -a Terminal;
        c : open -a Calendar;
    }

    mod1 - w [750ms] : {
        f : open -a Finder;
        s : open -a "System Settings";
    }
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['type'] == 'leader'
    assert parsed['bindings'][0]['timeout'] == 500  # default timeout
    assert len(parsed['bindings'][0]['subkeys']) == 3
    
    assert parsed['bindings'][1]['type'] == 'leader'
    assert parsed['bindings'][1]['timeout'] == 750
    assert len(parsed['bindings'][1]['subkeys']) == 2

def test_group_syntax():
    """Test parsing of group syntax for command expansion."""
    config = """
    mod1 + { c, f, m } : open -a { "Chrome", "Finder", "Mail" }
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 3
    assert parsed['bindings'][0]['key'] == 'c'
    assert parsed['bindings'][0]['action'] == 'open -a Chrome'
    assert parsed['bindings'][1]['key'] == 'f'
    assert parsed['bindings'][1]['action'] == 'open -a Finder'
    assert parsed['bindings'][2]['key'] == 'm'
    assert parsed['bindings'][2]['action'] == 'open -a Mail'

def test_application_focus():
    """Test parsing of application focus commands."""
    config = """
    mod1 - j : focus --app "IntelliJ IDEA"
    mod1 - k : focus --app "kitty"
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['action'] == 'focus --app "IntelliJ IDEA"'
    assert parsed['bindings'][1]['action'] == 'focus --app "kitty"' 