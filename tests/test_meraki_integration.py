"""Integration tests for the complete Meraki toolchain."""
import pytest
import json
import os
from src.meraki_tools.meraki_parser import MerakiParser
from src.meraki_tools.meraki_validator import MerakiValidator
from src.meraki_tools.meraki_formatter import MerakiFormatter


def test_basic_app_launcher_pipeline():
    """Test complete pipeline for basic app launcher configuration."""
    # Input Meraki config
    config = """
    # Define modifiers
    mod1 = lcmd + lalt  # Main modifier
    
    # App launcher
    mod1 - a : open -a "Chrome"  # Browser
    mod1 - m : open -a "Mail"    # Email
    """
    
    # Phase 1: Parse
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify AST structure
    assert "modifiers" in ast
    assert "mod1" in ast["modifiers"]
    assert ast["modifiers"]["mod1"]["keys"] == ["lcmd", "lalt"]
    
    assert len(ast["keybindings"]) == 2
    assert ast["keybindings"][0]["key"] == "a"
    assert ast["keybindings"][1]["key"] == "m"
    
    # Phase 2: Validate
    validator = MerakiValidator()
    validation_result = validator.validate(ast)
    assert validation_result.is_valid
    assert len(validation_result.errors) == 0
    
    # Phase 3: Format (verify roundtrip)
    formatter = MerakiFormatter()
    formatted = formatter.format(ast)
    reparsed = parser.parse_string(formatted)
    assert ast == reparsed


def test_nested_layer_pipeline():
    """Test pipeline with nested layers and timeouts."""
    config = """
    mod1 = lcmd + lalt
    
    # Development tools
    mod1 - d [500ms] : {
        c : open -a "Chrome";
        v : open -a "Visual Studio Code";
    }
    """
    
    # Parse and verify AST
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    binding = ast["keybindings"][0]
    assert binding["timeout"] == 500
    assert len(binding["nested_bindings"]) == 2
    assert "c" in binding["nested_bindings"]
    assert "v" in binding["nested_bindings"]
    
    # Validate nested structure
    validator = MerakiValidator()
    validation_result = validator.validate(ast)
    assert validation_result.is_valid


def test_command_chain_pipeline():
    """Test pipeline with command chains."""
    config = """
    mod1 = lcmd + lalt
    
    # Launch communication apps
    mod1 - c : open -a Slack; open -a Discord
    """
    
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify command chain in AST
    binding = ast["keybindings"][0]
    assert "actions" in binding
    assert len(binding["actions"]) == 2
    assert binding["actions"][0]["command"] == "open -a Slack"
    assert binding["actions"][1]["command"] == "open -a Discord"


def test_group_syntax_pipeline():
    """Test pipeline with group syntax expansion."""
    config = """
    mod1 = lcmd + lalt
    
    # Browser shortcuts
    mod1 + { n, p } : open -a { "Chrome", "Safari" }
    """
    
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify group expansion
    assert len(ast["keybindings"]) == 2
    assert ast["keybindings"][0]["key"] == "n"
    assert ast["keybindings"][0]["action"] == 'open -a "Chrome"'
    assert ast["keybindings"][1]["key"] == "p"
    assert ast["keybindings"][1]["action"] == 'open -a "Safari"'


def test_error_handling_pipeline():
    """Test error handling through the pipeline."""
    # Test invalid modifier
    with pytest.raises(Exception):
        config = "mod1 = invalid + key"
        parser = MerakiParser()
        parser.parse_string(config)
    
    # Test undefined modifier
    config = """
    mod1 = lcmd + lalt
    mod2 - x : open -a Chrome  # mod2 not defined
    """
    parser = MerakiParser()
    ast = parser.parse_string(config)
    validator = MerakiValidator()
    validation_result = validator.validate(ast)
    assert not validation_result.is_valid
    assert any("undefined modifier" in str(err).lower() for err in validation_result.errors)
    
    # Test duplicate binding
    config = """
    mod1 = lcmd + lalt
    mod1 - x : open -a Chrome
    mod1 - x : open -a Safari  # Duplicate
    """
    parser = MerakiParser()
    ast = parser.parse_string(config)
    validator = MerakiValidator()
    validation_result = validator.validate(ast)
    assert not validation_result.is_valid
    assert any("duplicate" in str(err).lower() for err in validation_result.errors)


def test_activation_flags_pipeline():
    """Test pipeline with activation flags."""
    config = """
    mod1 = lcmd + lalt
    
    # Mouse button handling
    mod1 ~down : show_menu
    mod1 ~up : hide_menu
    mod1 ~down ~repeat : resize_window
    """
    
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify activation flags
    assert len(ast["keybindings"]) == 3
    assert ast["keybindings"][0]["activation_flags"] == ["down"]
    assert ast["keybindings"][1]["activation_flags"] == ["up"]
    assert ast["keybindings"][2]["activation_flags"] == ["down", "repeat"]


def test_compound_modifier_pipeline():
    """Test pipeline with compound modifiers."""
    config = """
    mod1 = lcmd + lalt
    mod2 = lshift + lctrl
    
    # Compound modifier usage
    mod2 + shift - n : create_space
    """
    
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify compound modifier structure
    binding = ast["keybindings"][0]
    assert binding["key_combination"] == "mod2 + shift"
    assert binding["key"] == "n"
    assert binding["action"] == "create_space"


def test_comments_preservation_pipeline():
    """Test comment preservation through the pipeline."""
    config = """
    # Main modifier definition
    mod1 = lcmd + lalt  # Command + Option
    
    @END
    This is a multi-line comment
    describing the next binding
    END
    mod1 - a : open -a Chrome  # Launch browser
    """
    
    parser = MerakiParser()
    ast = parser.parse_string(config)
    
    # Verify comment preservation
    assert "Command + Option" in ast["modifiers"]["mod1"]["comments"]
    assert "Launch browser" in ast["keybindings"][0]["comments"]
    
    # Format and verify comments remain
    formatter = MerakiFormatter()
    formatted = formatter.format(ast)
    assert "Command + Option" in formatted
    assert "Launch browser" in formatted
    assert "This is a multi-line comment" in formatted 