"""Tests for the lexical analysis stage of the parser.

These tests include 'guard rails' to prevent the lexer from becoming too complex
by taking on responsibilities that belong in later stages."""

import pytest
from meraki.parser import LexicalAnalyzer
from lark.lexer import Token


def test_single_tokens():
    """Test recognition of individual tokens."""
    lexer = LexicalAnalyzer()
    test_cases = [
        ('mod1', 'IDENTIFIER'),
        ('=', 'EQUALS'),
        ('+', 'PLUS'),
        ('-', 'MINUS'),
        (':', 'COLON'),
        (';', 'SEMICOLON'),
        ('~', 'TILDE'),
        ('{', 'LBRACE'),
        ('}', 'RBRACE'),
        ('[', 'LBRACKET'),
        (']', 'RBRACKET'),
        ('42', 'NUMBER'),
        ('"hello"', 'QUOTED_STRING'),
        ('# comment', 'COMMENT'),
        ('\n', 'NEWLINE'),
    ]
    
    for text, expected_type in test_cases:
        tokens = list(lexer.tokenize(text))
        assert len(tokens) == 1
        assert tokens[0].type == expected_type
        assert tokens[0].value == text


def test_token_positions():
    """Test that tokens preserve their line and column positions."""
    lexer = LexicalAnalyzer()
    input_text = """mod1 = lcmd
    mod2 = lalt"""
    
    tokens = list(lexer.tokenize(input_text))
    
    # First line tokens
    assert tokens[0].line == 1  # mod1
    assert tokens[0].column == 1
    assert tokens[1].line == 1  # =
    assert tokens[1].column == 6
    
    # Second line tokens
    assert tokens[4].line == 2  # mod2
    assert tokens[4].column == 5


def test_whitespace_handling():
    """Test that whitespace is properly ignored."""
    lexer = LexicalAnalyzer()
    input_text = "mod1    =     lcmd"
    
    tokens = list(lexer.tokenize(input_text))
    assert len(tokens) == 3
    assert [t.type for t in tokens] == ['IDENTIFIER', 'EQUALS', 'IDENTIFIER']


def test_comment_handling():
    """Test different types of comments."""
    lexer = LexicalAnalyzer()
    test_cases = [
        ('# standalone comment\n', ['COMMENT', 'NEWLINE']),
        ('mod1 # inline comment\n', ['IDENTIFIER', 'COMMENT', 'NEWLINE']),
        ('# comment with # inside\n', ['COMMENT', 'NEWLINE']),
    ]
    
    for text, expected_types in test_cases:
        tokens = list(lexer.tokenize(text))
        assert [t.type for t in tokens] == expected_types


def test_string_handling():
    """Test string token handling."""
    lexer = LexicalAnalyzer()
    test_cases = [
        ('"simple string"', ['QUOTED_STRING']),
        ('"string with spaces"', ['QUOTED_STRING']),
        ('"string with #"', ['QUOTED_STRING']),
        ('"string with \\"quote\\""', ['QUOTED_STRING']),
    ]
    
    for text, expected_types in test_cases:
        tokens = list(lexer.tokenize(text))
        assert [t.type for t in tokens] == expected_types


def test_identifier_handling():
    """Test identifier token handling."""
    lexer = LexicalAnalyzer()
    test_cases = [
        ('mod1', True),
        ('lcmd', True),
        ('Safari', True),
        ('1mod', False),  # Can't start with number
        ('mod-1', False),  # Can't contain hyphen
        ('mod_1', True),   # Can contain underscore
        ('MOD1', True),    # Can be uppercase
    ]
    
    for text, should_match in test_cases:
        tokens = list(lexer.tokenize(text))
        if should_match:
            assert len(tokens) == 1
            assert tokens[0].type == 'IDENTIFIER'
        else:
            with pytest.raises(Exception):
                list(lexer.tokenize(text))


def test_error_handling():
    """Test lexer error handling."""
    lexer = LexicalAnalyzer()
    invalid_inputs = [
        '@',        # Invalid character
        '"unterminated string',  # Unterminated string
        '123.456',  # No floating point numbers
        '`backtick`',  # No backticks
    ]
    
    for text in invalid_inputs:
        with pytest.raises(Exception):
            list(lexer.tokenize(text))


def test_lexer_should_not_track_indentation_state():
    """Guard Rail: Lexer should not track or manage indentation state.
    
    The lexer should only recognize whitespace and newlines as individual tokens.
    Indentation structure should be handled by the parser."""
    lexer = LexicalAnalyzer()
    input_text = """
    mod1 = lcmd
        nested = lalt
    """
    
    tokens = list(lexer.tokenize(input_text))
    
    # The lexer should only produce basic tokens
    # It should not create special INDENT/DEDENT tokens
    for token in tokens:
        assert token.type not in ['INDENT', 'DEDENT']
        # No token should have indentation level information
        assert not hasattr(token, 'indent_level')


def test_lexer_should_not_handle_multiline_structures():
    """Guard Rail: Lexer should not handle multi-line structures.
    
    The lexer should treat each line independently, producing only basic tokens.
    Multi-line structures should be handled by the parser."""
    lexer = LexicalAnalyzer()
    input_text = """mod1 - l : {
        h : open -a Safari;
        t : open -a Terminal;
    }"""
    
    tokens = list(lexer.tokenize(input_text))
    
    # The lexer should not:
    # 1. Track brace matching
    # 2. Group tokens by block structure
    # 3. Handle special block-level formatting
    for token in tokens:
        # No token should have block level or nesting information
        assert not hasattr(token, 'block_level')
        assert not hasattr(token, 'in_block')
        assert not hasattr(token, 'block_type')


