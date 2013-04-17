#!/usr/bin/env python
#
# Code generator for Mini Triangle
#
# Author: Wilson Giese 
#

from byteplay import *
from types import CodeType, FunctionType

import imp
import marshal
import os
import struct
import sys
import time

import ast
import parser
import scanner


class CodeGeneratorError(Exception):
    """ Code Generator Exception """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node: %s' % (str(self.ast))


class TypeMismatchError(CodeGeneratorError):
    """ Exception for type mismatch(i.e Integer := String) """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node; Type Mismatch: %s' % (str(self.ast))


class InvalidExpressionError(CodeGeneratorError):
    """ Exception for invalid expressions """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node; Invalid Expression: %s' % (str(self.ast))


class InvalidDeclarationError(CodeGeneratorError):
    """ Exception for invalid declarations """

    def __init__(self, ast):
        self.ast = ast

    def __str__(self):
        return 'Error at ast node; Invalid Declaration: %s' % (str(self.ast))


class UnknownFunctionError(CodeGeneratorError):
    """ Exception for unknown function calls """

    def __init__(self, func_name):
        self.func_name = func_name

    def __str__(self):
        return 'Error at ast node; Unknown Function: %s' % (func_name)


class IllegalFunctionArgumentError(CodeGeneratorError):
    """ Exception for invalid function parameters """

    def __init__(self, func_name, argc):
        self.func_name = func_name
        self.argc = argc

    def __str__(self):
        return 'Error at ast node; Illegal Arguments.\nFunction: %s takes exactly %d arguments.' % (self.func_name, self.argc)


