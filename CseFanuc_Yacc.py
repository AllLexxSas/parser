#
# History
#
# Date          Name                Description of Change
# 10-Jul-2013   Kevin Chen          Creation
# 30-Nov-2013   Jason Fu            Add support for PRM[#i], PRM[#i, #j], PRM[#i]/[#k] & PRM[#i, #j]/[#k]
#                                   Add support for metacode "AX" & "AXNUM"
# 02-Jan-2014   Jason Fu            Fixed some mistakes in gValue, mValue, endStmt and extoutStmt
# 07-Feb-2014   Volker Grabowski    Reset error and g_bCallMacro for each parse call
#                                   Add missing NCExpressionFactory qualifier to AND_OP/OR_OP/XOR_OP
# 13-Apr-2016   Volker Grabowski    PR7539285: Handle different ROUND semantics
# 30-May-2016   Volker Grabowski    PR7726292: Suppress generation of PLY parsetab files
# 03-Jun-2016   Shuai Gao           ER8305694 and ER7724232:
#                                   Enhance rules for "IF THEN" and add rules for "ELSE" and "ENDIF".
# 01-Aug-2016   Shuai Gao           Fix rules for different ROUND.
# 09-Aug-2016   Volker Grabowski    Use custom exception class to handle parse errors
# 02-Sep-2016   Volker Grabowski    PR7796423: Handle non-LValues in assignment rule
# 06-Oct-2016   Volker Grabowski    PR7850582: Implement p_error for proper error handling
# 25-Oct-2016   Shuai Gao           PR7857807: Enhance rules for mValue.
#                                   Now a variable with a MINUS for address M (for example "M-#10") is supported.
# 08-May-2017   Volker Grabowski    Use must-be-implemented flag in CreateDynamicMetacodeCall
# 28-Aug-2017   Volker Grabowski    PR8958689: Support dynamic variable methods
# 11-Sep-2017   Volker Grabowski    Use variable method names that can be Python function names

import sys
import os
import ply.yacc as yacc
import ply.lex as lex
import CseFanuc_Lex

if CseFanuc_Lex.runInConsole == 0:
    from CSEWrapper import NCBasicType
    from CSEWrapper import NCExpressionFactory
    from CSEWrapper import CallFactory
    from CSEWrapper import NCLValue
    from CSEWrapper import CseParseError

