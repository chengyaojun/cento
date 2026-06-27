from src.lexer import TokenType, Token
from src.ast_nodes import *
from src.errors import CentoError


class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def parse(self) -> Program:
        expressions = []
        while not self._at_end():
            expressions.append(self._parse_expr())
        return Program(expressions)

    def _parse_expr(self):
        token = self._peek()
        if token.type == TokenType.NUMBER:
            return self._parse_number()
        elif token.type == TokenType.STRING:
            return self._parse_string()
        elif token.type == TokenType.BOOL:
            return self._parse_bool()
        elif token.type == TokenType.NIL:
            self._advance()
            return NilLiteral()
        elif token.type == TokenType.KEYWORD:
            return self._parse_keyword()
        elif token.type == TokenType.SYMBOL:
            return self._parse_symbol()
        elif token.type == TokenType.LBRACKET:
            return self._parse_list()
        elif token.type == TokenType.LBRACE:
            return self._parse_map()
        elif token.type == TokenType.LPAREN:
            return self._parse_form()
        else:
            raise CentoError(f"Unexpected token: {token.value} at line {token.line}")

    def _parse_number(self):
        token = self._advance()
        return NumberLiteral(float(token.value))

    def _parse_string(self):
        token = self._advance()
        return StringLiteral(token.value)

    def _parse_bool(self):
        token = self._advance()
        return BoolLiteral(token.value == "true")

    def _parse_keyword(self):
        token = self._advance()
        return KeywordLiteral(token.value)

    def _parse_symbol(self):
        token = self._advance()
        return SymbolRef(token.value)

    def _parse_list(self):
        self._expect(TokenType.LBRACKET)
        elements = []
        while self._peek().type != TokenType.RBRACKET:
            elements.append(self._parse_expr())
        self._expect(TokenType.RBRACKET)
        return ListLiteral(elements)

    def _parse_map(self):
        self._expect(TokenType.LBRACE)
        pairs = []
        while self._peek().type != TokenType.RBRACE:
            key = self._parse_expr()
            if not isinstance(key, KeywordLiteral):
                raise CentoError(f"Map keys must be keywords, got {type(key).__name__}")
            value = self._parse_expr()
            pairs.append((key, value))
        self._expect(TokenType.RBRACE)
        return MapLiteral(pairs)

    def _parse_form(self):
        self._expect(TokenType.LPAREN)
        token = self._peek()
        if token.type == TokenType.SYMBOL:
            if token.value == "let":
                result = self._parse_let()
            elif token.value == "fn":
                result = self._parse_fn()
            elif token.value == "if":
                result = self._parse_if()
            elif token.value == "import":
                result = self._parse_import()
            elif token.value == "try":
                result = self._parse_try()
            else:
                result = self._parse_call()
        else:
            result = self._parse_call()
        self._expect(TokenType.RPAREN)
        return result

    def _parse_call(self):
        # We're already past LPAREN
        callee = self._parse_expr()
        args = []
        while self._peek().type != TokenType.RPAREN:
            args.append(self._parse_expr())
        return CallExpr(callee=callee, args=args)

    def _parse_let(self):
        self._advance()  # skip 'let'
        self._expect(TokenType.LBRACKET)
        bindings = []
        while self._peek().type != TokenType.RBRACKET:
            name_token = self._expect(TokenType.SYMBOL)
            value_expr = self._parse_expr()
            bindings.append((name_token.value, value_expr))
        self._expect(TokenType.RBRACKET)
        body = []
        while self._peek().type != TokenType.RPAREN:
            body.append(self._parse_expr())
        return LetExpr(bindings=bindings, body=body)

    def _parse_fn(self):
        self._advance()  # skip 'fn'
        name = None
        if self._peek().type == TokenType.SYMBOL and self._peek().value != "[":
            name = self._advance().value
        self._expect(TokenType.LBRACKET)
        fixed_params = []
        rest_param = None
        while self._peek().type != TokenType.RBRACKET:
            tok = self._advance()
            if tok.type != TokenType.SYMBOL:
                raise CentoError(f"Expected parameter name, got {tok.type.name} at line {tok.line}")
            if tok.value == "&":
                if rest_param is not None:
                    raise CentoError(f"Multiple & in parameter list at line {tok.line}")
                if self._peek().type != TokenType.SYMBOL or self._peek().value == "&":
                    raise CentoError(f"Expected parameter name after & at line {tok.line}")
                rest_param = self._advance().value
            else:
                if rest_param is not None:
                    raise CentoError(f"Parameter after rest parameter at line {tok.line}")
                fixed_params.append(tok.value)
        self._expect(TokenType.RBRACKET)
        body = []
        while self._peek().type != TokenType.RPAREN:
            body.append(self._parse_expr())
        return FnExpr(name=name, fixed_params=fixed_params, rest_param=rest_param, body=body)

    def _parse_if(self):
        self._advance()  # skip 'if'
        condition = self._parse_expr()
        then_branch = self._parse_expr()
        else_branch = None
        if self._peek().type != TokenType.RPAREN:
            else_branch = self._parse_expr()
        return IfExpr(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _parse_import(self):
        self._advance()  # skip 'import'
        path = self._expect(TokenType.STRING).value
        symbols = []
        if self._peek().type == TokenType.LBRACKET:
            self._advance()  # skip [
            while self._peek().type != TokenType.RBRACKET:
                name = self._expect(TokenType.SYMBOL).value
                alias = None
                if self._peek().type == TokenType.KEYWORD and self._peek().value == "as":
                    self._advance()  # skip :as
                    alias = self._expect(TokenType.SYMBOL).value
                symbols.append((name, alias))
            self._expect(TokenType.RBRACKET)
        return ImportExpr(path=path, symbols=symbols)

    def _parse_try(self):
        self._advance()  # skip 'try'
        body = []
        catch_param = None
        catch_body = None
        finally_body = None
        # Parse body expressions until catch or finally
        while True:
            if self._peek().type == TokenType.LPAREN:
                next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
                if next_tok and next_tok.type == TokenType.SYMBOL and next_tok.value in ("catch", "finally"):
                    break
            if self._peek().type == TokenType.RPAREN:
                break
            body.append(self._parse_expr())
        # Parse catch
        if self._peek().type == TokenType.LPAREN:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.SYMBOL and next_tok.value == "catch":
                self._advance()  # skip (
                self._advance()  # skip catch
                self._expect(TokenType.LBRACKET)
                catch_param = self._expect(TokenType.SYMBOL).value
                self._expect(TokenType.RBRACKET)
                catch_body = []
                while self._peek().type != TokenType.RPAREN:
                    catch_body.append(self._parse_expr())
                self._expect(TokenType.RPAREN)
        # Parse finally
        if self._peek().type == TokenType.LPAREN:
            next_tok = self.tokens[self.pos + 1] if self.pos + 1 < len(self.tokens) else None
            if next_tok and next_tok.type == TokenType.SYMBOL and next_tok.value == "finally":
                self._advance()  # skip (
                self._advance()  # skip finally
                finally_body = []
                while self._peek().type != TokenType.RPAREN:
                    finally_body.append(self._parse_expr())
                self._expect(TokenType.RPAREN)
        return TryExpr(body=body, catch_param=catch_param, catch_body=catch_body, finally_body=finally_body)

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _expect(self, token_type: TokenType) -> Token:
        token = self._advance()
        if token.type != token_type:
            raise CentoError(f"Expected {token_type.name}, got {token.type.name} ('{token.value}') at line {token.line}")
        return token