# Environment format:
#   key = name
#   val = (type, writable(True/False))
#
class CodeGen(object):
    """ Code Generator for Mini-Triangle """

    def __init__(self, tree):
        self.tree = tree
        self.code = []
        # We need to create a stack of codes to keep track of current scope
        # We also need to store all of these scopes for pyc generation
        self.code_stacks = []
        self.code_stacks.append(self.code)
        # let_num will be used to name the let "functions"
        self.scope_depth = 0
        # We also need a list of environments for each scope(For typechecking and such)
        self.envs = []
        self.envs.append({})
        # Format [func name: param list, return type)]
        self.declared_functions = {}
        self.scope_vars = {}

    def __str__(self):
        return 'Code: %s' % (str(self.code))

    def generate(self):
        if type(self.tree) is not ast.Program:
            raise CodeGeneratorError(self.tree)

        self.gen_command(self.tree.command)
        self.code.append((LOAD_CONST, 0))  # Segfault without this
        self.code.append((RETURN_VALUE, None))
        code_obj = Code(self.code, [], [], False, False, False, 'gencode', '', 0, '')
        code = code_obj.to_code()
        func = FunctionType(code, globals(), 'gencode')

        return func

    def gen_command(self, node):
        """ Generate bytecode for all command types. """
        type_ = type(node)

        if type_ is ast.SequentialCommand:
            self.gen_command(node.command1)
            self.gen_command(node.command2)
        elif type_ is ast.AssignCommand:
            self.gen_expression(node.expression)
            vname = self.lookup_var(node.variable.identifier)
            if vname is None:
                raise InvalidExpressionError(node)
            self.code.append((STORE_FAST, vname))
        elif type_ is ast.CallCommand:
            # Code generation for getint function
            if node.identifier == 'getint':
                if len(node.expr_list) != 0:
                    raise IllegalFunctionArgumentError('getint', 0)

                self.code.append((LOAD_GLOBAL, 'input'))
                self.code.append((CALL_FUNCTION, 0))
            # Code generation for putint function
            elif node.identifier == 'putint':
                if len(node.expr_list) != 1:
                    raise IllegalFunctionArgumentError('putint', 1)
                self.gen_expression(node.expr_list[0])
                self.code.append((PRINT_ITEM, None))
                self.code.append((PRINT_NEWLINE, None))
            # Code generation for declared functions
            else:
                self.gen_call_command(node)
        elif type_ is ast.IfCommand:
            label_else = Label()
            label_if = Label()

            self.gen_expression(node.expression)
            self.code.append((POP_JUMP_IF_FALSE, label_else))
            self.gen_command(node.command1)
            self.code.append((JUMP_FORWARD, label_if))
            self.code.append((label_else, None))
            self.gen_command(node.command2)
            self.code.append((label_if, None))

        elif type_ is ast.WhileCommand:
            label_loop_test = Label()
            label_loop_done = Label()

            # Jump here to test retest condition.
            self.code.append((label_loop_test, None))
            self.gen_expression(node.expression)
            self.code.append((POP_JUMP_IF_FALSE, label_loop_done))
            self.gen_command(node.command)
            self.code.append((JUMP_ABSOLUTE, label_loop_test))
            # Jump here if condition fails.
            self.code.append((label_loop_done, None))
        elif type_ is ast.LetCommand:
            self.raise_scope()
            self.gen_declaration(node.declaration)
            self.gen_command(node.command)
            self.lower_scope()
        elif type_ is ast.ReturnCommand:
            self.gen_expression(node.expression)
            self.code.append((RETURN_VALUE, None))

        else:  # Unexpected node. Raise a Code Generation Exception.
            raise CodeGeneratorError(node)

    def gen_expression(self, node):
        """ Generate bytecode for an expression """
        type_ = type(node)

        if type_ is ast.BinaryExpression:
            self.gen_expression(node.expr1)
            self.gen_expression(node.expr2)

            # Call bytecode function for this operator
            if node.oper == '+':
                self.code.append((BINARY_ADD, None))
            elif node.oper == '*':
                self.code.append((BINARY_MULTIPLY, None))
            elif node.oper == '-':
                self.code.append((BINARY_SUBTRACT, None))
            elif node.oper == '/':
                self.code.append((BINARY_DIVIDE, None))
            elif node.oper == '<' or node.oper == '>':
                self.code.append((COMPARE_OP, node.oper))
            elif node.oper == '=':
                self.code.append((COMPARE_OP, '=='))
            elif node.oper == '\\':
                self.code.append((BINARY_MODULO, None))
            else:
                raise InvalidExpressionError(node)
        elif type_ is ast.IntegerExpression:
            self.code.append((LOAD_CONST, node.value))
        elif type_ is ast.VnameExpression:
            vname = self.lookup_var(node.variable.identifier)
            if vname is None:
                raise InvalidExpressionError(node)
            self.code.append((LOAD_FAST, vname))
        elif type_ is ast.UnaryExpression:
            self.gen_expression(node.expression)

            # Only supporting positive or negative unary
            if node.operator == '+':
                self.code.append((UNARY_POSITIVE, None))
            elif node.operator == '-':
                self.code.append((UNARY_NEGATIVE, None))
            else:
                raise InvalidExpressionError(node)
        elif type_ is ast.CallCommand:
            self.gen_command(node)
        else:
            raise InvalidExpressionError(node)

    def gen_declaration(self, node):
        """ Generate bytecode for a declaration """
        type_ = type(node)

        if type_ is ast.ConstDeclaration:
            self.gen_expression(node.expression)
            # Load const into env
            cur_env = self.get_current_env()
            cur_env[node.identifier] = ('Integer', False)
            self.add_var(node.identifier)
            vname = self.lookup_var(node.identifier)
            if vname is None:
                raise InvalidExpressionError(node)
            self.code.append((STORE_FAST, vname))
        elif type_ is ast.VarDeclaration:
            # Declare variable in environment
            cur_env = self.get_current_env()
            self.env_load(node.identifier, node.type_denoter, True)
            self.add_var(node.identifier)
            self.code.append((LOAD_CONST, None))
            vname = self.lookup_var(node.identifier)
            if vname is None:
                raise InvalidExpressionError(node)
            self.code.append((STORE_FAST, vname))
        elif type_ is ast.SequentialDeclaration:
            self.gen_declaration(node.decl1)
            self.gen_declaration(node.decl2)
        elif type_ is ast.FunctionDeclaration:
            self.gen_function(node)
        else:
            raise InvalidDeclarationError(node)

    def gen_function(self, node):
        self.raise_code_stack()
        # Add func name early incase of recursive calls
        self.declared_functions[node.name] = (node.arg_list, node.return_type_denoter)
        # Get all arg names for code_obj args
        arg_names = []
        for arg in node.arg_list:
            vname = arg[0].identifier
            self.env_load(vname, arg[1], True)
            vname = self.add_var(vname)
            arg_names.append(vname)

        # Genrate function body
        self.gen_command(node.command)

        # Add function to environment(For calling and type cheking)
        code_obj = Code(self.code, [], arg_names, False, False, True, node.name, '', 0, '')

        # Make function from code object
        self.lower_code_stack()
        self.code.append((LOAD_CONST, code_obj))
        self.code.append((MAKE_FUNCTION, 0))
        self.code.append((STORE_NAME, node.name))

    def gen_call_command(self, node):
        """ Generates code for program defined functions """
        if self.declared_functions.get(node.identifier) is not None:
            argc = len(self.declared_functions.get(node.identifier)[0])
            if argc != len(node.expr_list):
                raise IllegalFunctionArgumentError(node.identifier, argc)

            self.code.append((LOAD_GLOBAL, node.identifier))
            for e in node.expr_list:
                self.gen_expression(e)
            self.code.append((CALL_FUNCTION, argc))
            #self.code.append((POP_TOP, None))
        else:
            raise InvalidExpressionError(node)

    # ENVIRONMENT INTERACTION FUNCTIONS
    def get_current_env(self):
        return self.envs[len(self.envs)-1]

    def env_load(self, name, type_denoter, writable):
        self.get_current_env()[name] = (type_denoter, writable)

    # SCOPING FUNCTIONS
    def raise_code_stack(self):
        """
        Add a new code list to the code stack, and use as current scope.
        A new environment for the current scope is pushed onto the environment stack.
        """
        new_code = []
        self.code_stacks.append(new_code)
        self.code = new_code
        self.raise_scope()

    def lower_code_stack(self):
        """ Bring scope down one code list """
        self.code = self.code_stacks[len(self.code_stacks)-2]
        self.code_stacks.pop()
        self.lower_scope()

    # Scoping functions
    def add_var(self, var_name):
        var_list = self.scope_vars.get(var_name)

        if var_list is None:
            var_list = []
            self.scope_vars[var_name] = var_list

        if self.scope_depth == 0:
            var_list.append(var_name)
            return var_name
        else:
            var_list.append(var_name + str(self.scope_depth))
            return var_name + str(self.scope_depth)

    def lookup_var(self, var_name):
        var_list = self.scope_vars.get(var_name)
        if var_list is None:
            return None
        else:
            return var_list[len(var_list)-1]

    def raise_scope(self):
        self.envs.append({})
        self.scope_depth += 1

    def lower_scope(self):
        for x in self.get_current_env():
            self.scope_vars[x].pop()

        self.envs.pop()
        self.scope_depth -= 1

    # HELPER FUNCTIONS
    def print_code(self):
        for c in self.code:
            print c