class ExprCore():

    # Get the token map
    tokens = CseFanuc_Lex.tokens
    # Parsing rules

    precedence = (
                   ('left', 'AND','OR','XOR'),
                   ('left', 'PLUS','MINUS'),
                   ('left', 'TIMES','DIVIDE'),
                   ('right','UMINUS'),
    )

    def __init__(self, debug = 0, callF = None, exprSys = None):
        self.debug = debug
        self.names = { }
        modname = self.__class__.__name__
        self.debugfile = modname + ".dbg"
        self.tabmodule = modname + "_" + "parsetab"

        if CseFanuc_Lex.Debug == 1:
            self.parser = yacc.yacc(module=self, debug=self.debug, debugfile=self.debugfile, optimize=0, write_tables=0, tabmodule=self.tabmodule, errorlog = CseFanuc_Lex.logger)
        else:
            self.parser = yacc.yacc(module=self, debug=self.debug, debugfile=self.debugfile, optimize=0, write_tables=0, tabmodule=self.tabmodule, errorlog = yacc.NullLogger())

        self.szEndIfThenLabel = "FANUC_ENDIFTHEN_LABEL" 
        self.szIfThenLabel = "FANUC_IF_LABEL" 
        self.szElseLabel = "FANUC_ELSE_LABEL" 
        self.szEndIfLabel = "FANUC_ENDIF_LABEL" 
        self.szWrongIfLabel = "FANUC_WRONGIF_LABEL"

        if CseFanuc_Lex.runInConsole == 0:
            if callF != None:
                self.callFactory = callF
                self.exprSystem = self.callFactory.GetExprSystem()
                self.valueFactory = self.exprSystem.GetValueFactory()
                self.exprFactory = self.exprSystem.GetExprFactory()
                self.arrayexprFactory = self.exprSystem.GetArrayExprFactory()
                self.VarManager = self.exprSystem.GetVarManager()
            if exprSys != None:
                self.exprSystem = exprSys
                self.valueFactory = self.exprSystem.GetValueFactory()
                self.exprFactory = self.exprSystem.GetExprFactory()
                self.arrayexprFactory = self.exprSystem.GetArrayExprFactory()
                self.VarManager = self.exprSystem.GetVarManager()

    def SetCallFactory(self, callF):
        self.callFactory = callF
        self.exprSystem = self.callFactory.GetExprSystem()
        self.valueFactory = self.exprSystem.GetValueFactory()
        self.exprFactory = self.exprSystem.GetExprFactory()
        self.arrayexprFactory = self.exprSystem.GetArrayExprFactory()
        self.VarManager = self.exprSystem.GetVarManager()

    def SetExprSystem(self, exprSys):
        self.exprSystem = exprSys
        self.valueFactory = self.exprSystem.GetValueFactory()
        self.exprFactory = self.exprSystem.GetExprFactory()
        self.arrayexprFactory = self.exprSystem.GetArrayExprFactory()
        self.VarManager = self.exprSystem.GetVarManager()

    def p_variable_1(self, p):
        '''variable : '#' INTEGER_VALUE'''
        if p[2] == 0:
            p[0] = None
        else:
            strMethodName = 'VAR_' + str(p[2])
            if self.exprSystem.HasMethod(strMethodName):
                p[0] = self.exprFactory.CreateMethodExpr(strMethodName)
            else:
                p[0] = self.exprFactory.CreateVariableExpr('#' + str(p[2]))

    def p_variable_2(self, p):
        '''variable : '#' '[' expression ']' '''
        pArgExpr = self.CreateArithmeticExpr(p[3])
        pVarIndexExpr = self.exprFactory.CreateCastExpr(pArgExpr, NCBasicType.INTEGER)
        p[0] = self.exprFactory.CreateMethodExpr("GetDynamicVariable", [pVarIndexExpr])

    def p_variable_3(self, p):
        '''variable : '[' VARNAME ']' '''
        index = self.exprSystem.GetChannelState().GetControllerState().GetVariableNumber(p[2])
        if index == -1:
            self.error = ""
            raise CseParseError

        strVarName = '#'+str(index)
        if self.exprSystem.HasMethod(strVarName):
            p[0] = self.exprFactory.CreateMethodExpr(strVarName)
        else:
            p[0] = self.exprFactory.CreateVariableExpr(strVarName)

    def p_variable_4(self, p):
        '''variable : '[' VARNAME '[' expression ']' ']' '''
        index = self.exprSystem.GetChannelState().GetControllerState().GetVariableNumber(p[2])
        if index == -1:
            self.error = ""
            raise CseParseError

        pIntIndexExpr = self.exprFactory.CreateUnaryArithmeticExpr(p[4], NCExpressionFactory.ROUND_OP)
        pIntIndexExpr = self.exprFactory.CreateCastExpr(pIntIndexExpr, NCBasicType.INTEGER)
        pIntBaseExpr = self.CreateLiteralExprFromInteger(index)
        pVarIndexExpr = self.exprFactory.CreateBinaryArithmeticExpr(pIntBaseExpr, pIntIndexExpr, NCExpressionFactory.ADD_OP)
        p[0] = self.exprFactory.CreateMethodExpr("GetDynamicVariable", [pVarIndexExpr])

    def p_variable_5(self, p):
        '''variable : PRMVAR '[' expression ']' '''
        if self.VarManager.DoesArrayVariableExist('PRM'):
            pArray = self.arrayexprFactory.CreateVariableExpr('PRM')
            pList = [p[3]]
            p[0] = self.exprFactory.CreateArrayAccessExpr(pArray, pList)
        else:
            self.error = ""
            raise CseParseError
            
    def p_variable_6(self, p):
        '''variable : PRMVAR '[' expression ']' DIVIDE '[' expression ']' '''
        if self.VarManager.DoesArrayVariableExist('PRM2'):
            pArray = self.arrayexprFactory.CreateVariableExpr('PRM2')
            pList = [p[3],p[7]]
            p[0] = self.exprFactory.CreateArrayAccessExpr(pArray, pList)
        else:
            self.error = ""
            raise CseParseError
            
    def p_expression_1(self, p):
        '''expression : FLOAT_VALUE'''
        p[0] = self.CreateLiteralExprFromDouble(p[1])

    def p_expression_2(self, p):
        '''expression : INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_expression_3(self, p):
        '''expression : '[' expression ']' '''
        p[0] = p[2]

    def p_expression_4(self, p):
        '''expression : variable'''
        p[0] = self.CreateVarExpr(p[1])

    def p_expression_5(self, p):
        '''expression : FUNC '[' expression ']' '''
        pArgExpr = self.CreateArithmeticExpr(p[3])

        nUnaryOp = NCExpressionFactory.ROUND_OP
        bIgnore = False

        if p[1] == "ROUND":
            nUnaryOp = NCExpressionFactory.ROUND_OP
        elif p[1] == "SQRT":
            nUnaryOp = NCExpressionFactory.SQRT_OP
        elif p[1] == "ABS":
            nUnaryOp = NCExpressionFactory.ABS_OP
        elif p[1] == "ACOS":
            nUnaryOp = NCExpressionFactory.ACOS_OP
        elif p[1] == "ASIN":
            nUnaryOp = NCExpressionFactory.ASIN_OP
        elif p[1] == "BCD":
            bIgnore = True
        elif p[1] == "BIN":
            bIgnore = True
        elif p[1] == "COS":
            nUnaryOp = NCExpressionFactory.COS_OP
        elif p[1] == "FIX":
            nUnaryOp = NCExpressionFactory.ROUND_DOWN_OP
        elif p[1] == "FUP":
            nUnaryOp = NCExpressionFactory.ROUND_UP_OP
        elif p[1] == "SIN":
            nUnaryOp = NCExpressionFactory.SIN_OP
        elif p[1] == "TAN":
            nUnaryOp = NCExpressionFactory.TAN_OP

        if bIgnore:
            p[0] = pArgExpr
        else:
            p[0] = self.exprFactory.CreateUnaryArithmeticExpr(pArgExpr, nUnaryOp)

    def p_expression_6(self, p):
        '''expression : ATAN '[' expression ']' DIVIDE '[' expression ']' '''
        pExpr1 = self.CreateArithmeticExpr(p[3])
        pExpr2 = self.CreateArithmeticExpr(p[7])
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(pExpr1, pExpr2, NCExpressionFactory.ATAN2_OP)

    def p_expression_7(self, p):
        '''expression : expression PLUS expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.ADD_OP)

    def p_expression_8(self, p):
        '''expression : expression MINUS expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.SUB_OP)

    def p_expression_9(self, p):
        '''expression : expression TIMES expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.MULT_OP)

    def p_expression_10(self, p):
        '''expression : expression DIVIDE expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.DIV_OP)

    def p_expression_11(self, p):
        '''expression : expression MOD expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.MOD_OP)

    def p_expression_12(self, p):
        '''expression : expression AND expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.AND_OP)

    def p_expression_13(self, p):
        '''expression : expression OR expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.OR_OP)

    def p_expression_14(self, p):
        '''expression : expression XOR expression'''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateArithmeticExpr(p[1]), self.CreateArithmeticExpr(p[3]), NCExpressionFactory.XOR_OP)

    def p_expression_15(self, p):
        '''expression : MINUS expression %prec UMINUS'''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(p[2], NCExpressionFactory.NEG_OP)

    def p_expression_16(self, p):
        '''expression : PRMVAR '[' expression ',' expression ']' '''
        if self.VarManager.DoesArrayVariableExist('PRM'):
            pArray = self.arrayexprFactory.CreateVariableExpr('PRM')
            pList = [p[3]]
            pVariable = self.exprFactory.CreateArrayAccessExpr(pArray, pList)
            pExprArray = [pVariable,p[5]]
            p[0] = self.exprFactory.CreateMethodExpr("GetBitValue", pExprArray)
        else:
            self.error = ""
            raise CseParseError
            
    def p_expression_17(self, p):
        '''expression : PRMVAR '[' expression ',' expression ']' DIVIDE '[' expression ']' '''
        if self.VarManager.DoesArrayVariableExist('PRM2'):
            pArray = self.arrayexprFactory.CreateVariableExpr('PRM2')
            pList = [p[3],p[9]]
            pVariable = self.exprFactory.CreateArrayAccessExpr(pArray, pList)
            pExprArray = [pVariable,p[5]]
            p[0] = self.exprFactory.CreateMethodExpr("GetBitValue", pExprArray)
        else:
            self.error = ""
            raise CseParseError

    def p_expression_18(self, p):
        '''expression : AXNUM '[' AXISADDRESS ']' '''
        pAxisNameExpr = self.CreateLiteralExprFromString(p[3])
        pExprArray = [pAxisNameExpr]
        p[0] = self.exprFactory.CreateMethodExpr("GetJointNumber", pExprArray)
        
    def p_expression_19(self, p):
        '''expression : AXNUM '[' AXISADDRESS INTEGER_VALUE ']' '''
        pAxisNameExpr = self.CreateLiteralExprFromString(p[3]+str(p[4]))
        pExprArray = [pAxisNameExpr]
        p[0] = self.exprFactory.CreateMethodExpr("GetJointNumber", pExprArray)

    def p_error(self, p):
        self.error = ""

    def CreateLiteralExprFromInteger(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateIntegerValue(p))

    def CreateLiteralExprFromBool(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateBoolValue(p))

    def CreateLiteralExprFromString(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateStringValue(p))

    def CreateLiteralExprFromDouble(self, p):
        return self.exprFactory.CreateLiteral(self.valueFactory.CreateDoubleValue(p))

    def CreateArithmeticExpr(self, expr):
        pDefaultExpr = self.CreateLiteralExprFromDouble(0.0)
        pIsDefinedExpr = self.exprFactory.CreateUnaryArithmeticExpr(expr, NCExpressionFactory.DEFINED_OP)
        pResultExpr = self.exprFactory.CreateConditionalExpr(pIsDefinedExpr, expr, pDefaultExpr)
        return pResultExpr

    def CreateVarExpr(self, expr):
        if expr != None:
            return expr
        return self.exprFactory.CreateVariableExpr("#0")


