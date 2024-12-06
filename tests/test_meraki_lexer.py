"""Tests for the Meraki lexical analyzer.

This module contains comprehensive tests for the lexical analyzer, including
edge cases and error conditions.
"""

import pytest
from src.meraki_tools.meraki_lexer import (
    MerakiLexer,
    TokenType,
    Token,
    LexerError,
    create_lexer
)


def test_basic_tokens():
    """Test recognition of basic tokens."""
    lexer = create_lexer()
    text = "mod1 = lcmd + lalt"
    tokens = list(lexer.tokenize(text))
    
    expected = [
        Token(TokenType.IDENTIFIER, "mod1", 1, 1),
        Token(TokenType.EQUALS, "=", 1, 6),
        Token(TokenType.IDENTIFIER, "lcmd", 1, 8),
        Token(TokenType.PLUS, "+", 1, 13),
        Token(TokenType.IDENTIFIER, "lalt", 1, 15),
        Token(TokenType.EOF, "", 1, 19)
    ]
    
    assert len(tokens) == len(expected)
    for actual, expected in zip(tokens, expected):
        assert actual.type == expected.type
        assert actual.value == expected.value
        assert actual.line == expected.line
        assert actual.column == expected.column


def test_comments():
    """Test handling of comments."""
    lexer = create_lexer()
    text = """# Main modifier
mod1 = lcmd + lalt  # Command + Option"""
    
    tokens = list(lexer.tokenize(text))
    
    assert tokens[0].type == TokenType.COMMENT
    assert tokens[0].value == "# Main modifier"
    assert tokens[-2].type == TokenType.COMMENT
    assert tokens[-2].value == "# Command + Option"


def test_multiline_comments():
    """Test handling of multi-line comments."""
    lexer = create_lexer()
    text = """@END
This is a multi-line
comment block
END
mod1 = lcmd + lalt"""
    
    tokens = list(lexer.tokenize(text))
    
    assert tokens[0].type == TokenType.ML_START
    assert tokens[1].type == TokenType.ML_END
    assert tokens[2].type == TokenType.IDENTIFIER


def test_string_literals():
    """Test handling of quoted strings."""
    lexer = create_lexer()
    text = 'mod1 - m : "open -a Mail.app"'
    
    tokens = list(lexer.tokenize(text))
    
    assert any(
        t.type == TokenType.STRING and t.value == '"open -a Mail.app"'
        for t in tokens
    )


def test_command_chains():
    """Test handling of command chains with semicolons."""
    lexer = create_lexer()
    text = 'mod1 - m : open -a Mail.app; open -a Safari'
    
    tokens = list(lexer.tokenize(text))
    
    assert any(t.type == TokenType.SEMICOLON for t in tokens)


def test_group_syntax():
    """Test handling of group syntax with braces."""
    lexer = create_lexer()
    text = 'mod1 + { c, f, m } : open -a { "Chrome", "Finder", "Mail" }'
    
    tokens = list(lexer.tokenize(text))
    
    # Check for balanced braces
    lbraces = sum(1 for t in tokens if t.type == TokenType.LBRACE)
    rbraces = sum(1 for t in tokens if t.type == TokenType.RBRACE)
    assert lbraces == rbraces
    
    # Check for commas
    assert any(t.type == TokenType.COMMA for t in tokens)


def test_activation_flags():
    """Test handling of activation flags."""
    lexer = create_lexer()
    text = 'mod1 - x ~down ~repeat : command'
    
    tokens = list(lexer.tokenize(text))
    
    assert sum(1 for t in tokens if t.type == TokenType.TILDE) == 2
    assert any(
        t.type == TokenType.IDENTIFIER and t.value == "down"
        for t in tokens
    )
    assert any(
        t.type == TokenType.IDENTIFIER and t.value == "repeat"
        for t in tokens
    )


def test_timeout_syntax():
    """Test handling of timeout syntax."""
    lexer = create_lexer()
    text = 'mod1 - l [500ms] : command'
    
    tokens = list(lexer.tokenize(text))
    
    assert any(t.type == TokenType.LBRACKET for t in tokens)
    assert any(t.type == TokenType.NUMBER and t.value == "500" for t in tokens)
    assert any(t.type == TokenType.RBRACKET for t in tokens)


