import re
from typing import List, Tuple, Dict
from src.ast_nodes import Comment, CommentType, Modifier, KeyBinding, MerakiAST
from src.tokenizer import Token, TokenType
from src.logger import logger
from src.exceptions import ParseError

class MerakiParser:
    def __init__(self):
        """Initialize the parser."""
        # Regular expressions for comment detection
        self.line_comment_re = re.compile(r'^\s*#\s*(.*)$')
        self.inline_comment_re = re.compile(r'([^#]*?)#\s*(.*)$')
        self.multiline_start_re = re.compile(r'^\s*@END\s*$')
        self.multiline_end_re = re.compile(r'^\s*END\s*$')
        
        # Lexer state
        self.tokens: List[Token] = []
        self.current = 0
        
        # Comment handling
        self.pending_comments: List[Comment] = []

    def extract_comments(self, content: str) -> Tuple[List[Comment], str]:
        """Extract all comments and return them with clean content.
        
        This method preserves line numbers by replacing comment-only lines with empty lines.
        For inline comments, it removes only the comment part, keeping the code.
        """
        lines = content.split('\n')
        comments: List[Comment] = []
        clean_lines: List[str] = []
        
        for i, line in enumerate(lines):
            line = line.rstrip()
            line_number = i + 1
            
            # Check for line comment (entire line is a comment)
            if line.lstrip().startswith('#'):
                text = line.lstrip()[1:].lstrip()
                comments.append(Comment(
                    type=CommentType.LINE,
                    text=text,
                    line_number=line_number
                ))
                clean_lines.append('')  # Preserve line number with empty line
                continue
            
            # Check for multiline comment
            if line.lstrip() == '@END':
                start_line = line_number
                multiline_text = []
                clean_lines.append('')  # Replace @END with empty line
                
                i += 1
                while i < len(lines) and lines[i].strip() != 'END':
                    multiline_text.append(lines[i])
                    clean_lines.append('')  # Replace comment content with empty lines
                    i += 1
                
                if i < len(lines):  # Found END marker
                    comments.append(Comment(
                        type=CommentType.MULTILINE,
                        text='\n'.join(multiline_text),
                        line_number=start_line + 1,  # Start after @END
                        end_line=i + 1  # Include END marker
                    ))
                    clean_lines.append('')  # Replace END with empty line
                continue
            
            # Check for inline comment
            if '#' in line:
                code_part, comment_part = line.split('#', 1)
                comments.append(Comment(
                    type=CommentType.INLINE,
                    text=comment_part.strip(),
                    line_number=line_number,
                    associated_code_line=line_number
                ))
                clean_lines.append(code_part.rstrip())  # Keep code, remove comment
                continue
            
            # No comment found, keep line as is
            clean_lines.append(line)
        
        clean_content = '\n'.join(clean_lines)
        logger.debug("Clean content:\n%s", clean_content)
        logger.debug("Found comments:")
        for comment in comments:
            logger.debug("  %s at line %d: %s", 
                        comment.type, comment.line_number, comment.text)
        
        return comments, clean_content

    def parse(self, content: str) -> MerakiAST:
        """Parse Meraki configuration content into an AST."""
        # Phase 1: Extract comments
        logger.debug("Phase 1: Extracting comments")
        comments, clean_content = self.extract_comments(content)
        self.pending_comments = comments
        
        # Phase 2: Tokenize clean content
        logger.debug("Phase 2: Tokenizing clean content")
        self._tokenize(clean_content)
        
        # Phase 3: Parse into AST
        logger.debug("Phase 3: Parsing into AST")
        modifiers: Dict[str, Modifier] = {}
        keybindings: List[KeyBinding] = []
        
        # Track current line number
        current_line = 1
        
        while not self._is_at_end():
            # Skip whitespace and newlines
            if self._match(TokenType.WHITESPACE):
                continue
            
            if self._match(TokenType.NEWLINE):
                current_line += 1
                continue
            
            # Parse modifier definition or keybinding
            if self._match(TokenType.IDENTIFIER):
                name = self._previous().value
                line_number = current_line
                logger.debug("Found identifier '%s' at line %d", name, line_number)
                self._skip_whitespace()
                
                if self._match(TokenType.EQUALS):
                    logger.debug("Parsing modifier definition")
                    # Modifier definition
                    mod = self._parse_modifier_definition(name, line_number)
                    modifiers[mod.name] = mod
                elif self._match(TokenType.MINUS):
                    logger.debug("Parsing keybinding")
                    # Keybinding
                    binding = self._parse_keybinding([name], line_number)
                    keybindings.append(binding)
                else:
                    raise ParseError(
                        "Expected '=' or '-' after identifier",
                        self._peek().line,
                        self._peek().column
                    )
        
        # Return AST with any remaining unattached comments
        logger.debug("Returning AST with %d modifiers and %d keybindings",
                    len(modifiers), len(keybindings))
        return MerakiAST(
            modifiers=modifiers,
            keybindings=keybindings,
            comments=self.pending_comments
        ) 

    def _tokenize(self, content: str) -> None:
        """Tokenize the clean content."""
        self.tokens = []
        lines = content.split('\n')
        
        # Track line numbers
        line_map = {}
        current_line = 1
        for i, line in enumerate(lines, 1):
            if line.strip():  # Only map non-empty lines
                line_map[i] = current_line
                current_line += 1
        
        logger.debug("Line mapping: %s", line_map)
        
        for line_num, line in enumerate(lines, 1):
            if not line.strip():  # Skip empty lines
                continue
                
            logger.debug("Tokenizing line %d: %s", line_num, line)
            col = 0
            i = 0
            while i < len(line):
                char = line[i]
                logger.debug("  Processing char '%s' at position %d", char, i)
                
                # Skip whitespace
                if char.isspace():
                    spaces = ''
                    while i < len(line) and line[i].isspace():
                        spaces += line[i]
                        i += 1
                    if spaces:
                        logger.debug("  Found whitespace: '%s'", spaces)
                        self.tokens.append(Token(TokenType.WHITESPACE, spaces, line_map[line_num], col))
                        col += len(spaces)
                    continue
                
                # Handle operators and special characters
                if char == '=':
                    logger.debug("  Found equals")
                    self.tokens.append(Token(TokenType.EQUALS, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == '+':
                    logger.debug("  Found plus")
                    self.tokens.append(Token(TokenType.PLUS, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == '-':
                    logger.debug("  Found minus")
                    self.tokens.append(Token(TokenType.MINUS, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == ':':
                    logger.debug("  Found colon")
                    self.tokens.append(Token(TokenType.COLON, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == '{':
                    logger.debug("  Found left brace")
                    self.tokens.append(Token(TokenType.LBRACE, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == '}':
                    logger.debug("  Found right brace")
                    self.tokens.append(Token(TokenType.RBRACE, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == ',':
                    logger.debug("  Found comma")
                    self.tokens.append(Token(TokenType.COMMA, char, line_map[line_num], col))
                    i += 1
                    col += 1
                elif char == ';':
                    logger.debug("  Found semicolon")
                    self.tokens.append(Token(TokenType.SEMICOLON, char, line_map[line_num], col))
                    i += 1
                    col += 1
                # Handle strings
                elif char == '"':
                    logger.debug("  Found string start")
                    string_value = ''
                    i += 1  # Skip opening quote
                    col += 1
                    while i < len(line) and line[i] != '"':
                        string_value += line[i]
                        i += 1
                        col += 1
                    if i < len(line):  # Skip closing quote
                        i += 1
                        col += 1
                    logger.debug("  Found string: '%s'", string_value)
                    self.tokens.append(Token(TokenType.STRING, string_value, line_map[line_num], col - len(string_value)))
                # Handle identifiers and text
                else:
                    identifier = ''
                    start_col = col
                    while i < len(line) and not line[i].isspace() and line[i] not in '=+-:{}[];,':
                        identifier += line[i]
                        i += 1
                        col += 1
                    if identifier:
                        # Check if it's a timeout value
                        if identifier.endswith('ms'):
                            logger.debug("  Found timeout: '%s'", identifier)
                            self.tokens.append(Token(TokenType.TIMEOUT, identifier, line_map[line_num], start_col))
                        else:
                            logger.debug("  Found identifier: '%s'", identifier)
                            self.tokens.append(Token(TokenType.IDENTIFIER, identifier, line_map[line_num], start_col))
            
            # Add newline token at the end of each line
            logger.debug("  Adding newline")
            self.tokens.append(Token(TokenType.NEWLINE, '\n', line_map[line_num], col))
        
        # Add EOF token
        logger.debug("Adding EOF token")
        self.tokens.append(Token(TokenType.EOF, '', current_line, 0))
        
        # Log all tokens
        logger.debug("Final token stream:")
        for token in self.tokens:
            logger.debug("  %s: '%s' at line %d, col %d", 
                        token.type, token.value, token.line, token.column)

    def _parse_modifier_definition(self, name: str, line_number: int) -> Modifier:
        """Parse a modifier definition after the equals sign."""
        logger.debug("Parsing modifier definition for '%s'", name)
        self._skip_whitespace()
        
        # First key
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError(
                "Expected first key in modifier definition",
                self._peek().line,
                self._peek().column
            )
        key1 = self._previous().value
        logger.debug("Found first key: %s", key1)
        
        self._skip_whitespace()
        
        # Plus sign
        if not self._match(TokenType.PLUS):
            raise ParseError(
                "Expected '+' between keys",
                self._peek().line,
                self._peek().column
            )
        logger.debug("Found plus sign")
        
        self._skip_whitespace()
        
        # Second key
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError(
                "Expected second key in modifier definition",
                self._peek().line,
                self._peek().column
            )
        key2 = self._previous().value
        logger.debug("Found second key: %s", key2)
        
        # Skip to end of line
        while not self._is_at_end() and not self._check(TokenType.NEWLINE):
            self._advance()
        
        # Skip the newline
        self._match(TokenType.NEWLINE)
        
        # Get any comments for this line
        comments = self._get_comments_for_line(line_number)
        
        return Modifier(
            line_number=line_number,
            comments=comments,
            name=name,
            keys=[key1, key2]
        )

    def _parse_keybinding(self, modifiers: List[str], line_number: int) -> KeyBinding:
        """Parse a keybinding after the minus sign."""
        logger.debug("Parsing keybinding with modifiers: %s", modifiers)
        self._skip_whitespace()
        
        # Key
        if not self._match(TokenType.IDENTIFIER):
            raise ParseError(
                "Expected key after '-'",
                self._peek().line,
                self._peek().column
            )
        key = self._previous().value
        logger.debug("Found key: %s", key)
        
        # Optional timeout
        timeout = None
        self._skip_whitespace()
        if self._match(TokenType.LBRACE):
            if not self._match(TokenType.TIMEOUT):
                raise ParseError(
                    "Expected timeout value",
                    self._peek().line,
                    self._peek().column
                )
            try:
                timeout = int(self._previous().value.rstrip('ms'))
            except ValueError:
                raise ParseError(
                    "Invalid timeout value",
                    self._peek().line,
                    self._peek().column
                )
            if not self._match(TokenType.RBRACE):
                raise ParseError(
                    "Expected '}' after timeout",
                    self._peek().line,
                    self._peek().column
                )
            logger.debug("Found timeout: %d", timeout)
        
        self._skip_whitespace()
        
        # Colon
        if not self._match(TokenType.COLON):
            raise ParseError(
                "Expected ':' after key",
                self._peek().line,
                self._peek().column
            )
        
        self._skip_whitespace()
        
        # Action or nested bindings
        action = None
        nested_bindings = None
        
        if self._match(TokenType.LBRACE):
            logger.debug("Parsing nested bindings")
            nested_bindings = self._parse_nested_bindings(line_number)
        else:
            # Parse action until newline or semicolon
            action_text = []
            while not self._is_at_end():
                if self._check(TokenType.NEWLINE, TokenType.SEMICOLON):
                    break
                if self._match(TokenType.IDENTIFIER, TokenType.STRING):
                    action_text.append(self._previous().value)
                elif self._match(TokenType.WHITESPACE):
                    if action_text:  # Only add space if we have text
                        action_text.append(' ')
                else:
                    # Skip any other token
                    self._advance()
            
            if action_text:
                # Join and clean up extra spaces
                command = ' '.join(''.join(action_text).split())
                action = Action(
                    line_number=line_number,
                    comments=[],
                    command=command
                )
                logger.debug("Found action: %s", command)
            
            # Skip semicolon if present
            self._match(TokenType.SEMICOLON)
            
            # Skip to end of line
            while not self._is_at_end() and not self._check(TokenType.NEWLINE):
                self._advance()
            
            # Skip the newline
            self._match(TokenType.NEWLINE)
        
        # Get any comments for this line
        comments = self._get_comments_for_line(line_number)
        
        return KeyBinding(
            line_number=line_number,
            comments=comments,
            key_combination=' '.join(modifiers),
            key=key,
            timeout=timeout,
            action=action,
            nested_bindings=nested_bindings
        )

    def _parse_nested_bindings(self, parent_line: int) -> Dict[str, KeyBinding]:
        """Parse nested keybindings inside braces."""
        logger.debug("Parsing nested bindings")
        bindings = {}
        
        while not self._is_at_end():
            self._skip_whitespace()
            
            if self._match(TokenType.RBRACE):
                break
            
            if self._match(TokenType.IDENTIFIER):
                key = self._previous().value
                line_number = self._previous().line
                logger.debug("Found nested key: %s", key)
                
                self._skip_whitespace()
                if not self._match(TokenType.COLON):
                    raise ParseError(
                        "Expected ':' after key in nested binding",
                        self._peek().line,
                        self._peek().column
                    )
                
                # Parse the nested binding's action
                self._skip_whitespace()
                action_text = []
                while not self._is_at_end():
                    if self._check(TokenType.NEWLINE, TokenType.SEMICOLON):
                        break
                    if self._match(TokenType.IDENTIFIER, TokenType.STRING):
                        action_text.append(self._previous().value)
                    elif self._match(TokenType.WHITESPACE):
                        if action_text:  # Only add space if we have text
                            action_text.append(' ')
                    else:
                        # Skip any other token
                        self._advance()
                
                if action_text:
                    # Join and clean up extra spaces
                    command = ' '.join(''.join(action_text).split())
                    action = Action(
                        line_number=line_number,
                        comments=[],
                        command=command
                    )
                    logger.debug("Found nested action: %s", command)
                    
                    bindings[key] = KeyBinding(
                        line_number=line_number,
                        comments=self._get_comments_for_line(line_number),
                        key_combination='',  # Nested bindings don't have modifiers
                        key=key,
                        timeout=None,
                        action=action
                    )
                
                # Skip semicolon if present
                self._match(TokenType.SEMICOLON)
            
            self._skip_whitespace()
        
        return bindings

    def _get_comments_for_line(self, line_number: int) -> List[Comment]:
        """Get and remove comments associated with a specific line."""
        associated = []
        remaining = []
        
        for comment in self.pending_comments:
            if (comment.line_number == line_number or 
                comment.associated_code_line == line_number):
                associated.append(comment)
            else:
                remaining.append(comment)
        
        self.pending_comments = remaining
        return associated

    def _is_at_end(self) -> bool:
        """Check if we've reached the end of tokens."""
        return self.current >= len(self.tokens)

    def _peek(self) -> Token:
        """Look at the current token without consuming it."""
        if self._is_at_end():
            return Token(TokenType.EOF, "", -1, -1)
        return self.tokens[self.current]

    def _previous(self) -> Token:
        """Get the most recently consumed token."""
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        """Consume the current token and return it."""
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _match(self, *types: str) -> bool:
        """Check if the current token matches any of the given types."""
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _check(self, *types: str) -> bool:
        """Check if the current token is of any of the given types."""
        if self._is_at_end():
            return False
        return self._peek().type in types

    def _skip_whitespace(self) -> None:
        """Skip any whitespace tokens."""
        while self._match(TokenType.WHITESPACE, TokenType.NEWLINE):
            pass