class Parser(ExprCore):

    start = 'line'

    def p_line_1(self, p):
        '''line : lineContent'''

    def p_line_2(self, p):
        '''line : lineContent EOL'''

    def p_optionalComment_1(self, p):
        '''optionalComment : '''

    def p_optionalComment_2(self, p):
        '''optionalComment : COMMENT optionalComment'''

    def p_lineContent_1(self, p):
        '''lineContent : progName optionalComment'''

    def p_lineContent_2(self, p):
        '''lineContent : linePrefix numberedLine'''

    def p_progName_1(self, p):
        '''progName : PROGNUMBER'''
        self.callFactory.CreateLabelCall('O'+str(p[1]))
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromInteger(p[1])
        self.callFactory.CreateMetacodeCall("O", dictArgsNC)

    def p_progName_2(self, p):
        '''progName : FILENAME'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
        self.callFactory.CreateMetacodeCall("FileName", dictArgsNC)

    def p_linePrefix_1(self, p):
        '''linePrefix : lineSuppressList'''

    def p_linePrefix_2(self, p):
        '''linePrefix : lineSuppressList lineNumber lineSuppressList'''

    def p_lineSuppressList_1(self, p):
        '''lineSuppressList : '''

    def p_lineSuppressList_2(self, p):
        '''lineSuppressList : lineSuppressList lineSuppress'''


    def p_lineSuppress_1(self, p):
        '''lineSuppress : DIVIDE'''
        self.callFactory.CreateBreakCall(-1)

    def p_lineSuppress_2(self, p):
        '''lineSuppress : DIVIDE INTEGER_VALUE'''
        self.callFactory.CreateBreakCall(p[2])

    def p_lineNumber_1(self, p):
        '''lineNumber : lineNumberPrefix INTEGER_VALUE'''
        self.callFactory.CreateLabelCall('N'+str(p[2]))
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromInteger(p[2])
        self.callFactory.CreateMetacodeCall("N", dictArgsNC)

    def p_lineNumberPrefix_1(self, p):
        '''lineNumberPrefix : 'N' '''

    def p_lineNumberPrefix_2(self, p):
        '''lineNumberPrefix : ':' '''

    def p_numberedLine_1(self, p):
        '''numberedLine : '''

    def p_numberedLine_2(self, p):
        '''numberedLine : address numberedLine'''

    def p_numberedLine_3(self, p):
        '''numberedLine : assignment numberedLine'''

    def p_numberedLine_4(self, p):
        '''numberedLine : COMMENT numberedLine'''

    def p_numberedLine_5(self, p):
        '''numberedLine : gotoStmt optionalComment'''

    def p_numberedLine_6(self, p):
        '''numberedLine : ifGotoStmt optionalComment'''

    def p_numberedLine_7(self, p):
        '''numberedLine : ifThenStmt optionalComment'''

    def p_numberedLine_8(self, p):
        '''numberedLine : elseStmt optionalComment'''

    def p_numberedLine_9(self, p):
        '''numberedLine : endIfStmt optionalComment'''

    def p_numberedLine_10(self, p):
        '''numberedLine : whileDoStmt optionalComment'''

    def p_numberedLine_11(self, p):
        '''numberedLine : endStmt optionalComment'''

    def p_numberedLine_12(self, p):
        '''numberedLine : extoutStmt optionalComment'''

    def p_numberedLine_13(self, p):
        '''numberedLine : setvnStmt optionalComment'''

    def p_address_1(self, p):
        '''address : INTADDRESS intValue'''

        dictArgsNC = {}
        dictArgsNC["Value"] = p[2]
        self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

    def p_address_2(self, p):
        '''address : FLOATADDRESS intfloatValue'''

        dictArgsNC = {}
        dictArgsNC["Value"] = p[2]
        self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

    def p_address_3(self, p):
        '''address : PARAMETERADDRESS intfloatValue'''

        dictArgsNC = {}
        dictArgsNC["Value"] = p[2]
        self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

    def p_address_4(self, p):
        '''address : AXISADDRESS intfloatValue'''

        dictArgsNC = {}
        dictArgsNC["Value"] = p[2]
        self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

    def p_address_5(self, p):
        '''address : AXISADDRESS '=' intfloatValue'''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        self.callFactory.CreateMetacodeCall(p[1], dictArgsNC)

    def p_address_6(self, p):
        '''address : AXISADDRESS INTEGER_VALUE '=' intfloatValue'''
        dictArgsNC = {}
        dictArgsNC["Value"] = p[4]
        self.callFactory.CreateMetacodeCall(p[1]+str(p[2]), dictArgsNC)

    def p_address_7(self, p):
        '''address : ',' AXISADDRESS intfloatValue'''
        pszName = ''
        if p[2] == 'A':
            pszName = 'Angle'
        elif  p[2] == 'C':
            pszName = 'Chamfer'
        else:
            self.error = ""
            raise CseParseError

        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        self.callFactory.CreateMetacodeCall(pszName, dictArgsNC)

    def p_address_8(self, p):
        '''address : ',' FLOATADDRESS intfloatValue'''
        pszName = ''
        if p[2] == 'R':
            pszName = 'Radius'
        else:
            self.error = ""
            raise CseParseError

        dictArgsNC = {}
        dictArgsNC["Value"] = p[3]
        self.callFactory.CreateMetacodeCall(pszName, dictArgsNC)

    def p_address_9(self, p):
        '''address : GON'''
        self.callFactory.CreateMetacodeCall("GON")

    def p_address_10(self, p):
        '''address : GOF'''
        self.callFactory.CreateMetacodeCall("GOF")

    def p_address_11(self, p):
        '''address : 'G' gValue'''

    def p_address_12(self, p):
        '''address : 'M' mValue'''
        
    def p_address_13(self, p):
        '''address : AXISNUMADDRESS '[' INTEGER_VALUE ']' intfloatValue'''
        pAxisNumExpr = self.CreateLiteralExprFromInteger(p[3])
        pExprArray = [pAxisNumExpr]
        dictArgsNC = {}
        dictArgsNC["Value"] = p[5]
        pAXISNAME = self.exprFactory.CreateMethodExpr("GetJointName", pExprArray)
        self.callFactory.CreateDynamicMetacodeCall(pAXISNAME, dictArgsNC)

    def p_address_14(self, p):
        '''address : AXISNUMADDRESS '[' INTEGER_VALUE ']' '=' intfloatValue'''
        pAxisNumExpr = self.CreateLiteralExprFromInteger(p[3])
        pExprArray = [pAxisNumExpr]
        dictArgsNC = {}
        dictArgsNC["Value"] = p[6]
        pAXISNAME = self.exprFactory.CreateMethodExpr("GetJointName", pExprArray)
        self.callFactory.CreateDynamicMetacodeCall(pAXISNAME, dictArgsNC)

    def p_assignment_1(self, p):
        '''assignment : variable '=' expression'''
        if p[1] == None or not isinstance(p[1], NCLValue):
            self.error = ""
            raise CseParseError

        self.callFactory.CreateAssignCall(p[1], p[3])

    def p_intValue_1(self, p):
        '''intValue : INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_intValue_2(self, p):
        '''intValue : MINUS INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(-p[2])

    def p_intValue_3(self, p):
        '''intValue : variable'''
        p[0] = self.CreateVarExpr(p[1])

    def p_intValue_4(self, p):
        '''intValue : MINUS variable'''
        pArgExpr = self.CreateArithmeticExpr(self.CreateVarExpr(p[2]))
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(pArgExpr, NCExpressionFactory.NEG_OP)

    def p_intValue_5(self, p):
        '''intValue : '[' expression ']' '''
        p[0] = p[2]

    def p_intValue_6(self, p):
        '''intValue : MINUS '[' expression ']' '''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(self.CreateArithmeticExpr(p[3]), NCExpressionFactory.NEG_OP)

    def p_intfloatValue_1(self, p):
        '''intfloatValue : INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(p[1])

    def p_intfloatValue_2(self, p):
        '''intfloatValue : MINUS INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(-p[2])

    def p_intfloatValue_3(self, p):
        '''intfloatValue : PLUS INTEGER_VALUE'''
        p[0] = self.CreateLiteralExprFromInteger(p[2])

    def p_intfloatValue_4(self, p):
        '''intfloatValue : FLOAT_VALUE'''
        p[0] = self.CreateLiteralExprFromDouble(p[1])

    def p_intfloatValue_5(self, p):
        '''intfloatValue : MINUS FLOAT_VALUE'''
        p[0] = self.CreateLiteralExprFromDouble(-p[2])

    def p_intfloatValue_6(self, p):
        '''intfloatValue : PLUS FLOAT_VALUE'''
        p[0] = self.CreateLiteralExprFromDouble(p[2])

    def p_intfloatValue_7(self, p):
        '''intfloatValue : variable'''
        p[0] = self.CreateVarExpr(p[1])

    def p_intfloatValue_8(self, p):
        '''intfloatValue : PLUS variable'''
        p[0] = self.CreateVarExpr(p[2])

    def p_intfloatValue_9(self, p):
        '''intfloatValue : MINUS variable'''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(self.CreateArithmeticExpr(self.CreateVarExpr(p[2])), NCExpressionFactory.NEG_OP)

    def p_intfloatValue_10(self, p):
        '''intfloatValue : '[' expression ']' '''
        p[0] = p[2]

    def p_intfloatValue_11(self, p):
        '''intfloatValue : PLUS '[' expression ']' '''
        p[0] = p[3]

    def p_intfloatValue_12(self, p):
        '''intfloatValue : MINUS '[' expression ']' '''
        p[0] = self.exprFactory.CreateUnaryArithmeticExpr(self.CreateArithmeticExpr(p[3]), NCExpressionFactory.NEG_OP)

    def p_gValue_1(self, p):
        '''gValue : INTEGER_VALUE'''
        if p[1] == 65 or p[1] == 66:
            self.g_bCallMacro = True

        self.callFactory.CreateMetacodeCall('G'+str(p[1]))

    def p_gValue_2(self, p):
        '''gValue : INTEGER_VALUE FILENAME'''
        if p[1] != 65 and p[1] != 66:
            self.error = ""
            raise CseParseError

        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[2])
        self.callFactory.CreateMetacodeCall('G'+str(p[1]), dictArgsNC)

    def p_gValue_3(self, p):
        '''gValue : FLOAT_VALUE'''
        nMainG  = int(p[1])
        nSub = int(p[1]*10.0) - nMainG*10

        self.callFactory.CreateMetacodeCall('G'+str(nMainG)+'.'+str(nSub))

    def p_gValue_4(self, p):
        '''gValue : FLOAT_VALUE FILENAME'''
        nMainG  = int(p[1])
        nSubG = int(p[1]*10.0) - nMainG*10
        
        if (nMainG != 66 or nSubG != 1) and (nMainG != 72 or (nSubG != 1 and nSubG != 2)):
            self.error = ""
            raise CseParseError

        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[2])
        self.callFactory.CreateMetacodeCall('G'+str(nMainG)+'.'+str(nSubG), dictArgsNC)

    def p_gValue_5(self, p):
        '''gValue : variable'''
        pIntExpr = self.exprFactory.CreateCastExpr(self.CreateVarExpr(p[1]), NCBasicType.INTEGER)
        pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("G"), pIntExpr, NCExpressionFactory.ADD_OP)
        self.callFactory.CreateDynamicMetacodeCall(pMetaCodeExpr)

    def p_gValue_6(self, p):
        '''gValue : '[' expression ']' '''
        pIntExpr = self.exprFactory.CreateCastExpr(p[2], NCBasicType.INTEGER)
        pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("G"), pIntExpr, NCExpressionFactory.ADD_OP)
        self.callFactory.CreateDynamicMetacodeCall(pMetaCodeExpr)

    def p_mValue_1(self, p):
        '''mValue : INTEGER_VALUE'''
        if self.g_bCallMacro == True:
            dictArgsNC = {}
            dictArgsNC["Value"] = self.CreateLiteralExprFromInteger(p[1])
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)
        else:
            pIntExpr = self.CreateLiteralExprFromInteger(p[1])
            pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)
            if self.callFactory.IsMetacodeDefined(pMetaCodeExpr.GetValue().GetString()):
                self.callFactory.CreateMetacodeCall('M'+str(p[1]))

    def p_mValue_2(self, p):
        '''mValue : INTEGER_VALUE FILENAME'''
        if p[1] != 96 and p[1] != 98:
            self.error = ""
            raise CseParseError

        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[2])

        pIntExpr = self.CreateLiteralExprFromInteger(p[1])
        pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)
        if self.callFactory.IsMetacodeDefined(pMetaCodeExpr.GetValue().GetString()):
            self.callFactory.CreateMetacodeCall('M'+str(p[1]), dictArgsNC)

    def p_mValue_3(self, p):
        '''mValue : FLOAT_VALUE'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromDouble(p[1])

        pDoubleExpr = self.CreateLiteralExprFromDouble(p[1])
        pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pDoubleExpr, NCExpressionFactory.ADD_OP)
        if self.callFactory.IsMetacodeDefined(pMetaCodeExpr.GetValue().GetString()):
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)

    def p_mValue_4(self, p):
        '''mValue : MINUS FLOAT_VALUE'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromDouble(-p[2])

        pDoubleExpr = self.CreateLiteralExprFromDouble(-p[2])
        pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pDoubleExpr, NCExpressionFactory.ADD_OP)
        if self.callFactory.IsMetacodeDefined(pMetaCodeExpr.GetValue().GetString()):
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)

    def p_mValue_5(self, p):
        '''mValue : variable'''
        pVarExpr = self.CreateVarExpr(p[1])

        if self.g_bCallMacro == True:
            dictArgsNC = {}
            dictArgsNC["Value"] = pVarExpr
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)
        else:
            pIntExpr = self.exprFactory.CreateCastExpr(pVarExpr, NCBasicType.INTEGER)
            pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)
            self.callFactory.CreateDynamicMetacodeCall(pMetaCodeExpr, {}, [], False)

    def p_mValue_6(self, p):
        '''mValue : MINUS variable'''
        pArgExpr = self.CreateArithmeticExpr(self.CreateVarExpr(p[2]))
        pVarExpr = self.exprFactory.CreateUnaryArithmeticExpr(pArgExpr, NCExpressionFactory.NEG_OP)

        if self.g_bCallMacro == True:
            dictArgsNC = {}
            dictArgsNC["Value"] = pVarExpr
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)
        else:
            pIntExpr = self.exprFactory.CreateCastExpr(pVarExpr, NCBasicType.INTEGER)
            pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)
            self.callFactory.CreateDynamicMetacodeCall(pMetaCodeExpr, {}, [], False)

    def p_mValue_7(self, p):
        '''mValue : '[' expression ']' '''
        if self.g_bCallMacro == True:
            dictArgsNC = {}
            dictArgsNC["Value"] = p[2]
            self.callFactory.CreateMetacodeCall('M', dictArgsNC)
        else:
            pIntExpr = self.exprFactory.CreateCastExpr(p[2], NCBasicType.INTEGER)
            pMetaCodeExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("M"), pIntExpr, NCExpressionFactory.ADD_OP)
            self.callFactory.CreateDynamicMetacodeCall(pMetaCodeExpr, {}, [], False)

    def p_gotoStmt_1(self, p):
        '''gotoStmt : GOTO intValue'''
        pIntExpr = self.exprFactory.CreateCastExpr(p[2], NCBasicType.INTEGER)
        pTargetExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("N"), pIntExpr, NCExpressionFactory.ADD_OP)
        self.callFactory.CreateGotoCall(pTargetExpr, CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p_ifGotoStmt_1(self, p):
        '''ifGotoStmt : IF '[' boolExpr ']' GOTO intValue'''
        pTargetExpr = self.exprFactory.CreateBinaryArithmeticExpr(self.CreateLiteralExprFromString("N"), p[6], NCExpressionFactory.ADD_OP)
        self.callFactory.CreateIfCall(p[3], pTargetExpr, CallFactory.SEARCH_FORWARD_THEN_BACKWARD)

    def p_ifThenStmt_1(self, p):
        '''ifThenStmt : IF '[' boolExpr ']' THEN _embed0_ifThenStmt assignment'''
        self.callFactory.CreateLabelCall(self.szEndIfThenLabel)

    def p__embed0_ifThenStmt(self, p):
        '''_embed0_ifThenStmt : '''
        pNegCondition = self.exprFactory.CreateUnaryArithmeticExpr(p[-3], NCExpressionFactory.NEG_OP)
        self.callFactory.CreateIfCall(pNegCondition, self.CreateLiteralExprFromString(self.szEndIfThenLabel), CallFactory.SEARCH_FORWARD)

    def p_ifThenStmt_2(self, p):
        '''ifThenStmt : IF '[' boolExpr ']' THEN'''
        self.callFactory.CreateLabelCall(self.szIfThenLabel)
        pNegCondition = self.exprFactory.CreateUnaryArithmeticExpr(p[3], NCExpressionFactory.NEG_OP)
        self.callFactory.CreateNestedIfCall(pNegCondition, self.CreateLiteralExprFromString(self.szWrongIfLabel), CallFactory.SEARCH_FORWARD, self.szIfThenLabel, self.szEndIfLabel)

    def p_elseStmt_2(self, p):
        '''elseStmt : ELSE'''
        self.callFactory.CreateNestedGotoCall(self.CreateLiteralExprFromString(self.szEndIfLabel), CallFactory.SEARCH_FORWARD, self.szIfThenLabel, self.szEndIfLabel, 1)
        self.callFactory.CreateLabelCall(self.szWrongIfLabel)

    def p_endIfStmt_1(self, p):
        '''endIfStmt : ENDIF'''
        self.callFactory.CreateLabelCall(self.szWrongIfLabel)
        self.callFactory.CreateLabelCall(self.szEndIfLabel)

    def p_whileDoStmt_1(self, p):
        '''whileDoStmt : WHILE '[' boolExpr ']' DO endLabel'''
        strStartLabel = "WHILE"+str(p[6])
        strEndLabel = "END"+str(p[6])
        self.callFactory.CreateLabelCall(strStartLabel)
        pBoolExpr = self.exprFactory.CreateUnaryArithmeticExpr(p[3], NCExpressionFactory.NEG_OP)
        self.callFactory.CreateNestedIfCall(pBoolExpr, self.CreateLiteralExprFromString(strEndLabel), CallFactory.SEARCH_FORWARD, strStartLabel, strEndLabel)

    def p_endStmt_1(self, p):
        '''endStmt : END endLabel'''
        strStartLabel = "WHILE"+str(p[2])
        strEndLabel = "END"+str(p[2])
        self.callFactory.CreateNestedGotoCall(self.CreateLiteralExprFromString(strStartLabel), CallFactory.SEARCH_BACKWARD, strStartLabel, strEndLabel, 1)
        self.callFactory.CreateLabelCall(strEndLabel)

    def p_setvnStmt_1(self, p):
        '''setvnStmt : SETVN INTEGER_VALUE _embed0_setvnStmt '[' '''

        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromInteger(p[2])

        listArgsNC = []
        for arg in CseFanuc_Lex.commVarNameList:
            listArgsNC.append(self.CreateLiteralExprFromString(arg))

        self.callFactory.CreateMetacodeCall('SETVN', dictArgsNC, listArgsNC)

    def p_embed0_setvnStmt(self, p):
        '''_embed0_setvnStmt : '''
        CseFanuc_Lex.start_commVarName(p.lexer)

    def p_endLabel_1(self, p):
        '''endLabel : INTEGER_VALUE'''
        if p[1]<1 or p[1]>3:
            self.error = ""
            raise CseParseError

        p[0] = 1

    def p_boolExpr_1(self, p):
        '''boolExpr : expression BOOLOP expression'''
        if p[2] == 'EQ' or p[2] == 'NE':
            pDef1Expr = self.exprFactory.CreateUnaryArithmeticExpr(p[1], NCExpressionFactory.DEFINED_OP)
            pDef2Expr = self.exprFactory.CreateUnaryArithmeticExpr(p[3], NCExpressionFactory.DEFINED_OP)

            if p[2] == 'EQ':
                boolOP = NCExpressionFactory.EQ_OP
            else:
                boolOP = NCExpressionFactory.NE_OP

            pBoolOpExpr = self.exprFactory.CreateBinaryArithmeticExpr(p[1], p[3], boolOP)
            pCondition = self.exprFactory.CreateBinaryArithmeticExpr(pDef1Expr, pDef2Expr, NCExpressionFactory.AND_OP)
            pDefBoolOpExpr = self.exprFactory.CreateBinaryArithmeticExpr(pDef1Expr, pDef2Expr, boolOP)
            p[0] = self.exprFactory.CreateConditionalExpr(pCondition, pBoolOpExpr, pDefBoolOpExpr)
        else:
            pExpr1 = self.CreateArithmeticExpr(p[1])
            pExpr2 = self.CreateArithmeticExpr(p[3])
            nBinaryOp = NCExpressionFactory.GE_OP
            if p[2] == 'GE':
                nBinaryOp = NCExpressionFactory.GE_OP
            elif p[2] == 'GT':
                nBinaryOp = NCExpressionFactory.GT_OP
            elif p[2] == 'LE':
                nBinaryOp = NCExpressionFactory.LE_OP
            elif p[2] == 'LT':
                nBinaryOp = NCExpressionFactory.LT_OP
            
            p[0] = self.exprFactory.CreateBinaryArithmeticExpr(pExpr1, pExpr2, nBinaryOp)

    def p_boolExpr_2(self, p):
        '''boolExpr : '[' boolExpr ']' AND '[' boolExpr ']' '''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[2], p[6], NCExpressionFactory.AND_OP)

    def p_boolExpr_3(self, p):
        '''boolExpr : '[' boolExpr ']' OR '[' boolExpr ']' '''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[2], p[6], NCExpressionFactory.OR_OP)

    def p_boolExpr_4(self, p):
        '''boolExpr : '[' boolExpr ']' XOR '[' boolExpr ']' '''
        p[0] = self.exprFactory.CreateBinaryArithmeticExpr(p[2], p[6], NCExpressionFactory.XOR_OP)

    def p_extoutStmt_1(self, p):
        '''extoutStmt : POPEN'''
        self.callFactory.CreateMetacodeCall("POPEN")

    def p_extoutStmt_2(self, p):
        '''extoutStmt : BPRNT'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
        self.callFactory.CreateMetacodeCall('BPRNT', dictArgsNC)

    def p_extoutStmt_3(self, p):
        '''extoutStmt : DPRNT'''
        dictArgsNC = {}
        dictArgsNC["Value"] = self.CreateLiteralExprFromString(p[1])
        self.callFactory.CreateMetacodeCall('DPRNT', dictArgsNC)

    def p_extoutStmt_4(self, p):
        '''extoutStmt : PCLOS'''
        self.callFactory.CreateMetacodeCall("PCLOS")

    def parse(self, s):
        self.error = None
        self.g_bCallMacro = False
        self.parser.parse(s, tokenfunc=get_token)
        if self.error != None:
            return False
        
        return True

last_token = None

def get_token():
    global last_token
    last_token = CseFanuc_Lex.lex.token()
    return last_token

class ParserExpr(ExprCore):

    g_pExpr = None
    
    start = 'startExpr'

    def p_startExpr(self, p):
        'startExpr : expression'
        ParserExpr.g_pExpr = p[1]

    def parse(self, s):
        self.error = None
        self.g_bCallMacro = False
        self.parser.parse(s)
        if self.error != None:
            return None
        
        return ParserExpr.g_pExpr

if __name__ == '__main__':

    parser = Parser();
    while 1:
        try:
            s = input('GCode > ')
        except EOFError:
            break
        if not s: continue
        parser.error = None
        parser.parse(s)
        if parser.error != None:
            print("LOGIC ERROR")