def test_invalid_character():
    """Test handling of invalid characters."""
    lexer = create_lexer()
    text = 'mod1 = lcmd $ lalt'
    
    with pytest.raises(LexerError) as exc:
        list(lexer.tokenize(text))
    
    assert "Invalid character: $" in str(exc.value)


def test_line_number_tracking():
    """Test tracking of line numbers."""
    lexer = create_lexer()
    text = """mod1 = lcmd + lalt
mod2 = lshift + lctrl
mod3 - m : command"""
    
    tokens = [t for t in lexer.tokenize(text) if t.type != TokenType.NEWLINE]
    
    # First line tokens
    first_line = [t for t in tokens if t.value in ["mod1", "lcmd", "lalt"]]
    assert all(t.line == 1 for t in first_line), f"First line tokens: {first_line}"
    
    # Second line tokens
    second_line = [t for t in tokens if t.value in ["mod2", "lshift", "lctrl"]]
    assert all(t.line == 2 for t in second_line), f"Second line tokens: {second_line}"
    
    # Third line tokens
    third_line = [t for t in tokens if t.value in ["mod3", "m", "command"]]
    assert all(t.line == 3 for t in third_line), f"Third line tokens: {third_line}"


def test_empty_input():
    """Test handling of empty input."""
    lexer = create_lexer()
    tokens = list(lexer.tokenize(""))
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_whitespace_only():
    """Test handling of whitespace-only input."""
    lexer = create_lexer()
    tokens = list(lexer.tokenize("  \t  \n  \t  "))
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_nested_multiline_comments():
    """Test handling of nested multi-line comments."""
    lexer = create_lexer()
    text = """@END
First level
@END
Second level
END
Still in first level
END
mod1 = lcmd + lalt"""
    
    tokens = list(lexer.tokenize(text))
    assert tokens[-6].type == TokenType.IDENTIFIER
    assert tokens[-6].value == "mod1"


def test_invalid_timeout():
    """Test handling of invalid timeout syntax."""
    lexer = create_lexer()
    text = 'mod1 - l [500] : command'  # Missing 'ms'
    
    with pytest.raises(LexerError) as exc:
        list(lexer.tokenize(text))
    assert "Invalid timeout" in str(exc.value)


def test_unterminated_string():
    """Test handling of unterminated string literals."""
    lexer = create_lexer()
    text = 'mod1 - m : "unterminated string'
    
    with pytest.raises(LexerError) as exc:
        list(lexer.tokenize(text))
    assert "Unterminated string" in str(exc.value)


def test_unterminated_multiline_comment():
    """Test handling of unterminated multi-line comments."""
    lexer = create_lexer()
    text = """@END
This comment is never terminated
mod1 = lcmd + lalt"""
    
    with pytest.raises(LexerError) as exc:
        list(lexer.tokenize(text))
    assert "Unterminated multi-line comment" in str(exc.value)


def test_mixed_whitespace():
    """Test handling of mixed whitespace characters."""
    lexer = create_lexer()
    text = "mod1\t=\tlcmd\t+\tlalt"
    tokens = list(lexer.tokenize(text))
    
    assert len([t for t in tokens if t.type != TokenType.EOF]) == 5
    assert all(t.type == TokenType.IDENTIFIER for t in tokens[::2][:-1])


def test_consecutive_operators():
    """Test handling of consecutive operators."""
    lexer = create_lexer()
    text = "mod1++mod2"  # Invalid but should tokenize
    
    tokens = list(lexer.tokenize(text))
    assert len([t for t in tokens if t.type == TokenType.PLUS]) == 2


def test_max_identifier_length():
    """Test handling of very long identifiers."""
    lexer = create_lexer()
    long_id = "a" + "b" * 100
    
    with pytest.raises(LexerError) as exc:
        list(lexer.tokenize(long_id))
    assert "Identifier too long" in str(exc.value) 