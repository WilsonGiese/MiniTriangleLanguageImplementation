Mini Triangle Language Implementation
==================================
Wilson Giese - giese.wilson@gmail.com

About
-----

This is a compiler for the "MiniTriangle" language. MiniTriangle is a small language I used to become famailiar with the ideas of Programming Language implementation. This language is compiled to Python Bytecode, and the compiler will create fully executable ".pyc" files which will run on the Python stack machine. See the [EBNF](https://github.com/WilsonGiese/MiniTriangleLanguageImplementation/blob/master/EBNF) for this version of MiniTriangle grammar. 


Features
--------
- Integer type(with arbitrary precision thanks to Python's stack machine). 
- Function definitions/calls
- Control structures(If-else, while loops, etc...)
- Precedence
- [EBNF](https://github.com/WilsonGiese/MiniTriangleLanguageImplementation/blob/master/EBNF)


Compiling and Running MiniTriangle
----------------------------------
    $ python codegen.py <YourFile>.mt
    $ pyhon <YourFile>.pyc
    
The [Byteplay](https://code.google.com/p/byteplay/) library is required to compile this language, but once compiled it is not needed to run the PYC files. 


Features to Implement
---------------------
- Types: Floating point type, char type, and array type. 
- Method to include and link external files/libraries
