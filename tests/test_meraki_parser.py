import pytest
from src.meraki_tools.meraki_parser import MerakiParser

def test_parse_basic_modifier():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
"""
    result = parser.parse_string(config)
    assert "modifiers" in result
    assert "mod1" in result["modifiers"]
    assert result["modifiers"]["mod1"]["keys"] == ["lcmd", "lalt"]

def test_parse_basic_keybinding():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - m : open -a Mail.app
"""
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["key_combination"] == "mod1"
    assert binding["key"] == "m"
    assert binding["action"] == "open -a Mail.app"

def test_parse_with_comments():
    parser = MerakiParser()
    config = """# Main modifier
mod1 = lcmd + lalt  # Command + Option
"""
    result = parser.parse_string(config)
    assert "mod1" in result["modifiers"]
    assert "# Command + Option" in result["modifiers"]["mod1"]["comments"]

def test_parse_with_timeout():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - l [500ms] : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["timeout"] == 500
    assert binding["nested_bindings"] is not None
    assert "h" in binding["nested_bindings"]
    assert "t" in binding["nested_bindings"]
    assert binding["nested_bindings"]["h"]["action"] == "open -a Safari"
    assert binding["nested_bindings"]["t"]["action"] == "open -a Terminal"

def test_parse_deep_nested_bindings():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - l : {
    h : {
        s : open -a Safari;
        c : open -a Chrome;
    }
    t : open -a Terminal;
}"""
    result = parser.parse_string(config)
    assert len(result["keybindings"]) == 1
    binding = result["keybindings"][0]
    assert binding["nested_bindings"] is not None
    assert "h" in binding["nested_bindings"]
    assert "t" in binding["nested_bindings"]
    
    h_binding = binding["nested_bindings"]["h"]
    assert h_binding["nested_bindings"] is not None
    assert "s" in h_binding["nested_bindings"]
    assert "c" in h_binding["nested_bindings"]
    assert h_binding["nested_bindings"]["s"]["action"] == "open -a Safari"
    assert h_binding["nested_bindings"]["c"]["action"] == "open -a Chrome"
    
    t_binding = binding["nested_bindings"]["t"]
    assert t_binding["action"] == "open -a Terminal"
    assert t_binding["nested_bindings"] is None 

def test_parse_leader_key_with_custom_timeout():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - l [750ms] : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["timeout"] == 750
    assert binding["nested_bindings"] is not None

def test_parse_leader_key_with_default_timeout():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - l : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    assert binding["timeout"] == 500  # Default timeout
    assert binding["nested_bindings"] is not None

def test_parse_hierarchical_chains():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 - a : {
    f : {
        n : open -a "Finder";
        s : open -a "System Settings";
    }
    t : {
        v : open -a "Visual Studio Code";
        s : open -a "Sublime Text";
    }
}"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    
    # Check first level
    assert binding["key"] == "a"
    assert "f" in binding["nested_bindings"]
    assert "t" in binding["nested_bindings"]
    
    # Check second level under 'f'
    f_bindings = binding["nested_bindings"]["f"]["nested_bindings"]
    assert f_bindings["n"]["action"] == 'open -a "Finder"'
    assert f_bindings["s"]["action"] == 'open -a "System Settings"'
    
    # Check second level under 't'
    t_bindings = binding["nested_bindings"]["t"]["nested_bindings"]
    assert t_bindings["v"]["action"] == 'open -a "Visual Studio Code"'
    assert t_bindings["s"]["action"] == 'open -a "Sublime Text"'

def test_parse_group_syntax():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod1 + { c, f, m } : open -a { "Chrome", "Finder", "Mail" }"""
    result = parser.parse_string(config)
    bindings = result["keybindings"]
    
    assert len(bindings) == 3
    assert bindings[0]["key"] == "c"
    assert bindings[0]["action"] == 'open -a "Chrome"'
    assert bindings[1]["key"] == "f"
    assert bindings[1]["action"] == 'open -a "Finder"'
    assert bindings[2]["key"] == "m"
    assert bindings[2]["action"] == 'open -a "Mail"'

def test_parse_activation_flags():
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

def test_parse_compound_modifiers():
    parser = MerakiParser()
    config = """mod1 = lcmd + lalt
mod2 = lshift + lctrl
mod2 + shift - n : create_space"""
    result = parser.parse_string(config)
    binding = result["keybindings"][0]
    
    assert binding["key_combination"] == "mod2 + shift"
    assert binding["key"] == "n"
    assert binding["action"] == "create_space" 