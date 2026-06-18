from enum import Enum, auto
from dataclasses import dataclass


class TokenType(Enum):
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    NUMBER = auto()
    STRING = auto()
    BOOL = auto()
    NIL = auto()
    SYMBOL = auto()
    KEYWORD = auto()
    EOF = auto()


@dataclass
class Token:
    type: TokenType
    value: str
    line: int

    def __eq__(self, other):
        if not isinstance(other, Token):
            return NotImplemented
        return self.type == other.type and self.value == other.value and self.line == other.line


class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.tokens = []

    def tokenize(self) -> list[Token]:
        while self.pos < len(self.source):
            self._skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
            ch = self.source[self.pos]
            if ch == '(':
                self.tokens.append(Token(TokenType.LPAREN, ch, self.line))
                self.pos += 1
            elif ch == ')':
                self.tokens.append(Token(TokenType.RPAREN, ch, self.line))
                self.pos += 1
            elif ch == '[':
                self.tokens.append(Token(TokenType.LBRACKET, ch, self.line))
                self.pos += 1
            elif ch == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ch, self.line))
                self.pos += 1
            elif ch == '{':
                self.tokens.append(Token(TokenType.LBRACE, ch, self.line))
                self.pos += 1
            elif ch == '}':
                self.tokens.append(Token(TokenType.RBRACE, ch, self.line))
                self.pos += 1
            elif ch == '"':
                self._read_string()
            elif ch == ':':
                self._read_keyword()
            elif ch.isdigit():
                self._read_number()
            elif self._is_symbol_start(ch):
                self._read_symbol()
            else:
                raise SyntaxError(f"Unexpected character '{ch}' at line {self.line}")
        self.tokens.append(Token(TokenType.EOF, "", self.line))
        return self.tokens

    def _skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            ch = self.source[self.pos]
            if ch in ' \t\r':
                self.pos += 1
            elif ch == '\n':
                self.line += 1
                self.pos += 1
            elif ch == ';':
                while self.pos < len(self.source) and self.source[self.pos] != '\n':
                    self.pos += 1
            else:
                break

    def _read_string(self):
        self.pos += 1  # skip opening "
        start = self.pos
        while self.pos < len(self.source) and self.source[self.pos] != '"':
            if self.source[self.pos] == '\n':
                self.line += 1
            self.pos += 1
        if self.pos >= len(self.source):
            raise SyntaxError(f"Unterminated string at line {self.line}")
        value = self.source[start:self.pos]
        self.tokens.append(Token(TokenType.STRING, value, self.line))
        self.pos += 1  # skip closing "

    def _read_keyword(self):
        self.pos += 1  # skip :
        start = self.pos
        while self.pos < len(self.source) and self._is_symbol_char(self.source[self.pos]):
            self.pos += 1
        name = self.source[start:self.pos]
        self.tokens.append(Token(TokenType.KEYWORD, name, self.line))

    def _read_number(self):
        start = self.pos
        while self.pos < len(self.source) and (self.source[self.pos].isdigit() or self.source[self.pos] == '.'):
            self.pos += 1
        value = self.source[start:self.pos]
        self.tokens.append(Token(TokenType.NUMBER, value, self.line))

    def _read_symbol(self):
        start = self.pos
        while self.pos < len(self.source) and self._is_symbol_char(self.source[self.pos]):
            self.pos += 1
        value = self.source[start:self.pos]
        if value == "true" or value == "false":
            self.tokens.append(Token(TokenType.BOOL, value, self.line))
        elif value == "nil":
            self.tokens.append(Token(TokenType.NIL, value, self.line))
        else:
            self.tokens.append(Token(TokenType.SYMBOL, value, self.line))

    @staticmethod
    def _is_symbol_start(ch: str) -> bool:
        return ch.isalpha() or ch in '+-*/=<>!?_'

    @staticmethod
    def _is_symbol_char(ch: str) -> bool:
        return ch.isalnum() or ch in '+-*/=<>!?_-'
