import pytest
from meraki.parser import parse_config

def test_basic_modifier_definition():
    """Test parsing of basic modifier definitions."""
    config = """
    mod1 = lcmd + lalt
    mod2 = lshift + lctrl
    """
    parsed = parse_config(config)
    
    assert 'mod1' in parsed['modifiers']
    assert parsed['modifiers']['mod1'] == ['lcmd', 'lalt']
    assert 'mod2' in parsed['modifiers']
    assert parsed['modifiers']['mod2'] == ['lshift', 'lctrl']

def test_standard_modifier_support():
    """Test support for standard modifiers."""
    config = """
    cmd - m : open -a Mail.app
    alt + shift - s : open -a Safari
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['modifiers'] == ['cmd']
    assert parsed['bindings'][1]['modifiers'] == ['alt', 'shift']

def test_modifier_only_keybinds():
    """Test modifier-only keybinds with activation flags."""
    config = """
    cmd ~down: show_app_switcher
    cmd ~up: hide_app_switcher
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['activation_flag'] == '~down'
    assert parsed['bindings'][1]['activation_flag'] == '~up'

def test_compound_modifiers():
    """Test complex modifier combinations."""
    config = """
    mod1 + shift - a : action1
    mod2 + ctrl - b : action2
    """
    parsed = parse_config(config)
    
    assert len(parsed['bindings']) == 2
    assert parsed['bindings'][0]['modifiers'] == ['mod1', 'shift']
    assert parsed['bindings'][1]['modifiers'] == ['mod2', 'ctrl'] 