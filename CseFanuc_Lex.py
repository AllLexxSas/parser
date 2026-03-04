#
# History
#
# Date          Name                Description of Change
# 10-Jul-2013   Kevin Chen          Creation
# 30-Nov-2013   Jason Fu            Add token "AXNUM", "AXISNUMADDRESS", "PRMVAR"
# 03-Jun-2016   Shuai Gao           Add token "ELSE" and "ENDIF"
# 16-Jun-2016   Shuai Gao           Enhance token "ELSE" by adding abbreviated EL
# 09-Aug-2016   Volker Grabowski    Use custom exception class to handle parse errors
# 02-Sep-2016   Volker Grabowski    Move CseParseError to CSEWrapper.py

import sys
import re
import os
import ply.lex as lex

runInConsole = 0
Debug = 0

if runInConsole == 0:
    from CSEWrapper import CseParseError

if Debug == 1:
    fileLog = open(os.path.split(os.path.realpath(__file__))[0] + r'\log.txt','a')
    logger = lex.PlyLogger(fileLog)

commVarNameList = []

# Get the token map
tokens = (
    "PROGNUMBER", "INTEGER_VALUE", "FLOAT_VALUE", "COMMENT", "FUNC", "ATAN", "AND", "XOR",
    "OR", "MOD", "BOOLOP", "GON", "GOF", "IF", "GOTO", "THEN", "ELSE", "ENDIF", "WHILE", "DO", "END", "POPEN", "BPRNT",
    "DPRNT", "PCLOS", "FLOATADDRESS", "PARAMETERADDRESS", "AXISADDRESS", "INTADDRESS", "SETVN", "VARNAME", "PRMVAR",
    "FILENAME", "EOL", "AXNUM", "AXISNUMADDRESS", 
    "PLUS", "MINUS", "TIMES", "DIVIDE"
          )

# Declare the state
states = (  ('commVarName','exclusive'),)

literals = ['M', 'N','G', '=', ':', '#', '[', ']', ',']

#t_EQUALS  = r'='
t_PLUS    = r'\+'
t_MINUS   = r'-'
t_TIMES   = r'\*'
t_DIVIDE  = r'/'

t_ignore = " \t"



def t_PROGNUMBER(t):
    r'O\d+'
    t.value = int(t.value[1: len(t.value)])
    return t

def t_FLOAT_VALUE_1(t):
    r'\d+\.\d*'
    t.value = float(t.value)
    t.type = "FLOAT_VALUE"
    return t

def t_FLOAT_VALUE_2(t):
    r'\.\d+'
    t.value = float(t.value)
    t.type = "FLOAT_VALUE"
    return t

