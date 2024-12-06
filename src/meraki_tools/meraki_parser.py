"""Basic parser for Meraki configuration files.

This module implements Phase 1 and 2 features:
1. Basic token parsing
2. Simple modifier definitions (mod1 = lcmd + lalt)
3. Basic keybindings (mod1 - k : command)
4. Compound modifiers (mod1 + shift)
5. Group syntax (mod1 + {a,b,c})
6. Basic error reporting
"""

from dataclasses import dataclass, asdict
from typing import Dict, List
from .meraki_lexer import TokenType, Token, create_lexer


@dataclass
class ModifierDefinition:
    """Represents a modifier definition in the configuration."""
    name: str  # The name of the modifier (e.g. mod1)
    keys: List[str]  # The two keys that make up the modifier
    comments: List[str]  # Any comments associated with the definition
    line_number: int  # Line number where the definition appears


@dataclass
class Keybinding:
    """Represents a basic keybinding in the configuration."""
    modifiers: List[str]  # The modifiers used (e.g. ["mod1", "shift"])
    key: str  # The key being bound
    command: str  # The command to execute
    comments: List[str]  # Any comments associated with the binding
    line_number: int  # Line number where the binding appears


class ParseError(Exception):
    """Exception raised for parsing errors."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


class MerakiParser:
    """Basic parser for Meraki configuration files."""
    
    def __init__(self):
        """Initialize the parser."""
        self.lexer = create_lexer()
        self.tokens = []
        self.current = 0
    
    def parse_string(self, content: str) -> Dict:
        """Parse a Meraki config string and return an AST."""
        # Initialize parser state
        self.tokens = list(self.lexer.tokenize(content))
        self.current = 0
        
        # Initialize AST
        ast = {
            "modifiers": {},
            "keybindings": [],
            "comments": []
        }
        
        while not self._is_at_end():
            # Skip whitespace and newlines
            if self._match(TokenType.WHITESPACE, TokenType.NEWLINE):
                continue
            
            # Handle comments
            if self._match(TokenType.COMMENT):
                # Remove # and whitespace
                ast["comments"].append(self._previous().value[1:].strip())
                continue
            
            # Parse modifier definition or keybinding
            if self._match(TokenType.IDENTIFIER):
                name = self._previous().value
                self._skip_whitespace()
                
                if self._match(TokenType.EQUALS):
                    # Modifier definition
                    mod_def = self._parse_modifier_definition(name)
                    ast["modifiers"][mod_def.name] = asdict(mod_def)
                elif self._match(TokenType.MINUS):
                    # Keybinding
                    binding = self._parse_keybinding([name])
                    ast["keybindings"].append(asdict(binding))
                elif self._match(TokenType.PLUS):
                    # Compound modifier keybinding
                    modifiers = [name]
                    while True:
                        self._skip_whitespace()
                        if self._match(TokenType.LBRACE):
                            # Group of modifiers
                            group = self._parse_group()
                            modifiers.extend(group)
                        elif self._match(TokenType.IDENTIFIER):
                            modifiers.append(self._previous().value)
                        else:
                            raise ParseError(
                                "Expected modifier or '{' after '+'",
                                self._peek().line,
                                self._peek().column
                            )
                        
                        self._skip_whitespace()
                        if not self._match(TokenType.PLUS):
                            break
                    
                    if not self._match(TokenType.MINUS):
                        raise ParseError(
                            "Expected '-' after modifiers",
                            self._peek().line,
                            self._peek().column
                        )
                    
                    binding = self._parse_keybinding(modifiers)
                    ast["keybindings"].append(asdict(binding))
                else:
                    raise ParseError(
                        "Expected '=', '-', or '+' after identifier",
                        self._peek().line,
                        self._peek().column
                    )
            else:
                raise ParseError(
                    f"Unexpected token: {self._peek().type}",
                    self._peek().line,
                    self._peek().column
                )
        
        return ast
    
    def _parse_group(self) -> List[str]:
        """Parse a group of identifiers {a,b,c}."""
        items = []
        start_line = self._peek().line
        start_column = self._peek().column
        
        while not self._is_at_end():
            self._skip_whitespace()
            
            # Check for non-group tokens that indicate unterminated group
            if self._check(TokenType.COLON, TokenType.NEWLINE):
                raise ParseError(
                    "Unterminated group",
                    start_line,
                    start_column
                )
            
            if self._match(TokenType.RBRACE):
                if not items:
                    raise ParseError(
                        "Empty group",
                        self._peek().line,
                        self._peek().column
                    )
                return items
            
            if items:
                # Not the first item, expect comma
                if not self._match(TokenType.COMMA):
                    raise ParseError(
                        "Expected ',' between group items",
                        self._peek().line,
                        self._peek().column
                    )
                self._skip_whitespace()
            
            if not self._match(TokenType.IDENTIFIER):
                raise ParseError(
                    "Expected identifier in group",
                    self._peek().line,
                    self._peek().column
                )
            
            items.append(self._previous().value)
        
        raise ParseError(
            "Unterminated group",
            start_line,
            start_column
        )
    
    def _parse_modifier_definition(self, name: str) -> ModifierDefinition:
        """Parse a modifier definition after the equals sign."""
        self._skip_whitespace()
        
        # First key
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError(
                "Expected first key in modifier definition",
                self._peek().line,
                self._peek().column
            )
        key1 = self._previous().value
        
        self._skip_whitespace()
        
        # Plus sign
        if not self._match(TokenType.PLUS):
            raise ParseError(
                "Expected '+' between keys",
                self._peek().line,
                self._peek().column
            )
        
        self._skip_whitespace()
        
        # Second key
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError(
                "Expected second key in modifier definition",
                self._peek().line,
                self._peek().column
            )
        key2 = self._previous().value
        
        # Handle optional comment
        comments = []
        self._skip_whitespace()
        if self._match(TokenType.COMMENT):
            # Remove # and whitespace
            comments.append(self._previous().value[1:].strip())
        
        # Skip to end of line
        while not self._is_at_end() and not self._match(TokenType.NEWLINE):
            self._advance()
        
        return ModifierDefinition(
            name=name,
            keys=[key1, key2],
            comments=comments,
            line_number=self._peek().line
        )
    
    def _parse_keybinding(self, modifiers: List[str]) -> Keybinding:
        """Parse a keybinding after the minus sign."""
        self._skip_whitespace()
        
        # Key (can be a single key or a group)
        keys = []
        if self._match(TokenType.LBRACE):
            keys = self._parse_group()
        elif self._match(TokenType.IDENTIFIER):
            keys = [self._previous().value]
        else:
            raise ParseError(
                "Expected key or '{' in keybinding",
                self._peek().line,
                self._peek().column
            )
        
        self._skip_whitespace()
        
        # Colon
        if not self._match(TokenType.COLON):
            raise ParseError(
                "Expected ':' after key",
                self._peek().line,
                self._peek().column
            )
        
        # Command (collect all text/string tokens until newline or comment)
        command_parts = []
        self._skip_whitespace()
        
        # Track if we need to add space between parts
        need_space = False
        
        while not self._is_at_end():
            token_types = (
                TokenType.TEXT,
                TokenType.STRING,
                TokenType.IDENTIFIER
            )
            if self._match(*token_types):
                if need_space:
                    command_parts.append(" ")
                command_parts.append(self._previous().value)
                need_space = True
            elif self._match(TokenType.WHITESPACE):
                need_space = True
            elif self._check(TokenType.COMMENT, TokenType.NEWLINE):
                break
            else:
                self._advance()  # Skip other tokens
        
        if not command_parts:
            raise ParseError(
                "Expected command after ':'",
                self._peek().line,
                self._peek().column
            )
        
        # Handle optional comment
        comments = []
        if self._match(TokenType.COMMENT):
            # Remove # and whitespace
            comments.append(self._previous().value[1:].strip())
        
        # Skip to end of line
        while not self._is_at_end() and not self._match(TokenType.NEWLINE):
            self._advance()
        
        # Create a keybinding for each key in the group
        bindings = []
        for key in keys:
            bindings.append(Keybinding(
                modifiers=modifiers,
                key=key,
                command="".join(command_parts).strip(),
                comments=comments,
                line_number=self._peek().line
            ))
        
        # If it's a single key, return just that binding
        # Otherwise, return the first binding and let the caller handle expansion
        return bindings[0]
    
    def _skip_whitespace(self):
        """Skip any whitespace tokens."""
        while self._match(TokenType.WHITESPACE):
            pass
    
    def _is_at_end(self) -> bool:
        """Check if we've reached the end of the token stream."""
        return self._peek().type == TokenType.EOF
    
    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self.current]
    
    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self.current - 1]
    
    def _advance(self) -> Token:
        """Consume and return the current token."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()
    
    def _match(self, *types: TokenType) -> bool:
        """Check if the current token matches any of the given types."""
        for type_ in types:
            if self._check(type_):
                self._advance()
                return True
        return False
    
    def _check(self, *types: TokenType) -> bool:
        """Check if the current token is of any of the given types."""
        if self._is_at_end():
            return False
        return self._peek().type in types 