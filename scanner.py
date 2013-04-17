#!/usr/bin/env python
#
# Scanner(Lexer) for Mini Triangle
#
# Author: Wilson Giese
#

import cStringIO as StringIO
import string

# Token Constants
TK_IDENTIFIER = 0   # Function names, class names, variable names, etc...
TK_INTLITERAL = 1
TK_OPERATOR   = 2   # + | - | * | / | < | > | = | \
TK_BEGIN      = 3   # begin
TK_CONST      = 4   # const
TK_DO         = 5   # do
TK_ELSE       = 6   # else
TK_END        = 7   # end
TK_IF         = 8   # if
TK_IN         = 9   # in
TK_LET        = 10  # let
TK_THEN       = 11  # then
TK_VAR        = 12  # var
TK_WHILE      = 13  # while
TK_SEMICOLON  = 14  # ;
TK_COLON      = 15  # :
TK_BECOMES    = 16  # :=
TK_IS         = 17  # ~
TK_LPAREN     = 18  # (
TK_RPAREN     = 19  # )
TK_EOT        = 20  # end of text
TK_FUNCDEF    = 21  # func
TK_RETURN     = 22  # return
TK_COMMA      = 23  # ,

TOKENS = {TK_IDENTIFIER: 'IDENTIFIER',
          TK_INTLITERAL: 'INTLITERAL',
          TK_OPERATOR:   'OPERATOR',
          TK_BEGIN:      'BEGIN',
          TK_CONST:      'CONST',
          TK_DO:         'DO',
          TK_ELSE:       'ELSE',
          TK_END:        'END',
          TK_IF:         'IF',
          TK_IN:         'IN',
          TK_LET:        'LET',
          TK_THEN:       'THEN',
          TK_VAR:        'VAR',
          TK_WHILE:      'WHILE',
          TK_SEMICOLON:  'SEMICOLON',
          TK_COLON:      'COLON',
          TK_BECOMES:    'BECOMES',
          TK_IS:         'IS',
          TK_LPAREN:     'LPAREN',
          TK_RPAREN:     'RPAREN',
          TK_EOT:        'EOT',
          TK_FUNCDEF:    'FUNCDEF',
          TK_RETURN:     'RETURN',
          TK_COMMA:      'COMMA'}

KEYWORDS = {'begin':  TK_BEGIN,
            'const':  TK_CONST,
            'do':     TK_DO,
            'else':   TK_ELSE,
            'end':    TK_END,
            'if':     TK_IF,
            'in':     TK_IN,
            'let':    TK_LET,
            'then':   TK_THEN,
            'var':    TK_VAR,
            'while':  TK_WHILE,
            'func':   TK_FUNCDEF,
            'return': TK_RETURN}

OPERATORS = ['+', '*', '-', '/', '<', '>', '=', '!=', '\\']


class Token(object):
    """ A simple Token structure.

        Contains the token type, value and position.
    """
    def __init__(self, type, val, pos):
        self.type = type
        self.val = val
        self.pos = pos

    def __str__(self):
        return '(%s(%s) at %s)' % (TOKENS[self.type], self.val, self.pos)

    def __repr__(self):
        return self.__str__()


class ScannerError(Exception):
    """ Scanner error exception.

        pos: position in the input text where the error occurred.
    """
    def __init__(self, pos, char):
        self.pos = pos
        self.char = char

    def __str__(self):
        return 'ScannerError at pos = %d, char = %s' % (self.pos, self.char)


class Scanner(object):
    """Scanner for the following token grammar

    Token     ::=  Letter (Letter | Digit)* | Digit Digit* |
                   '+' | '-' | '*' | '/' | '<' | '>' | '=' | '\'
                   ':' ('=' | <empty>) | ';' | '~' | '(' | ')' | <eot>

    Separator ::=  '!' Graphic* <eol> | <space> | <eol>
    """

    def __init__(self, input):
        # Use StringIO to treat input string like a file.
        self.inputstr = StringIO.StringIO(input)
        self.eot = False   # Are we at the end of the input text?
        self.pos = 0       # Position in the input text
        self.char = ''     # The current character from the input text
        self.char_take()   # Fill self.char with the first character

    def scan(self):
        """Main entry point to scanner object.

        Return a list of Tokens.
        """

        self.tokens = []
        while 1:
            token = self.scan_token()
            self.tokens.append(token)

            if token.type == TK_EOT:
                break
        return self.tokens

    def scan_token(self):
        """Scan a single token from input text.

        Return a Token.
        """

        c = self.char_current()
        token = None

        while not self.char_eot():
            # Remove spaces
            if c.isspace():
                self.char_take()
                c = self.char_current()
                continue

            # Remove Comments
            if c == '!':
                while self.char_current() != '\n' and not self.char_eot():
                    self.char_take()
                c = self.char_current()
                continue

            if c.isdigit():   # Integer
                token = self.scan_int()
                break
            elif c.isalpha():  # Keyword/Identifier
                pos = self.char_pos()
                word = self.scan_keyword()

                # Get type from dictionary
                token_type = KEYWORDS.get(word)

                if token_type is None:  # Not a keyword
                    token = Token(TK_IDENTIFIER, word, pos)
                else:  # Is a keyword
                    token = Token(token_type, 0, pos)
                break
            elif c in OPERATORS:
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_OPERATOR, val, pos)
                break
            elif c == ';':
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_SEMICOLON, 0, pos)
                break
            elif c == ':':
                pos = self.char_pos()
                val = self.char_take()

                # Check for becomes(:=) token
                if(self.char_current() == '='):
                    val += self.char_take()
                    token = Token(TK_BECOMES, 0, pos)
                else:
                    token = Token(TK_COLON, 0, pos)
                break
            elif c == '~':
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_IS, 0, pos)
                break
            elif c == '(':
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_LPAREN, 0, pos)
                break
            elif c == ')':
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_RPAREN, 0, pos)
                break
            elif c == ',':
                pos = self.char_pos()
                val = self.char_take()
                token = Token(TK_COMMA, 0, pos)
                break
            else:
                raise ScannerError(self.char_pos(), self.char_current())

        # Finished building token
        if token is not None:
            return token

        if self.char_eot():
            return(Token(TK_EOT, 0, self.char_pos()))

    def scan_int(self):
        """Int :== Digit (Digit*)"""

        pos = self.char_pos()
        numlist = [self.char_take()]

        while self.char_current().isdigit():
            numlist.append(self.char_take())

        return Token(TK_INTLITERAL, int(string.join(numlist, '')), pos)

    def scan_keyword(self):
        """Scans and builds keyword. Terminates on any non-alpha or non-digit character

        Note: Keywords CANNOT start with digits. Those should all be considered ints
        """
        word = self.char_take()

        while self.char_current().isalpha() or self.char_current().isdigit():
            word += self.char_take()

        return word

    def char_current(self):
        """Return in the current input character."""

        return self.char

    def char_take(self):
        """Consume the current character and read the next character
        from the input text.

        Update self.char, self.eot, and self.pos
        """

        char_prev = self.char

        self.char = self.inputstr.read(1)
        if self.char == '':
            self.eot = True

        self.pos += 1

        return char_prev

    def char_pos(self):
        """Return the position of the *current* character in the input text."""

        return self.pos - 1

    def char_eot(self):
        """Determine if we are at the end of the input text."""

        return self.eot