def t_INTEGER_VALUE(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_COMMENT_2(t):
    r'\([^\)]*\)'
    t.type = "COMMENT"
    return t

def t_COMMENT_1(t):
    r'%[^\n]*'
    t.type = "COMMENT"
    return t

def t_FUNC_1(t):
    r'ROUND'
    t.type = "FUNC"
    return t

def t_FUNC_2(t):
    r'SQRT'
    t.type = "FUNC"
    return t

def t_FUNC_3(t):
    r'ABS'
    t.type = "FUNC"
    return t

def t_FUNC_4(t):
    r'ACOS'
    t.type = "FUNC"
    return t

def t_FUNC_5(t):
    r'ASIN'
    t.type = "FUNC"
    return t

def t_FUNC_6(t):
    r'BCD'
    t.type = "FUNC"
    return t

def t_FUNC_7(t):
    r'BIN'
    t.type = "FUNC"
    return t

def t_FUNC_8(t):
    r'COS'
    t.type = "FUNC"
    return t

def t_FUNC_9(t):
    r'FIX'
    t.type = "FUNC"
    return t

def t_FUNC_10(t):
    r'FUP'
    t.type = "FUNC"
    return t

def t_FUNC_11(t):
    r'SIN'
    t.type = "FUNC"
    return t

def t_FUNC_12(t):
    r'TAN'
    t.type = "FUNC"
    return t

def t_ATAN(t):
    r'ATAN'
    return t

def t_AND(t):
    r'AND'
    return t

def t_XOR(t):
    r'XOR'
    return t

def t_OR(t):
    r'OR'
    return t

def t_MOD(t):
    r'MOD'
    return t

def t_BOOLOP_1(t):
    r'EQ'
    t.type = "BOOLOP"
    return t

def t_BOOLOP_2(t):
    r'GE'
    t.type = "BOOLOP"
    return t

def t_BOOLOP_3(t):
    r'GT'
    t.type = "BOOLOP"
    return t

def t_BOOLOP_4(t):
    r'LE'
    t.type = "BOOLOP"
    return t

def t_BOOLOP_5(t):
    r'LT'
    t.type = "BOOLOP"
    return t

def t_BOOLOP_6(t):
    r'NE'
    t.type = "BOOLOP"
    return t

def t_GON(t):
    r'GON'
    return t

def t_GOF(t):
    r'GOF'
    return t

def t_IF(t):
    r'IF'
    return t

def t_GOTO(t):
    r'GOTO|GO'
    return t

def t_THEN(t):
    r'THEN'
    return t

def t_ELSE(t):
    r'ELSE|EL'
    return t

def t_ENDIF(t):
    r'ENDIF'
    return t

def t_WHILE(t):
    r'WHILE|WH'
    return t

def t_DO(t):
    r'DO'
    return t

def t_END(t):
    r'END|EN'
    return t

def t_POPEN(t):
    r'POPEN'
    return t

def t_BPDPPNT(t):
    r'(BPRNT|DPRNT)[ \t]*\[(\[[^\]]*\]|[^\]])*\]'
    ch = t.value[0]
    nPos = t.value.find('[')
    t.value = t.value[nPos+1:len(t.value)-1]
    if ch == 'B':
        t.type = "BPRNT"
    else:
        t.type = "DPRNT"
    return t

def t_PCLOS(t):
    r'PCLOS'
    return t

def t_SETVN(t):
    r'SETVN'
    return t

def t_PRMVAR(t):
    r'PRM'
    return t
    
def t_AXNUM(t):
    r'AXNUM'
    return t
    
def t_AXISNUMADDRESS(t):
    r'AX'
    return t
    
def t_FLOATADDRESS_1(t):
    r'D'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_2(t):
    r'E'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_3(t):
    r'F'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_4(t):
    r'H'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_5(t):
    r'Q'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_6(t):
    r'R'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_7(t):
    r'S'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_8(t):
    r'T'
    t.type = "FLOATADDRESS"
    return t

def t_FLOATADDRESS_9(t):
    r'P'
    t.type = "FLOATADDRESS"
    return t

def t_PARAMETERADDRESS_1(t):
    r'I'
    t.type = "PARAMETERADDRESS"
    return t

def t_PARAMETERADDRESS_2(t):
    r'J'
    t.type = "PARAMETERADDRESS"
    return t

def t_PARAMETERADDRESS_3(t):
    r'K'
    t.type = "PARAMETERADDRESS"
    return t

def t_AXISADDRESS_1(t):
    r'A'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_2(t):
    r'B'
    t.type = 'AXISADDRESS'
    return t

def t_AXISADDRESS_3(t):
    r'C'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_4(t):
    r'U'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_5(t):
    r'V'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_6(t):
    r'W'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_7(t):
    r'X'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_8(t):
    r'Y'
    t.type = "AXISADDRESS"
    return t

def t_AXISADDRESS_9(t):
    r'Z'
    t.type = "AXISADDRESS"
    return t

def t_INTADDRESS(t):
    r'L'
    return t

def t_VARNAME(t):
    r'\#[a-zA-Z_]\w{1,7}'
    t.value = t.value[1:len(t.value)]
    return t

def t_FILENAME(t):
    r'<[^>]*>'
    t.value = t.value[1:len(t.value)-1]
    return t

def start_commVarName(lexer):
    del commVarNameList[:]
    lexer.begin("commVarName")

@lex.TOKEN(r"[a-zA-Z]\w{1,7}")
def t_commVarName_char(t):
    commVarNameList.append(t.value)
    pass

@lex.TOKEN(r",")
def t_commVarName_separator(t):
    pass

@lex.TOKEN(r"\]")
def t_commVarName_quit(t):
    t.lexer.begin("INITIAL")
    pass

# Ignored characters (whitespace)
t_commVarName_ignore = " \t\n"

def t_EOL(t):
    r'\n|\r'
    return t

def t_error(t):
    raise CseParseError

if Debug == 1:
    lex = lex.lex(optimize=0, debug=0, errorlog = logger)
else:
    lex = lex.lex(optimize=0, debug=0, errorlog = lex.NullLogger())

if __name__ == '__main__':

    s = input('GCode > ')
    lex.input(s)
    while True:
        tok = lex.token()
        if not tok: break
        print (tok)
