import pytest
import logging
from src.parser.meraki_parser import (
    MerakiParser,
    CommentType,
    Comment,
    ParseError
)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_line_comment_extraction():
    parser = MerakiParser()
    content = """# Define modifiers
mod1 = lcmd + lalt
# App launcher with timeout"""

    comments, clean_content = parser.extract_comments(content)
    
    assert len(comments) == 2
    assert comments[0].type == CommentType.LINE
    assert comments[0].text == "Define modifiers"
    assert comments[0].line_number == 1
    
    assert comments[1].type == CommentType.LINE
    assert comments[1].text == "App launcher with timeout"
    assert comments[1].line_number == 3
    
    expected_clean = "\nmod1 = lcmd + lalt\n"
    assert clean_content == expected_clean

def test_inline_comment_extraction():
    parser = MerakiParser()
    content = "mod1 = lcmd + lalt  # Main modifier"
    
    comments, clean_content = parser.extract_comments(content)
    
    assert len(comments) == 1
    assert comments[0].type == CommentType.INLINE
    assert comments[0].text == "Main modifier"
    assert comments[0].line_number == 1
    assert comments[0].associated_code_line == 1
    
    assert clean_content.strip() == "mod1 = lcmd + lalt"

def test_multiline_comment_extraction():
    parser = MerakiParser()
    content = """mod1 = lcmd + lalt
@END
This is a multiline
comment block
END
mod2 = lshift + lctrl"""

    comments, clean_content = parser.extract_comments(content)
    
    assert len(comments) == 1
    assert comments[0].type == CommentType.MULTILINE
    assert comments[0].text == "This is a multiline\ncomment block"
    assert comments[0].line_number == 2
    assert comments[0].end_line == 5
    
    expected_clean = "mod1 = lcmd + lalt\n\n\n\n\nmod2 = lshift + lctrl"
    assert clean_content == expected_clean

def test_mixed_comments_extraction():
    parser = MerakiParser()
    content = """# Configuration file
mod1 = lcmd + lalt  # Main modifier
@END
Documentation for
the next section
END
mod2 = lshift + lctrl"""

    comments, clean_content = parser.extract_comments(content)
    
    assert len(comments) == 3
    # Line comment
    assert comments[0].type == CommentType.LINE
    assert comments[0].text == "Configuration file"
    assert comments[0].line_number == 1
    
    # Inline comment
    assert comments[1].type == CommentType.INLINE
    assert comments[1].text == "Main modifier"
    assert comments[1].line_number == 2
    
    # Multiline comment
    assert comments[2].type == CommentType.MULTILINE
    assert comments[2].text == "Documentation for\nthe next section"
    assert comments[2].line_number == 3
    
    expected_clean = "\nmod1 = lcmd + lalt\n\n\n\n\nmod2 = lshift + lctrl"
    assert clean_content == expected_clean

def test_parse_with_comments():
    logger.debug("Running test_parse_with_comments")
    parser = MerakiParser()
    content = """# Main modifier
mod1 = lcmd + lalt  # Command + Option
"""
    logger.debug("Content:\n%s", content)
    result = parser.parse(content)
    logger.debug("Result: %s", result)
    assert "mod1" in result.modifiers
    mod1 = result.modifiers["mod1"]
    logger.debug("mod1: %s", mod1)
    logger.debug("mod1 comments: %s", mod1.comments)
    assert len(mod1.comments) == 2
    assert mod1.comments[0].type == CommentType.LINE
    assert mod1.comments[0].text == "Main modifier"
    assert mod1.comments[1].type == CommentType.INLINE
    assert mod1.comments[1].text == "Command + Option"

def test_parse_basic_modifier():
    parser = MerakiParser()
    content = "mod1 = lcmd + lalt"
    result = parser.parse(content)
    assert "mod1" in result.modifiers
    mod1 = result.modifiers["mod1"]
    assert mod1.name == "mod1"
    assert mod1.keys == ["lcmd", "lalt"]

def test_parse_basic_keybinding():
    parser = MerakiParser()
    content = """mod1 = lcmd + lalt
mod1 - m : open -a Mail.app
"""
    result = parser.parse(content)
    assert len(result.keybindings) == 1
    binding = result.keybindings[0]
    assert binding.key_combination == "mod1"
    assert binding.key == "m"
    assert binding.action.command == "open -a Mail.app"

def test_parse_with_timeout():
    parser = MerakiParser()
    content = """mod1 = lcmd + lalt
mod1 - l [500ms] : {
    h : open -a Safari;
    t : open -a Terminal;
}"""
    result = parser.parse(content)
    assert len(result.keybindings) == 1
    binding = result.keybindings[0]
    assert binding.key_combination == "mod1"
    assert binding.key == "l"
    assert binding.timeout == 500
    assert binding.nested_bindings is not None
    assert "h" in binding.nested_bindings
    assert "t" in binding.nested_bindings
    assert binding.nested_bindings["h"].action.command == "open -a Safari"
    assert binding.nested_bindings["t"].action.command == "open -a Terminal"

def test_parse_compound_modifiers():
    parser = MerakiParser()
    content = """mod1 = lcmd + lalt
mod2 = lshift + lctrl
mod2 + shift - n : create_space"""
    result = parser.parse(content)
    binding = result.keybindings[0]
    assert binding.key_combination == "mod2 shift"
    assert binding.key == "n"
    assert binding.action.command == "create_space" 