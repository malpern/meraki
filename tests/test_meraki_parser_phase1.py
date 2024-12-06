"""Tests for Phase 1 and 2 of the Meraki parser implementation."""

import pytest
from src.meraki_tools.meraki_parser import MerakiParser, ParseError


def test_parse_basic_modifier():
    """Test parsing a basic modifier definition."""
    parser = MerakiParser()
    config = "mod1 = lcmd + lalt"
    
    result = parser.parse_string(config)
    assert "mod1" in result["modifiers"]
    assert result["modifiers"]["mod1"]["keys"] == ["lcmd", "lalt"]
    assert result["modifiers"]["mod1"]["comments"] == []


def test_parse_basic_keybinding():
    """Test parsing a basic keybinding."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - m : open -a Mail.app"""
    
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["modifiers"] == ["mod1"]
    assert binding["key"] == "m"
    assert binding["command"] == "open -a Mail.app"


def test_parse_compound_modifier():
    """Test parsing a compound modifier keybinding."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 + shift - m : open -a Mail.app"""
    
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["modifiers"] == ["mod1", "shift"]
    assert binding["key"] == "m"
    assert binding["command"] == "open -a Mail.app"


def test_parse_multiple_compound_modifiers():
    """Test parsing multiple compound modifiers."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 + shift + ctrl - m : open -a Mail.app"""
    
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["modifiers"] == ["mod1", "shift", "ctrl"]
    assert binding["key"] == "m"
    assert binding["command"] == "open -a Mail.app"


def test_parse_group_keys():
    """Test parsing group syntax for keys."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - {h,j,k,l} : focus"""
    
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["modifiers"] == ["mod1"]
    assert binding["key"] == "h"  # First key in group
    assert binding["command"] == "focus"


def test_parse_group_modifiers():
    """Test parsing group syntax for modifiers."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 + {shift,ctrl} - m : open -a Mail.app"""
    
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["modifiers"] == ["mod1", "shift", "ctrl"]
    assert binding["key"] == "m"
    assert binding["command"] == "open -a Mail.app"


def test_parse_with_comments():
    """Test parsing with inline comments."""
    parser = MerakiParser()
    config = """# Main modifier
mod1 = lcmd + lalt  # Command + Option
mod1 + shift - m : open -a Mail.app  # Opens Mail"""
    
    result = parser.parse_string(config)
    assert len(result["comments"]) == 1
    assert "Main modifier" in result["comments"][0]
    assert "Command + Option" in result["modifiers"]["mod1"]["comments"][0]
    assert "Opens Mail" in result["keybindings"][0]["comments"][0]


def test_parse_quoted_command():
    """Test parsing a command with quoted arguments."""
    parser = MerakiParser()
    config = 'mod1 + shift - t : open -a "Terminal.app"'
    
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["command"] == 'open -a "Terminal.app"'


def test_parse_multiple_definitions():
    """Test parsing multiple definitions."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod2 = lshift + lctrl

mod1 + shift - m : open -a Mail.app
mod2 + ctrl - t : open -a Terminal.app"""
    
    result = parser.parse_string(config)
    assert len(result["modifiers"]) == 2
    assert len(result["keybindings"]) == 2


def test_error_invalid_modifier():
    """Test error on invalid modifier definition."""
    parser = MerakiParser()
    config = "mod1 = lcmd +"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected second key" in str(exc.value)


def test_error_invalid_compound_modifier():
    """Test error on invalid compound modifier."""
    parser = MerakiParser()
    config = "mod1 + + shift - k"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected modifier" in str(exc.value)


def test_error_missing_minus():
    """Test error on missing minus after compound modifier."""
    parser = MerakiParser()
    config = "mod1 + shift k"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected '-' after modifiers" in str(exc.value)


def test_error_empty_group():
    """Test error on empty group."""
    parser = MerakiParser()
    config = "mod1 - {} : command"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Empty group" in str(exc.value)


def test_error_unterminated_group():
    """Test error on unterminated group."""
    parser = MerakiParser()
    config = "mod1 - {h,j,k : command"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Unterminated group" in str(exc.value)


def test_error_missing_comma():
    """Test error on missing comma in group."""
    parser = MerakiParser()
    config = "mod1 - {h j k} : command"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected ',' between group items" in str(exc.value)


def test_error_invalid_keybinding():
    """Test error on invalid keybinding."""
    parser = MerakiParser()
    config = "mod1 - k"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected ':'" in str(exc.value)


def test_error_missing_command():
    """Test error on missing command."""
    parser = MerakiParser()
    config = "mod1 - k :"
    
    with pytest.raises(ParseError) as exc:
        parser.parse_string(config)
    assert "Expected command" in str(exc.value) 