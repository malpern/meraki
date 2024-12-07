"""Tests for the structural analysis stage of the parser."""

import pytest
from meraki.parser import StructuralAnalyzer

def test_modifier_structure():
    """Test parsing of modifier definitions."""
    analyzer = StructuralAnalyzer()
    input_text = """
    mod1 = lcmd + lalt  # Primary modifier
    mod2 = lshift + lctrl
    """
    tree = analyzer.parse(input_text)
    
    statements = [s for s in tree['statements'] if s.get('type') == 'modifier']
    assert len(statements) == 2
    
    mod1 = next(s for s in statements if s['name'] == 'mod1')
    assert mod1['value'] == ['lcmd', 'lalt']
    assert mod1['comment'] == "# Primary modifier"

def test_simple_binding_structure():
    """Test parsing of simple keybindings."""
    analyzer = StructuralAnalyzer()
    input_text = "mod1 - m : open -a Mail.app"
    tree = analyzer.parse(input_text)
    
    bindings = [s for s in tree['statements'] if s.get('type') == 'binding']
    assert len(bindings) == 1
    assert bindings[0]['key'] == 'm'
    assert 'mod1' in bindings[0]['modifiers']

def test_leader_block_structure():
    """Test parsing of leader blocks."""
    analyzer = StructuralAnalyzer()
    input_text = """
    mod1 - l : {
        h : open -a Safari;
        t : open -a Terminal;
    }
    """
    tree = analyzer.parse(input_text)
    
    bindings = [s for s in tree['statements'] if s.get('type') == 'binding']
    assert len(bindings) == 1
    assert bindings[0]['binding_type'] == 'leader'
    assert len(bindings[0]['entries']) == 2

def test_comment_structure():
    """Test parsing of comments in different contexts."""
    analyzer = StructuralAnalyzer()
    input_text = """
    # Top level comment
    mod1 = lcmd  # Inline comment
    """
    tree = analyzer.parse(input_text)
    
    assert len(tree['comments']) == 2
    assert any("Top level" in c for c in tree['comments'])
    assert any("Inline" in c for c in tree['comments'])

def test_nested_structure():
    """Test parsing of nested structures with comments."""
    analyzer = StructuralAnalyzer()
    input_text = """
    mod1 - l : {  # Leader block
        # Inner comment
        h : open -a Safari;  # Action comment
    }
    """
    tree = analyzer.parse(input_text)
    
    bindings = [s for s in tree['statements'] if s.get('type') == 'binding']
    assert len(bindings) == 1
    
    leader = bindings[0]
    assert leader['comment'] == "# Leader block"
    assert len(leader['entries']) == 1
    assert leader['entries'][0]['comment'] == "# Action comment"

def test_error_handling():
    """Test structural error handling."""
    analyzer = StructuralAnalyzer()
    invalid_inputs = [
        "mod1 =",  # Incomplete modifier
        "mod1 - ",  # Incomplete binding
        "mod1 - l : { h : open -a Safari",  # Unclosed block
    ]
    
    for input_text in invalid_inputs:
        with pytest.raises(Exception):
            analyzer.parse(input_text) 