def gen_pyc(code, name):
    pyc_file = name + '.pyc'

    with open(pyc_file, 'wb') as pyc_f:
        magic = int(imp.get_magic().encode('hex'), 16)
        pyc_f.write(struct.pack(">L", magic))
        pyc_f.write(struct.pack(">L", time.time()))
        marshal.dump(code.func_code, pyc_f)


if __name__ == '__main__':

    if len(sys.argv) == 2:
        try:
            source = open(sys.argv[1], 'r')
        except IOError:
            print 'Could not find source file: %s' % (sys.argv[1])
            sys.exit(0)

        # Split path to get name, and file info
        name_split = os.path.splitext(sys.argv[1])
        name = name_split[0]
        exten = name_split[1]

        if exten == '.mt':
            text = source.read()

            # Scan
            scan = scanner.Scanner(text)
            try:
                tokens = scan.scan()
            except scanner.ScannerError as e:
                print e
                sys.exit(0)

            # Parse
            parse = parser.Parser(tokens)
            try:
                tree = parse.parse()
            except parser.ParserException as e:
                print 'Could not compile source:'
                print e
                sys.exit(0)

            # Generate Code
            cg = CodeGen(tree)
            func = cg.generate()

            # Generate compiled Mini-Triangle code
            gen_pyc(func, name)

        else:
            print 'Error: Unrecoginized file type: Cannot compile \'%s\'' % (exten)
        source.close()
    else:
        print 'Usage: python %s /path/to/source' % (sys.argv[0])
