import pytest
from meraki.parser import parse_config

def test_empty_comment() -> None:
    """Test parsing of an empty comment line."""
    config = "#"
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0] == "#"

def test_whitespace_before_comment() -> None:
    """Test parsing of comments with leading whitespace."""
    config = "    # Comment with space"
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0].strip() == "# Comment with space"

def test_special_chars_in_comment() -> None:
    """Test parsing of comments with special characters."""
    config = "# Comment with {brackets} and (parens) and [squares]"
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0] == "# Comment with {brackets} and (parens) and [squares]"

def test_multiple_hashes() -> None:
    """Test parsing of comments with multiple hash symbols."""
    config = "## Double hash comment"
    parsed = parse_config(config)
    assert len(parsed.comments) == 1
    assert parsed.comments[0] == "## Double hash comment" 