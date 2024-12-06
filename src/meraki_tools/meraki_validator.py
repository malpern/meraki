from typing import Dict, List, Set, Tuple

class ValidationError:
    def __init__(self, message: str, line_number: int):
        self.message = message
        self.line_number = line_number

    def __str__(self):
        return f"Line {self.line_number}: {self.message}"

class MerakiValidator:
    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
    
    def validate(self, ast: Dict) -> Tuple[List[ValidationError], List[ValidationError]]:
        """Validate a Meraki AST and return a tuple of (errors, warnings)."""
        self.errors = []
        self.warnings = []
        
        # Check for undefined modifiers in keybindings first
        self._check_undefined_modifiers(ast)
        
        # Only check for unused modifiers if all modifiers are defined
        if not self.errors:
            self._check_unused_modifiers(ast)
        
        # Check for duplicate keybindings
        self._check_duplicate_keybindings(ast)
        
        return self.errors, self.warnings
    
    def _check_unused_modifiers(self, ast: Dict):
        """Check for modifiers that are defined but never used."""
        defined_modifiers = set(ast["modifiers"].keys())
        used_modifiers = set()
        
        # Collect all used modifiers from keybindings
        for binding in ast["keybindings"]:
            used_modifiers.add(binding["key_combination"])
        
        # Find unused modifiers
        unused_modifiers = defined_modifiers - used_modifiers
        for modifier in unused_modifiers:
            line_number = ast["modifiers"][modifier]["line_number"]
            self.warnings.append(
                ValidationError(
                    f"Modifier '{modifier}' is defined but never used",
                    line_number
                )
            )
    
    def _check_duplicate_keybindings(self, ast: Dict):
        """Check for duplicate keybindings."""
        seen_bindings = {}  # (modifier, key) -> line_number
        
        for binding in ast["keybindings"]:
            key = (binding["key_combination"], binding["key"])
            if key in seen_bindings:
                self.errors.append(
                    ValidationError(
                        f"Duplicate keybinding '{key[0]} - {key[1]}' (previously defined at line {seen_bindings[key]})",
                        binding["line_number"]
                    )
                )
            else:
                seen_bindings[key] = binding["line_number"]
    
    def _check_undefined_modifiers(self, ast: Dict):
        """Check for keybindings that use undefined modifiers."""
        defined_modifiers = set(ast["modifiers"].keys())
        
        for binding in ast["keybindings"]:
            modifier = binding["key_combination"]
            if modifier not in defined_modifiers:
                self.errors.append(
                    ValidationError(
                        f"Keybinding uses undefined modifier '{modifier}'",
                        binding["line_number"]
                    )
                ) 