def test_lexer_should_not_relate_tokens():
    """Guard Rail: Lexer should not make decisions about token relationships.
    
    The lexer should treat each token independently. Token relationships
    should be handled by the parser."""
    lexer = LexicalAnalyzer()
    input_text = "mod1 = lcmd + lalt"
    
    tokens = list(lexer.tokenize(input_text))
    
    # The lexer should not:
    # 1. Group related tokens
    # 2. Track operator precedence
    # 3. Associate modifiers with their targets
    for token in tokens:
        # No token should have relationship information
        assert not hasattr(token, 'related_to')
        assert not hasattr(token, 'precedence')
        assert not hasattr(token, 'modifies')


def test_lexer_should_be_stateless():
    """Guard Rail: Lexer should not maintain state between tokenization calls.
    
    Each call to tokenize should be independent."""
    lexer = LexicalAnalyzer()
    
    # First tokenization
    tokens1 = list(lexer.tokenize("mod1 = lcmd"))
    
    # Second tokenization should be completely independent
    tokens2 = list(lexer.tokenize("mod2 = lalt"))
    
    # The lexer should not:
    # 1. Remember previous tokens
    # 2. Track running state
    # 3. Maintain context between calls
    assert not hasattr(lexer, 'previous_tokens')
    assert not hasattr(lexer, 'state')
    assert not hasattr(lexer, 'context')


def test_comprehensive_positions():
    """Test exact positions for all token types."""
    lexer = LexicalAnalyzer()
    input_text = """mod1 = lcmd  # Comment
    "string" + 42"""
    
    tokens = list(lexer.tokenize(input_text))
    
    # First line
    assert tokens[0].line == 1 and tokens[0].column == 1  # mod1
    assert tokens[1].line == 1 and tokens[1].column == 6  # =
    assert tokens[2].line == 1 and tokens[2].column == 8  # lcmd
    assert tokens[3].line == 1 and tokens[3].column == 14  # Comment
    
    # Second line
    assert tokens[5].line == 2 and tokens[5].column == 5  # string
    assert tokens[6].line == 2 and tokens[6].column == 13  # +
    assert tokens[7].line == 2 and tokens[7].column == 15  # 42


def test_escaped_positions():
    """Test positions after escaped characters."""
    lexer = LexicalAnalyzer()
    input_text = '"escaped \\"quote\\" here"'
    
    tokens = list(lexer.tokenize(input_text))
    assert len(tokens) == 1
    assert tokens[0].column == 1
    assert len(tokens[0].value) == len(input_text)


def test_newline_formats():
    """Test positions with different newline formats."""
    lexer = LexicalAnalyzer()
    input_text = "a\nb\r\nc\rd"
    
    tokens = list(lexer.tokenize(input_text))
    assert tokens[0].line == 1  # a
    assert tokens[2].line == 2  # b
    assert tokens[4].line == 3  # c
    assert tokens[6].line == 4  # d


def test_unicode_whitespace():
    """Test handling of Unicode whitespace characters."""
    lexer = LexicalAnalyzer()
    # Include various Unicode whitespace characters
    input_text = "mod1\u2002=\u2003lcmd"  # \u2002 is en space, \u2003 is em space
    
    tokens = list(lexer.tokenize(input_text))
    assert len(tokens) == 3
    assert [t.type for t in tokens] == ['IDENTIFIER', 'EQUALS', 'IDENTIFIER']


def test_mixed_whitespace():
    """Test handling of mixed whitespace."""
    lexer = LexicalAnalyzer()
    input_text = "mod1\t \t=  \t  lcmd"
    
    tokens = list(lexer.tokenize(input_text))
    assert len(tokens) == 3
    assert [t.type for t in tokens] == ['IDENTIFIER', 'EQUALS', 'IDENTIFIER']


def test_error_recovery():
    """Test error recovery and position reporting."""
    lexer = LexicalAnalyzer()
    input_text = "mod1 @ lcmd\nmod2 = lalt"
    
    with pytest.raises(Exception) as exc:
        tokens = list(lexer.tokenize(input_text))
        assert "line 1" in str(exc.value)
        assert "column 6" in str(exc.value)


def test_max_token_length():
    """Test handling of maximum token length."""
    lexer = LexicalAnalyzer()
    long_identifier = "a" * 1000
    
    with pytest.raises(Exception) as exc:
        tokens = list(lexer.tokenize(long_identifier))
        assert "maximum token length" in str(exc.value).lower()


def test_large_input():
    """Test performance with large input."""
    lexer = LexicalAnalyzer()
    # Create a large but valid input
    large_input = "\n".join([f"mod{i} = key{i}" for i in range(1000)])
    
    tokens = list(lexer.tokenize(large_input))
    assert len(tokens) > 3000  # Each line should produce at least 3 tokens


def test_pathological_input():
    """Test performance with pathological input patterns."""
    lexer = LexicalAnalyzer()
    # Create input with many repeated characters
    input_text = "+" * 100 + "\n" + "#" * 100
    
    tokens = list(lexer.tokenize(input_text))
    assert len(tokens) == 102  # 100 plus signs + newline + 1 comment