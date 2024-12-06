import pytest
from src.meraki_tools.meraki_formatter import MerakiFormatter, FormattingOptions

def test_format_modifier_definition():
    formatter = MerakiFormatter()
    input_text = """mod1=lcmd+lalt
mod2   =    lshift   +   lctrl"""
    
    expected = """mod1 = lcmd + lalt
mod2 = lshift + lctrl"""
    
    assert formatter.format_string(input_text) == expected

def test_format_keybinding():
    formatter = MerakiFormatter()
    input_text = """mod1-m:open -a Mail.app
mod1   -    l   :   open -a Safari"""
    
    expected = """mod1 - m : open -a Mail.app
mod1 - l : open -a Safari"""
    
    assert formatter.format_string(input_text) == expected

def test_format_with_comments():
    formatter = MerakiFormatter()
    input_text = """# Main modifier
mod1 = lcmd + lalt  # Command + Option
mod1 - m : open -a Mail.app  # Opens Mail"""
    
    expected = """# Main modifier
mod1 = lcmd + lalt                      # Command + Option
mod1 - m : open -a Mail.app             # Opens Mail"""
    
    assert formatter.format_string(input_text) == expected

def test_format_nested_blocks():
    formatter = MerakiFormatter()
    input_text = """mod1 - l : {
h : open -a Safari;
t:open -a Terminal;
}"""
    
    expected = """mod1 - l : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    
    assert formatter.format_string(input_text) == expected

def test_format_with_custom_options():
    options = FormattingOptions(
        indent_size=2,
        max_line_length=60,
        align_comments=False
    )
    formatter = MerakiFormatter(options)
    
    input_text = """mod1 - l : {
h : open -a Safari;  # Web browser
t:open -a Terminal;  # Terminal
}"""
    
    expected = """mod1 - l : {
  h : open -a Safari;  # Web browser
  t : open -a Terminal;  # Terminal
}"""
    
    assert formatter.format_string(input_text) == expected

def test_format_leader_key_with_timeout():
    formatter = MerakiFormatter()
    input_text = """mod1-l[500ms]:{
    h:open -a Safari;
    t:open -a Terminal;
}"""
    
    expected = """mod1 - l [500ms] : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    
    assert formatter.format_string(input_text) == expected

def test_format_hierarchical_chains():
    formatter = MerakiFormatter()
    input_text = """mod1-a:{
f:{
    n:open -a "Finder";
    s:open -a "System Settings";
}
t:{
    v:open -a "Visual Studio Code";
    s:open -a "Sublime Text";
}
}"""
    
    expected = """mod1 - a : {
    f : {
        n : open -a "Finder";
        s : open -a "System Settings";
    }
    t : {
        v : open -a "Visual Studio Code";
        s : open -a "Sublime Text";
    }
}"""
    
    assert formatter.format_string(input_text) == expected

def test_format_group_syntax():
    formatter = MerakiFormatter()
    input_text = """mod1+{c,f,m}:open -a{"Chrome","Finder","Mail"}"""
    
    expected = """mod1 + { c, f, m } : open -a { "Chrome", "Finder", "Mail" }"""
    
    assert formatter.format_string(input_text) == expected

def test_format_activation_flags():
    formatter = MerakiFormatter()
    input_text = """mod1-x~down:show_menu
mod1-x~up:hide_menu
mod1-y~down~repeat:resize_window"""
    
    expected = """mod1 - x ~down : show_menu
mod1 - x ~up : hide_menu
mod1 - y ~down ~repeat : resize_window"""
    
    assert formatter.format_string(input_text) == expected 