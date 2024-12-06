"""Lexical analyzer for Meraki configuration files.

This module provides a lexical analyzer (lexer) for the Meraki configuration
language. The lexer breaks down input text into a sequence of tokens that can be
used by the parser.

Token Types:
    - Basic elements: identifiers, numbers, strings, text
    - Operators: +, -, :, ~, ;, =
    - Delimiters: {}, [], ,
    - Special: whitespace, newline, comment
"""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Iterator
import re


class TokenType(Enum):
    """Token types for Meraki configuration lexical analysis."""
    # Basic elements
    IDENTIFIER = auto()      # modifiers, keys
    NUMBER = auto()          # timeout values
    STRING = auto()          # quoted text
    TEXT = auto()           # unquoted text
    
    # Operators
    PLUS = auto()           # +
    MINUS = auto()          # -
    COLON = auto()          # :
    TILDE = auto()          # ~
    SEMICOLON = auto()      # ;
    EQUALS = auto()         # =
    
    # Delimiters
    LBRACE = auto()         # {
    RBRACE = auto()         # }
    LBRACKET = auto()       # [
    RBRACKET = auto()       # ]
    COMMA = auto()          # ,
    
    # Special
    WHITESPACE = auto()     # space, tab
    NEWLINE = auto()        # \n
    COMMENT = auto()        # # comments
    EOF = auto()            # end of file


@dataclass
class Token:
    """Represents a single token in the input stream."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        """Return a string representation of the token."""
        return (
            f"Token({self.type}, '{self.value}', "
            f"line={self.line}, col={self.column})"
        )


class LexerError(Exception):
    """Exception raised for lexical analysis errors."""
    def __init__(self, message: str, line: int, column: int):
        self.message = message
        self.line = line
        self.column = column
        super().__init__(f"Line {line}, Column {column}: {message}")


class MerakiLexer:
    """Lexical analyzer for Meraki configuration files."""
    
    # Constants
    MAX_IDENTIFIER_LENGTH = 50
    
    def __init__(self):
        """Initialize the lexer with token patterns."""
        # Token patterns in priority order
        self.token_specs = [
            # Whitespace and comments
            (r'[ \t]+', TokenType.WHITESPACE),
            (r'#[^\n]*', TokenType.COMMENT),
            (r'\n', TokenType.NEWLINE),
            
            # Operators (must come before identifiers)
            (r'(?<![\w-])\+(?![\w-])', TokenType.PLUS),  # Plus not part of word
            (r'(?<![\w-])-(?![\w-])', TokenType.MINUS),  # Minus not part of word
            (r':', TokenType.COLON),
            (r'~', TokenType.TILDE),
            (r';', TokenType.SEMICOLON),
            (r'=', TokenType.EQUALS),
            
            # Delimiters
            (r'\{', TokenType.LBRACE),
            (r'\}', TokenType.RBRACE),
            (r'\[', TokenType.LBRACKET),
            (r'\]', TokenType.RBRACKET),
            (r',', TokenType.COMMA),
            
            # Strings with error detection
            (r'"[^"\n]*"', TokenType.STRING),
            (r'"[^"\n]*$', 'UNTERMINATED_STRING'),
            
            # Numbers
            (r'\d+', TokenType.NUMBER),
            
            # Identifiers with length check
            (fr'[a-z][a-z0-9_]{{{self.MAX_IDENTIFIER_LENGTH},}}',
             'IDENTIFIER_TOO_LONG'),
            (r'[a-z][a-z0-9_]*', TokenType.IDENTIFIER),
            
            # Raw text (anything else that's not whitespace)
            (r'[^\s\n"#{}[\]~;:=+,]+', TokenType.TEXT),
        ]
        
        # Build the master regex pattern
        pattern_parts = [
            f'(?P<{t[1].name if isinstance(t[1], TokenType) else t[1]}>{t[0]})'
            for t in self.token_specs
        ]
        self.pattern = '|'.join(pattern_parts)
        self.regex = re.compile(self.pattern)
        
        # Initialize state
        self.input: str = ""
        self.pos: int = 0
        self.line: int = 1
        self.column: int = 1
    
    def tokenize(self, text: str) -> Iterator[Token]:
        """Convert input text into a stream of tokens.
        
        Args:
            text: The input text to tokenize
        
        Yields:
            Token objects representing each token found in the input
        
        Raises:
            LexerError: If invalid input is encountered
        """
        self.input = text
        self.pos = 0
        self.line = 1
        self.column = 1
        
        while self.pos < len(self.input):
            # Save the starting position for this token
            start_line = self.line
            start_column = self.column
            
            match = self.regex.match(self.input, self.pos)
            
            if match is None:
                # No token matches at current position
                raise LexerError(
                    f"Invalid character: {self.input[self.pos]}",
                    self.line,
                    self.column
                )
            
            # Get the matched token type and value
            token_type = None
            value = None
            for name, type_ in [
                (t[1].name if isinstance(t[1], TokenType) else t[1], t[1])
                for t in self.token_specs
            ]:
                if match.group(name):
                    if name == 'UNTERMINATED_STRING':
                        raise LexerError(
                            "Unterminated string literal",
                            start_line,
                            start_column
                        )
                    elif name == 'IDENTIFIER_TOO_LONG':
                        msg = f"Identifier too long (max {self.MAX_IDENTIFIER_LENGTH} chars)"
                        raise LexerError(msg, start_line, start_column)
                    token_type = type_
                    value = match.group(name)
                    break
            
            if token_type is not None:
                # Skip whitespace tokens
                if token_type != TokenType.WHITESPACE:
                    yield Token(
                        token_type,
                        value,
                        start_line,
                        start_column
                    )
                
                # Update position
                for char in value:
                    if char == '\n':
                        self.line += 1
                        self.column = 1
                    else:
                        self.column += 1
                
                self.pos = match.end()
            else:
                # This shouldn't happen given our regex pattern
                raise LexerError(
                    "Unknown token type",
                    self.line,
                    self.column
                )
        
        # Add EOF token
        yield Token(TokenType.EOF, "", self.line, self.column)


def create_lexer() -> MerakiLexer:
    """Factory function to create a new lexer instance."""
    return MerakiLexer() 