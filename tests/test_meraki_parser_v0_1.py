"""Tests for Meraki Parser v0.1 features."""
import pytest
from src.meraki_tools.meraki_parser import MerakiParser


def test_parse_command_chains():
    """Test parsing multiple commands in sequence."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - x : open -a Slack; open -a Discord"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["actions"] == [
        {"command": "open -a Slack"},
        {"command": "open -a Discord"}
    ]


def test_parse_multiline_comments():
    """Test parsing multi-line comments with @END markers."""
    parser = MerakiParser()
    config = """@END
This is a multi-line comment
describing the next binding
END
mod1 = lcmd + lalt"""
    result = parser.parse_string(config)
    assert result["modifiers"]["mod1"]["comments"][0].startswith("This is")


def test_parse_modifier_only_keybinds():
    """Test parsing modifier-only keybinds."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 ~down : show_switcher
mod1 ~up : hide_switcher"""
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 2
    assert result["keybindings"][0]["key"] is None
    assert result["keybindings"][0]["activation_flags"] == ["down"]


def test_parse_group_expansion():
    """Test parsing group syntax with expansion."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - d : {  # Development tools
    c : open -a Chrome;
    p : open -a "PyCharm CE";
    i : open -a iTerm;
}"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["nested_bindings"] == {
        "c": {"action": "open -a Chrome", "nested_bindings": None},
        "p": {"action": 'open -a "PyCharm CE"', "nested_bindings": None},
        "i": {"action": "open -a iTerm", "nested_bindings": None}
    }


def test_parse_compound_modifiers():
    """Test parsing compound modifiers."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod2 = lshift + lctrl
mod2 + shift - n : open -a Notes"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["key_combination"] == "mod2 + shift"
    assert binding["key"] == "n"
    assert binding["action"] == "open -a Notes"


def test_parse_activation_flags():
    """Test parsing activation flags."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - x ~down : show_menu
mod1 - x ~up : hide_menu
mod1 - y ~down ~repeat : resize_window"""
    result = parser.parse_string(config)
    bindings = result["keybindings"]
    assert bindings[0]["activation_flags"] == ["down"]
    assert bindings[1]["activation_flags"] == ["up"]
    assert bindings[2]["activation_flags"] == ["down", "repeat"]


# Error Cases
def test_invalid_compound_modifier():
    """Test invalid compound modifier syntax."""
    parser = MerakiParser()
    config = "mod1 + + shift - x : command"
    with pytest.raises(Exception):
        parser.parse_string(config)


def test_invalid_group_syntax():
    """Test invalid group syntax."""
    parser = MerakiParser()
    config = "mod1 + { a, b, } : { cmd1, cmd2 }"
    with pytest.raises(Exception):
        parser.parse_string(config)


def test_invalid_activation_flags():
    """Test invalid activation flag combinations."""
    parser = MerakiParser()
    config = "mod1 ~invalid : command"
    with pytest.raises(Exception):
        parser.parse_string(config)


# Edge Cases
def test_empty_group():
    """Test empty group syntax."""
    parser = MerakiParser()
    config = "mod1 + {} : {}"
    with pytest.raises(Exception):
        parser.parse_string(config)


def test_nested_groups():
    """Test nested group syntax (should fail)."""
    parser = MerakiParser()
    config = "mod1 + { a, {b, c} } : command"
    with pytest.raises(Exception):
        parser.parse_string(config)


def test_mixed_activation_flags():
    """Test mixing up/down flags (should fail)."""
    parser = MerakiParser()
    config = "mod1 ~up ~down : command"
    with pytest.raises(Exception):
        parser.parse_string(config)


# Complex Cases
def test_compound_modifier_with_group():
    """Test compound modifier with group syntax."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod2 = lshift + lctrl
mod2 + shift + { a, b, c } : open -a { "App1", "App2", "App3" }"""
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 3
    for binding in result["keybindings"]:
        assert binding["key_combination"] == "mod2 + shift"


def test_activation_flags_with_timeout():
    """Test activation flags with timeout."""
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 ~down [500ms] : {
    a : command1;
    b : command2;
}"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["activation_flags"] == ["down"]
    assert binding["timeout"] == 500
    assert binding["nested_bindings"] is not None 