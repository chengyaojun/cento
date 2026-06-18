import pytest
from src.lexer import Lexer, TokenType, Token


def _tokens(source: str) -> list[Token]:
    """Tokenize and strip the trailing EOF token for easier assertion."""
    return [t for t in Lexer(source).tokenize() if t.type != TokenType.EOF]


def test_number():
    tokens = _tokens("42")
    assert tokens == [Token(TokenType.NUMBER, "42", 1)]

def test_float():
    tokens = _tokens("3.14")
    assert tokens == [Token(TokenType.NUMBER, "3.14", 1)]

def test_string():
    tokens = _tokens('"hello world"')
    assert tokens == [Token(TokenType.STRING, "hello world", 1)]

def test_bool():
    tokens = _tokens("true false")
    assert tokens == [
        Token(TokenType.BOOL, "true", 1),
        Token(TokenType.BOOL, "false", 1),
    ]

def test_nil():
    tokens = _tokens("nil")
    assert tokens == [Token(TokenType.NIL, "nil", 1)]

def test_symbol():
    tokens = _tokens("foo bar-baz")
    assert tokens == [
        Token(TokenType.SYMBOL, "foo", 1),
        Token(TokenType.SYMBOL, "bar-baz", 1),
    ]

def test_operator_symbols():
    tokens = _tokens("+ - * / > < = >= <=")
    assert tokens == [
        Token(TokenType.SYMBOL, "+", 1),
        Token(TokenType.SYMBOL, "-", 1),
        Token(TokenType.SYMBOL, "*", 1),
        Token(TokenType.SYMBOL, "/", 1),
        Token(TokenType.SYMBOL, ">", 1),
        Token(TokenType.SYMBOL, "<", 1),
        Token(TokenType.SYMBOL, "=", 1),
        Token(TokenType.SYMBOL, ">=", 1),
        Token(TokenType.SYMBOL, "<=", 1),
    ]

def test_keyword():
    tokens = _tokens(":name :age")
    assert tokens == [
        Token(TokenType.KEYWORD, "name", 1),
        Token(TokenType.KEYWORD, "age", 1),
    ]

def test_parens():
    tokens = _tokens("()")
    assert tokens == [
        Token(TokenType.LPAREN, "(", 1),
        Token(TokenType.RPAREN, ")", 1),
    ]

def test_brackets():
    tokens = _tokens("[]")
    assert tokens == [
        Token(TokenType.LBRACKET, "[", 1),
        Token(TokenType.RBRACKET, "]", 1),
    ]

def test_braces():
    tokens = _tokens("{}")
    assert tokens == [
        Token(TokenType.LBRACE, "{", 1),
        Token(TokenType.RBRACE, "}", 1),
    ]

def test_comment():
    tokens = _tokens("; this is a comment\n42")
    assert tokens == [Token(TokenType.NUMBER, "42", 2)]

def test_simple_expression():
    tokens = _tokens("(+ 1 2)")
    assert tokens == [
        Token(TokenType.LPAREN, "(", 1),
        Token(TokenType.SYMBOL, "+", 1),
        Token(TokenType.NUMBER, "1", 1),
        Token(TokenType.NUMBER, "2", 1),
        Token(TokenType.RPAREN, ")", 1),
    ]

def test_let_expression():
    code = '(let [x 10] (+ x 1))'
    tokens = _tokens(code)
    assert tokens == [
        Token(TokenType.LPAREN, "(", 1),
        Token(TokenType.SYMBOL, "let", 1),
        Token(TokenType.LBRACKET, "[", 1),
        Token(TokenType.SYMBOL, "x", 1),
        Token(TokenType.NUMBER, "10", 1),
        Token(TokenType.RBRACKET, "]", 1),
        Token(TokenType.LPAREN, "(", 1),
        Token(TokenType.SYMBOL, "+", 1),
        Token(TokenType.SYMBOL, "x", 1),
        Token(TokenType.NUMBER, "1", 1),
        Token(TokenType.RPAREN, ")", 1),
        Token(TokenType.RPAREN, ")", 1),
    ]

def test_unterminated_string():
    with pytest.raises(SyntaxError):
        Lexer('"hello').tokenize()

def test_unexpected_char():
    with pytest.raises(SyntaxError):
        Lexer("@").tokenize()
