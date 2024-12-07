"""Tests for the semantic analysis stage of the parser."""

import pytest
from meraki.parser import SemanticAnalyzer, ModifierDef, Keybinding, ConfigurationAST

def create_mock_parse_tree(statements=None, comments=None, notes=None):
    """Create a mock parse tree for testing."""
    return {
        'statements': statements or [],
        'comments': comments or [],
        'notes': notes or []
    }

def test_modifier_conversion():
    """Test conversion of modifiers to AST nodes."""
    analyzer = SemanticAnalyzer()
    tree = create_mock_parse_tree(statements=[
        {
            'type': 'modifier',
            'name': 'mod1',
            'value': ['lcmd', 'lalt'],
            'comment': '# Primary modifier'
        }
    ])
    
    ast = analyzer.process(tree)
    
    assert isinstance(ast, ConfigurationAST)
    assert 'mod1' in ast.modifiers
    assert isinstance(ast.modifiers['mod1'], ModifierDef)
    assert ast.modifiers['mod1'].keys == ['lcmd', 'lalt']
    assert ast.modifiers['mod1'].comments == ['# Primary modifier']

def test_comment_preservation():
    """Test preservation of comments in AST."""
    analyzer = SemanticAnalyzer()
    tree = create_mock_parse_tree(
        statements=[
            {
                'type': 'modifier',
                'name': 'mod1',
                'value': ['lcmd'],
                'comment': '# Inline comment'
            }
        ],
        comments=['# Standalone comment']
    )
    
    ast = analyzer.process(tree)
    
    assert len(ast.comments) == 2
    assert '# Standalone comment' in ast.comments
    assert '# Inline comment' in ast.comments

def test_empty_input():
    """Test processing of empty input."""
    analyzer = SemanticAnalyzer()
    tree = create_mock_parse_tree()
    
    ast = analyzer.process(tree)
    
    assert isinstance(ast, ConfigurationAST)
    assert len(ast.modifiers) == 0
    assert len(ast.keybindings) == 0
    assert len(ast.comments) == 0

def test_line_number_tracking():
    """Test line number tracking in AST nodes."""
    analyzer = SemanticAnalyzer()
    tree = create_mock_parse_tree(statements=[
        {
            'type': 'modifier',
            'name': 'mod1',
            'value': ['lcmd'],
            'line_number': 42
        }
    ])
    
    ast = analyzer.process(tree)
    
    assert ast.modifiers['mod1'].line_number == 42

def test_error_handling():
    """Test semantic error handling."""
    analyzer = SemanticAnalyzer()
    invalid_trees = [
        # Missing type
        create_mock_parse_tree(statements=[{'name': 'mod1'}]),
        # Invalid type
        create_mock_parse_tree(statements=[{'type': 'invalid'}]),
        # Missing required fields
        create_mock_parse_tree(statements=[{'type': 'modifier'}])
    ]
    
    for tree in invalid_trees:
        with pytest.raises(Exception):
            analyzer.process(tree) 