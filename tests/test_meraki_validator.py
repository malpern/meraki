import pytest
from src.meraki_tools.meraki_validator import MerakiValidator

def test_unused_modifier():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1},
            "mod2": {"keys": ["lshift", "lctrl"], "comments": [], "line_number": 2}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "m",
                "action": "open -a Mail.app",
                "comments": [],
                "line_number": 3
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 0
    assert len(warnings) == 1
    assert "mod2" in str(warnings[0])
    assert warnings[0].line_number == 2

def test_duplicate_keybinding():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "m",
                "action": "open -a Mail.app",
                "comments": [],
                "line_number": 2
            },
            {
                "key_combination": "mod1",
                "key": "m",
                "action": "open -a Messages.app",
                "comments": [],
                "line_number": 3
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "Duplicate keybinding" in str(errors[0])
    assert errors[0].line_number == 3

def test_undefined_modifier():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod2",
                "key": "m",
                "action": "open -a Mail.app",
                "comments": [],
                "line_number": 2
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 1
    assert len(warnings) == 0
    assert "undefined modifier" in str(errors[0])
    assert errors[0].line_number == 2

def test_validate_timeout_values():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "l",
                "timeout": -100,  # Invalid negative timeout
                "nested_bindings": {},
                "line_number": 2
            },
            {
                "key_combination": "mod1",
                "key": "k",
                "timeout": 10000,  # Too long timeout
                "nested_bindings": {},
                "line_number": 3
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 1  # Negative timeout is an error
    assert len(warnings) == 1  # Long timeout is a warning
    assert "negative timeout" in str(errors[0])
    assert "timeout exceeds recommended maximum" in str(warnings[0])

def test_validate_nested_binding_depth():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "a",
                "nested_bindings": {
                    "b": {
                        "nested_bindings": {
                            "c": {
                                "nested_bindings": {
                                    "d": {
                                        "action": "test",
                                        "line_number": 5
                                    }
                                },
                                "line_number": 4
                            }
                        },
                        "line_number": 3
                    }
                },
                "line_number": 2
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(warnings) == 1
    assert "deep nesting" in str(warnings[0])

def test_validate_duplicate_nested_keys():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "a",
                "nested_bindings": {
                    "x": {
                        "action": "test1",
                        "line_number": 2
                    },
                    "x": {  # Duplicate key in nested binding
                        "action": "test2",
                        "line_number": 3
                    }
                },
                "line_number": 4
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 1
    assert "duplicate nested key" in str(errors[0])

def test_validate_activation_flag_combinations():
    validator = MerakiValidator()
    ast = {
        "modifiers": {
            "mod1": {"keys": ["lcmd", "lalt"], "comments": [], "line_number": 1}
        },
        "keybindings": [
            {
                "key_combination": "mod1",
                "key": "x",
                "action": "test",
                "activation_flags": ["up", "repeat"],  # Invalid combination
                "line_number": 2
            }
        ]
    }
    
    errors, warnings = validator.validate(ast)
    assert len(errors) == 1
    assert "invalid activation flag combination" in str(errors[0]) 