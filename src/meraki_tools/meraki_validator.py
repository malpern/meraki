from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ValidationResult:
    """Result of AST validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]

class MerakiValidator:
    """Validates Meraki AST structure and semantics."""
    
    def __init__(self):
        """Initialize validator."""
        self.errors = []
        self.warnings = []
    
    def validate(self, ast: Dict) -> ValidationResult:
        """Validate AST structure and semantics."""
        self.errors = []
        self.warnings = []
        
        # Validate required top-level keys
        if "modifiers" not in ast:
            self.errors.append("Missing 'modifiers' section")
        if "keybindings" not in ast:
            self.errors.append("Missing 'keybindings' section")
        
        # Validate modifiers
        if "modifiers" in ast:
            self._validate_modifiers(ast["modifiers"])
        
        # Validate keybindings
        if "keybindings" in ast:
            self._validate_keybindings(ast["keybindings"], ast.get("modifiers", {}))
        
        return ValidationResult(
            is_valid=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings
        )
    
    def _validate_modifiers(self, modifiers: Dict) -> None:
        """Validate modifier definitions."""
        for name, mod in modifiers.items():
            if not isinstance(mod, dict):
                self.errors.append(f"Invalid modifier definition for '{name}'")
                continue
            
            if "keys" not in mod:
                self.errors.append(f"Missing keys in modifier '{name}'")
            elif not isinstance(mod["keys"], list) or len(mod["keys"]) != 2:
                self.errors.append(f"Invalid keys format in modifier '{name}'")
            
            if "line_number" not in mod:
                self.warnings.append(f"Missing line number in modifier '{name}'")
    
    def _validate_keybindings(self, keybindings: List[Dict], modifiers: Dict) -> None:
        """Validate keybinding definitions."""
        for binding in keybindings:
            if not isinstance(binding, dict):
                self.errors.append("Invalid keybinding definition")
                continue
            
            # Validate key combination
            if "key_combination" not in binding:
                self.errors.append("Missing key combination in keybinding")
            else:
                self._validate_key_combination(binding["key_combination"], modifiers)
            
            # Validate key
            if "key" in binding and binding["key"] is not None:
                if not isinstance(binding["key"], str):
                    self.errors.append("Invalid key format")
            
            # Validate action or actions
            if "action" not in binding and "actions" not in binding:
                self.errors.append("Missing action in keybinding")
            elif "actions" in binding:
                if not isinstance(binding["actions"], list):
                    self.errors.append("Invalid actions format")
                elif not all(isinstance(a, dict) and "command" in a for a in binding["actions"]):
                    self.errors.append("Invalid action format in command chain")
            
            # Validate timeout
            if "timeout" in binding and binding["timeout"] is not None:
                if not isinstance(binding["timeout"], int):
                    self.errors.append("Invalid timeout format")
                elif binding["timeout"] < 0:
                    self.errors.append("Timeout cannot be negative")
            
            # Validate nested bindings
            if "nested_bindings" in binding and binding["nested_bindings"] is not None:
                if not isinstance(binding["nested_bindings"], dict):
                    self.errors.append("Invalid nested bindings format")
                else:
                    self._validate_nested_bindings(binding["nested_bindings"])
            
            # Validate line number
            if "line_number" not in binding:
                self.warnings.append("Missing line number in keybinding")
    
    def _validate_key_combination(self, key_combination: str, modifiers: Dict) -> None:
        """Validate key combination against defined modifiers."""
        parts = key_combination.split()
        if not parts:
            self.errors.append("Empty key combination")
            return
        
        base_mod = parts[0]
        if base_mod not in modifiers:
            self.errors.append(f"Undefined modifier '{base_mod}'")
    
    def _validate_nested_bindings(self, nested_bindings: Dict) -> None:
        """Validate nested binding definitions."""
        for key, binding in nested_bindings.items():
            if not isinstance(binding, dict):
                self.errors.append(f"Invalid nested binding for key '{key}'")
                continue
            
            if "command" not in binding:
                self.errors.append(f"Missing command in nested binding for key '{key}'")
            elif not isinstance(binding["command"], str):
                self.errors.append(f"Invalid command format in nested binding for key '{key}'")