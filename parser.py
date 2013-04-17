#!/usr/bin/env python
#
# Parser for Mini Triangle
#
# Author: Wilson Giese
#

import ast as ast
import scanner as scanner


class ParserException(Exception):

    def __init__(self, pos, type, exp_type=''):
        self.pos = pos
        self.type = type
        self.exp_type = exp_type

    def __str__(self):
        if self.exp_type != '':
            return ('ParserException: Found bad token %s at %d. Expected %s' %
                    (scanner.TOKENS[self.type], self.pos,
                    scanner.TOKENS[self.exp_type]))
        else:
            return ('ParserException: Found bad token %s at %d. ' %
                    (scanner.TOKENS[self.type], self.pos))


class Parser(object):

    def __init__(self, tokens):
        self.tokens = tokens
        self.curindex = 0
        self.curtoken = tokens[0]

    def parse(self):
        """Parse the token stream"""
        return self.parse_program()

    def parse_program(self):
        """Command """

        program = ast.Program(self.parse_command())
        self.token_accept(scanner.TK_EOT)
        return program

    def parse_command(self):
        """ single-Command ( single-Command )* """

        c1 = self.parse_single_command()
        # Look for single_commands until we do not encounter an END or EOT
        while self.curtoken.type != scanner.TK_END and self.curtoken.type != scanner.TK_EOT:
            c2 = self.parse_single_command()
            c1 = ast.SequentialCommand(c1, c2)

        return c1

    def parse_single_command(self):
        """V-name ':=' Expression ';'
        |  call-command ';'
        |  if Expression then single-Command else single-Command
        |  while Expression do single-Command
        |  let Declaration in single-Command
        |  begin Command end
        """
        # Assignment or Function Call
        if self.curtoken.type == scanner.TK_IDENTIFIER:
            name = self.token_current().val
            self.token_accept_any()

            # Variable Assignment
            if self.curtoken.type == scanner.TK_BECOMES:
                self.token_accept_any()
                expr = self.parse_expression()
                self.token_accept(scanner.TK_SEMICOLON)
                return ast.AssignCommand(ast.Vname(name), expr)
            # Function call
            elif self.curtoken.type == scanner.TK_LPAREN:
                self.token_accept_any()
                param_list = self.parse_argument_list()
                self.token_accept(scanner.TK_RPAREN)
                self.token_accept(scanner.TK_SEMICOLON)
                return ast.CallCommand(name, param_list)
            # Unexpected tokens
            else:
                raise ParserException(self.curtoken.pos, self.curtoken.type)
        # While Loop
        elif self.curtoken.type == scanner.TK_WHILE:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_DO)
            com = self.parse_single_command()
            return ast.WhileCommand(expr, com)
        # If Statement
        elif self.curtoken.type == scanner.TK_IF:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_THEN)
            com1 = self.parse_single_command()
            self.token_accept(scanner.TK_ELSE)
            com2 = self.parse_single_command()
            return ast.IfCommand(expr, com1, com2)
        # Let-In Statement
        elif self.curtoken.type == scanner.TK_LET:
            self.token_accept_any()
            dec = self.parse_declaration()
            self.token_accept(scanner.TK_IN)
            com = self.parse_single_command()
            return ast.LetCommand(dec, com)
        # Begin-End Statement
        elif self.curtoken.type == scanner.TK_BEGIN:
            self.token_accept_any()
            com = self.parse_command()
            self.token_accept(scanner.TK_END)
            return com
        elif self.curtoken.type == scanner.TK_RETURN:
            self.token_accept_any()
            expr = self.parse_expression()
            self.token_accept(scanner.TK_SEMICOLON)
            return ast.ReturnCommand(expr)
        # Unexpected tokens
        else:
            raise ParserException(self.curtoken.pos, self.curtoken.type)

    def parse_expression(self):
        """Ter-Expression ( Oper-Ter Ter-Expression )* """

        e1 = self.parse_tertiary_expression()
        token = self.token_current()
        while token.type == scanner.TK_OPERATOR and token.val in ['<', '>', '=']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_tertiary_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_tertiary_expression(self):
        """ Sec-Expression ( Oper-Sec Sec-Expression )* """

        e1 = self.parse_secondary_expression()
        token = self.token_current()
        while token.type == scanner.TK_OPERATOR and token.val in ['+', '-']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_secondary_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_secondary_expression(self):
        """ Pri-Expression ( Oper-Pri Pri-Expression )* """

        e1 = self.parse_primary_expression()
        token = self.token_current()
        while token.type == scanner.TK_OPERATOR and token.val in ['*', '/', '']:
            oper = token.val
            self.token_accept_any()
            e2 = self.parse_primary_expression()
            token = self.token_current()
            e1 = ast.BinaryExpression(e1, oper, e2)
        return e1

    def parse_primary_expression(self):
        """Integer-Literal
        |  V-name
        |  Operator primary-Expression
        |  '(' Expression ')'
        |  function-call
        """

        token = self.token_current()
        # Integer-Literal
        if token.type == scanner.TK_INTLITERAL:
            e1 = ast.IntegerExpression(token.val)
            self.token_accept_any()
        # Variable name or function call
        elif token.type == scanner.TK_IDENTIFIER:
            name = self.token_current().val
            self.token_accept_any()

            # Function call
            if self.curtoken.type == scanner.TK_LPAREN:
                self.token_accept_any()
                param_list = self.parse_argument_list()
                self.token_accept(scanner.TK_RPAREN)
                e1 = ast.CallCommand(name, param_list)
            # Variable name
            else:
                e1 = ast.VnameExpression(ast.Vname(name))
        # Unary Expression
        elif token.type == scanner.TK_OPERATOR:
            oper = self.token_current()
            self.token_accept_any()
            e1 = ast.UnaryExpression(oper.val, self.parse_primary_expression())
        # ( Expression )
        elif token.type == scanner.TK_LPAREN:
            self.token_accept_any()
            e1 = self.parse_expression()
            self.token_accept(scanner.TK_RPAREN)
        # Unexpected tokens
        else:
            raise ParserException(self.curtoken.pos, self.curtoken.type)
        return e1

    def parse_declaration(self):
        """single-Declaration ( single-Declaration )* """

        d1 = self.parse_single_declaration()
        # Look for single_declarations until we do not encounter IN
        while self.curtoken.type != scanner.TK_IN:
            d2 = self.parse_single_declaration()
            d1 = ast.SequentialDeclaration(d1, d2)
        return d1

    def parse_single_declaration(self):
        """const Identifier ~ Expression ';'
        |  var Identifier : Type-denoter ';'
        |  func Identifier '(' parameter-list ')' ':'' Type-denoter single-Command
        """

        # Constant Declaration
        if self.curtoken.type == scanner.TK_CONST:
            self.token_accept_any()
            name = self.token_current().val
            self.token_accept(scanner.TK_IDENTIFIER)
            self.token_accept(scanner.TK_IS)
            expr = self.parse_expression()
            self.token_accept(scanner.TK_SEMICOLON)
            return ast.ConstDeclaration(name, expr)
        # Variable Declaration
        elif self.curtoken.type == scanner.TK_VAR:
            self.token_accept_any()
            name = self.token_current().val
            self.token_accept(scanner.TK_IDENTIFIER)
            self.token_accept(scanner.TK_COLON)
            type_d = ast.TypeDenoter(self.token_current().val)
            self.token_accept(scanner.TK_IDENTIFIER)
            self.token_accept(scanner.TK_SEMICOLON)
            return ast.VarDeclaration(name, type_d)
        # Function Declaration
        elif self.curtoken.type == scanner.TK_FUNCDEF:
            return self.parse_function_declaration()
        # Unexpected tokens
        else:
            raise ParserException(self.curtoken.pos, self.curtoken.type)

    def parse_function_declaration(self):
        self.token_accept(scanner.TK_FUNCDEF)
        name = self.token_current().val
        self.token_accept(scanner.TK_IDENTIFIER)
        self.token_accept(scanner.TK_LPAREN)
        param_list = self.parse_parameter_list()
        self.token_accept(scanner.TK_RPAREN)
        self.token_accept(scanner.TK_COLON)
        return_type = self.token_current().val
        self.token_accept(scanner.TK_IDENTIFIER)
        com = self.parse_single_command()
        return ast.FunctionDeclaration(name, param_list, return_type, com)

    def parse_parameter_list(self):
        """ Identifier ':' 'Type-denoter' ( ',' Identifier : Type-denoter )*
        Returns a list of tuples with the format [(Vname(var_name), TypeDenoter(var_type)),...]
        """

        param_list = []
        var_name = self.token_current().val
        self.token_accept(scanner.TK_IDENTIFIER)
        self.token_accept(scanner.TK_COLON)
        var_type = self.token_current().val
        self.token_accept(scanner.TK_IDENTIFIER)
        param_list.append((ast.Vname(var_name), ast.TypeDenoter(var_type)))

        while self.curtoken.type == scanner.TK_COMMA:
            self.token_accept_any()
            var_name = self.token_current().val
            self.token_accept(scanner.TK_IDENTIFIER)
            self.token_accept(scanner.TK_COLON)
            var_type = self.token_current().val
            self.token_accept(scanner.TK_IDENTIFIER)
            param_list.append((ast.Vname(var_name), ast.TypeDenoter(var_type)))
        return param_list

    def parse_argument_list(self):
        """ Expression ( ',' Expression )* """
        arg_list = []
        if self.curtoken.type != scanner.TK_RPAREN:
            arg_list.append(self.parse_expression())
        else:
            return arg_list

        while self.curtoken.type == scanner.TK_COMMA:
            self.token_accept_any()
            arg_list.append(self.parse_expression())
        return arg_list

    def token_current(self):
        """Return curent token"""
        return self.curtoken

    def token_accept_any(self):
        """Remove Token except EOT"""

        if self.curtoken.type != scanner.TK_EOT:
            self.curindex += 1
            self.curtoken = self.tokens[self.curindex]

    def token_look_ahead(self):
        if self.curtoken.tye != scanner.TK_EOT:
            forward_token = self.tokens[self.curindex + 1]
        else:
            forward_token = self.curtoken
        return forward_token

    def token_accept(self, type):
        """Check and then remove token"""
        if self.curtoken.type != type:
            raise ParserException(self.curtoken.pos, self.curtoken.type,
                                  exp_type=type)
        self.token_accept_any()


if __name__ == '__main__':
    pass
