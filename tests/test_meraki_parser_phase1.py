"""Tests for Phase 1 of the Meraki parser implementation."""

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
    assert binding["modifier"] == "mod1"
    assert binding["key"] == "m"
    assert binding["command"] == "open -a Mail.app"


def test_parse_with_comments():
    """Test parsing with inline comments."""
    parser = MerakiParser()
    config = """# Main modifier
mod1 = lcmd + lalt  # Command + Option
mod1 - m : open -a Mail.app  # Opens Mail"""
    
    result = parser.parse_string(config)
    assert len(result["comments"]) == 1
    assert "Main modifier" in result["comments"][0]
    assert "Command + Option" in result["modifiers"]["mod1"]["comments"][0]
    assert "Opens Mail" in result["keybindings"][0]["comments"][0]


def test_parse_quoted_command():
    """Test parsing a command with quoted arguments."""
    parser = MerakiParser()
    config = 'mod1 - t : open -a "Terminal.app"'
    
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["command"] == 'open -a "Terminal.app"'


def test_parse_multiple_definitions():
    """Test parsing multiple definitions."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod2 = lshift + lctrl

mod1 - m : open -a Mail.app
mod2 - t : open -a Terminal.app"""
    
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