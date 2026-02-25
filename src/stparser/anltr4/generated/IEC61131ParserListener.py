# Generated from IEC61131Parser.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .IEC61131Parser import IEC61131Parser
else:
    from IEC61131Parser import IEC61131Parser

# This class defines a complete listener for a parse tree produced by IEC61131Parser.
class IEC61131ParserListener(ParseTreeListener):

    # Enter a parse tree produced by IEC61131Parser#start.
    def enterStart(self, ctx:IEC61131Parser.StartContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#start.
    def exitStart(self, ctx:IEC61131Parser.StartContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#namespace_declaration.
    def enterNamespace_declaration(self, ctx:IEC61131Parser.Namespace_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#namespace_declaration.
    def exitNamespace_declaration(self, ctx:IEC61131Parser.Namespace_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#namespace_elements.
    def enterNamespace_elements(self, ctx:IEC61131Parser.Namespace_elementsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#namespace_elements.
    def exitNamespace_elements(self, ctx:IEC61131Parser.Namespace_elementsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#full_qualified_identifier.
    def enterFull_qualified_identifier(self, ctx:IEC61131Parser.Full_qualified_identifierContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#full_qualified_identifier.
    def exitFull_qualified_identifier(self, ctx:IEC61131Parser.Full_qualified_identifierContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#using_directive.
    def enterUsing_directive(self, ctx:IEC61131Parser.Using_directiveContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#using_directive.
    def exitUsing_directive(self, ctx:IEC61131Parser.Using_directiveContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#library_element_declaration.
    def enterLibrary_element_declaration(self, ctx:IEC61131Parser.Library_element_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#library_element_declaration.
    def exitLibrary_element_declaration(self, ctx:IEC61131Parser.Library_element_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#constant.
    def enterConstant(self, ctx:IEC61131Parser.ConstantContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#constant.
    def exitConstant(self, ctx:IEC61131Parser.ConstantContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#cast.
    def enterCast(self, ctx:IEC61131Parser.CastContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#cast.
    def exitCast(self, ctx:IEC61131Parser.CastContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#integer.
    def enterInteger(self, ctx:IEC61131Parser.IntegerContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#integer.
    def exitInteger(self, ctx:IEC61131Parser.IntegerContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#bits.
    def enterBits(self, ctx:IEC61131Parser.BitsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#bits.
    def exitBits(self, ctx:IEC61131Parser.BitsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#real.
    def enterReal(self, ctx:IEC61131Parser.RealContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#real.
    def exitReal(self, ctx:IEC61131Parser.RealContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#string.
    def enterString(self, ctx:IEC61131Parser.StringContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#string.
    def exitString(self, ctx:IEC61131Parser.StringContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#time.
    def enterTime(self, ctx:IEC61131Parser.TimeContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#time.
    def exitTime(self, ctx:IEC61131Parser.TimeContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#timeofday.
    def enterTimeofday(self, ctx:IEC61131Parser.TimeofdayContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#timeofday.
    def exitTimeofday(self, ctx:IEC61131Parser.TimeofdayContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#date.
    def enterDate(self, ctx:IEC61131Parser.DateContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#date.
    def exitDate(self, ctx:IEC61131Parser.DateContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#datetime.
    def enterDatetime(self, ctx:IEC61131Parser.DatetimeContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#datetime.
    def exitDatetime(self, ctx:IEC61131Parser.DatetimeContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ref_null.
    def enterRef_null(self, ctx:IEC61131Parser.Ref_nullContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ref_null.
    def exitRef_null(self, ctx:IEC61131Parser.Ref_nullContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#data_type_name.
    def enterData_type_name(self, ctx:IEC61131Parser.Data_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#data_type_name.
    def exitData_type_name(self, ctx:IEC61131Parser.Data_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#non_generic_type_name.
    def enterNon_generic_type_name(self, ctx:IEC61131Parser.Non_generic_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#non_generic_type_name.
    def exitNon_generic_type_name(self, ctx:IEC61131Parser.Non_generic_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#elementary_type_name.
    def enterElementary_type_name(self, ctx:IEC61131Parser.Elementary_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#elementary_type_name.
    def exitElementary_type_name(self, ctx:IEC61131Parser.Elementary_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#numeric_type_name.
    def enterNumeric_type_name(self, ctx:IEC61131Parser.Numeric_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#numeric_type_name.
    def exitNumeric_type_name(self, ctx:IEC61131Parser.Numeric_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#integer_type_name.
    def enterInteger_type_name(self, ctx:IEC61131Parser.Integer_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#integer_type_name.
    def exitInteger_type_name(self, ctx:IEC61131Parser.Integer_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#signed_integer_type_name.
    def enterSigned_integer_type_name(self, ctx:IEC61131Parser.Signed_integer_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#signed_integer_type_name.
    def exitSigned_integer_type_name(self, ctx:IEC61131Parser.Signed_integer_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#unsigned_integer_type_name.
    def enterUnsigned_integer_type_name(self, ctx:IEC61131Parser.Unsigned_integer_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#unsigned_integer_type_name.
    def exitUnsigned_integer_type_name(self, ctx:IEC61131Parser.Unsigned_integer_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#real_type_name.
    def enterReal_type_name(self, ctx:IEC61131Parser.Real_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#real_type_name.
    def exitReal_type_name(self, ctx:IEC61131Parser.Real_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#date_type_name.
    def enterDate_type_name(self, ctx:IEC61131Parser.Date_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#date_type_name.
    def exitDate_type_name(self, ctx:IEC61131Parser.Date_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#bit_string_type_name.
    def enterBit_string_type_name(self, ctx:IEC61131Parser.Bit_string_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#bit_string_type_name.
    def exitBit_string_type_name(self, ctx:IEC61131Parser.Bit_string_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#generic_type_name.
    def enterGeneric_type_name(self, ctx:IEC61131Parser.Generic_type_nameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#generic_type_name.
    def exitGeneric_type_name(self, ctx:IEC61131Parser.Generic_type_nameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#data_type_declaration.
    def enterData_type_declaration(self, ctx:IEC61131Parser.Data_type_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#data_type_declaration.
    def exitData_type_declaration(self, ctx:IEC61131Parser.Data_type_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#type_declaration.
    def enterType_declaration(self, ctx:IEC61131Parser.Type_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#type_declaration.
    def exitType_declaration(self, ctx:IEC61131Parser.Type_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#initializations_constant.
    def enterInitializations_constant(self, ctx:IEC61131Parser.Initializations_constantContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#initializations_constant.
    def exitInitializations_constant(self, ctx:IEC61131Parser.Initializations_constantContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#initializations_identifier.
    def enterInitializations_identifier(self, ctx:IEC61131Parser.Initializations_identifierContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#initializations_identifier.
    def exitInitializations_identifier(self, ctx:IEC61131Parser.Initializations_identifierContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#initializations_array_initialization.
    def enterInitializations_array_initialization(self, ctx:IEC61131Parser.Initializations_array_initializationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#initializations_array_initialization.
    def exitInitializations_array_initialization(self, ctx:IEC61131Parser.Initializations_array_initializationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#initializations_structure_initialization.
    def enterInitializations_structure_initialization(self, ctx:IEC61131Parser.Initializations_structure_initializationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#initializations_structure_initialization.
    def exitInitializations_structure_initialization(self, ctx:IEC61131Parser.Initializations_structure_initializationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#subrange_spec_init.
    def enterSubrange_spec_init(self, ctx:IEC61131Parser.Subrange_spec_initContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#subrange_spec_init.
    def exitSubrange_spec_init(self, ctx:IEC61131Parser.Subrange_spec_initContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#subrange.
    def enterSubrange(self, ctx:IEC61131Parser.SubrangeContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#subrange.
    def exitSubrange(self, ctx:IEC61131Parser.SubrangeContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#enumerated_specification.
    def enterEnumerated_specification(self, ctx:IEC61131Parser.Enumerated_specificationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#enumerated_specification.
    def exitEnumerated_specification(self, ctx:IEC61131Parser.Enumerated_specificationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#array_specification.
    def enterArray_specification(self, ctx:IEC61131Parser.Array_specificationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#array_specification.
    def exitArray_specification(self, ctx:IEC61131Parser.Array_specificationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#array_initialization.
    def enterArray_initialization(self, ctx:IEC61131Parser.Array_initializationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#array_initialization.
    def exitArray_initialization(self, ctx:IEC61131Parser.Array_initializationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#array_initial_elements.
    def enterArray_initial_elements(self, ctx:IEC61131Parser.Array_initial_elementsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#array_initial_elements.
    def exitArray_initial_elements(self, ctx:IEC61131Parser.Array_initial_elementsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#array_initial_element.
    def enterArray_initial_element(self, ctx:IEC61131Parser.Array_initial_elementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#array_initial_element.
    def exitArray_initial_element(self, ctx:IEC61131Parser.Array_initial_elementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#structure_declaration.
    def enterStructure_declaration(self, ctx:IEC61131Parser.Structure_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#structure_declaration.
    def exitStructure_declaration(self, ctx:IEC61131Parser.Structure_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#name.
    def enterName(self, ctx:IEC61131Parser.NameContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#name.
    def exitName(self, ctx:IEC61131Parser.NameContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#structure_initialization.
    def enterStructure_initialization(self, ctx:IEC61131Parser.Structure_initializationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#structure_initialization.
    def exitStructure_initialization(self, ctx:IEC61131Parser.Structure_initializationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#string_type_declaration.
    def enterString_type_declaration(self, ctx:IEC61131Parser.String_type_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#string_type_declaration.
    def exitString_type_declaration(self, ctx:IEC61131Parser.String_type_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#reference_specification.
    def enterReference_specification(self, ctx:IEC61131Parser.Reference_specificationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#reference_specification.
    def exitReference_specification(self, ctx:IEC61131Parser.Reference_specificationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#reference_value.
    def enterReference_value(self, ctx:IEC61131Parser.Reference_valueContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#reference_value.
    def exitReference_value(self, ctx:IEC61131Parser.Reference_valueContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#identifier_list.
    def enterIdentifier_list(self, ctx:IEC61131Parser.Identifier_listContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#identifier_list.
    def exitIdentifier_list(self, ctx:IEC61131Parser.Identifier_listContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#function_declaration.
    def enterFunction_declaration(self, ctx:IEC61131Parser.Function_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#function_declaration.
    def exitFunction_declaration(self, ctx:IEC61131Parser.Function_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#var_decls.
    def enterVar_decls(self, ctx:IEC61131Parser.Var_declsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#var_decls.
    def exitVar_decls(self, ctx:IEC61131Parser.Var_declsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#var_decl.
    def enterVar_decl(self, ctx:IEC61131Parser.Var_declContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#var_decl.
    def exitVar_decl(self, ctx:IEC61131Parser.Var_declContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#var_decl_inner.
    def enterVar_decl_inner(self, ctx:IEC61131Parser.Var_decl_innerContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#var_decl_inner.
    def exitVar_decl_inner(self, ctx:IEC61131Parser.Var_decl_innerContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#variable_keyword.
    def enterVariable_keyword(self, ctx:IEC61131Parser.Variable_keywordContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#variable_keyword.
    def exitVariable_keyword(self, ctx:IEC61131Parser.Variable_keywordContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#access_specifier.
    def enterAccess_specifier(self, ctx:IEC61131Parser.Access_specifierContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#access_specifier.
    def exitAccess_specifier(self, ctx:IEC61131Parser.Access_specifierContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#function_block_declaration.
    def enterFunction_block_declaration(self, ctx:IEC61131Parser.Function_block_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#function_block_declaration.
    def exitFunction_block_declaration(self, ctx:IEC61131Parser.Function_block_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#body.
    def enterBody(self, ctx:IEC61131Parser.BodyContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#body.
    def exitBody(self, ctx:IEC61131Parser.BodyContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#funcBody.
    def enterFuncBody(self, ctx:IEC61131Parser.FuncBodyContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#funcBody.
    def exitFuncBody(self, ctx:IEC61131Parser.FuncBodyContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#interface_declaration.
    def enterInterface_declaration(self, ctx:IEC61131Parser.Interface_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#interface_declaration.
    def exitInterface_declaration(self, ctx:IEC61131Parser.Interface_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#class_declaration.
    def enterClass_declaration(self, ctx:IEC61131Parser.Class_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#class_declaration.
    def exitClass_declaration(self, ctx:IEC61131Parser.Class_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#methods.
    def enterMethods(self, ctx:IEC61131Parser.MethodsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#methods.
    def exitMethods(self, ctx:IEC61131Parser.MethodsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#method.
    def enterMethod(self, ctx:IEC61131Parser.MethodContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#method.
    def exitMethod(self, ctx:IEC61131Parser.MethodContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#program_declaration.
    def enterProgram_declaration(self, ctx:IEC61131Parser.Program_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#program_declaration.
    def exitProgram_declaration(self, ctx:IEC61131Parser.Program_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#global_variable_list_declaration.
    def enterGlobal_variable_list_declaration(self, ctx:IEC61131Parser.Global_variable_list_declarationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#global_variable_list_declaration.
    def exitGlobal_variable_list_declaration(self, ctx:IEC61131Parser.Global_variable_list_declarationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#stl_list.
    def enterStl_list(self, ctx:IEC61131Parser.Stl_listContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#stl_list.
    def exitStl_list(self, ctx:IEC61131Parser.Stl_listContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#stl_expression.
    def enterStl_expression(self, ctx:IEC61131Parser.Stl_expressionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#stl_expression.
    def exitStl_expression(self, ctx:IEC61131Parser.Stl_expressionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#stl_call.
    def enterStl_call(self, ctx:IEC61131Parser.Stl_callContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#stl_call.
    def exitStl_call(self, ctx:IEC61131Parser.Stl_callContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#unaryNegateExpr.
    def enterUnaryNegateExpr(self, ctx:IEC61131Parser.UnaryNegateExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#unaryNegateExpr.
    def exitUnaryNegateExpr(self, ctx:IEC61131Parser.UnaryNegateExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryOrExpr.
    def enterBinaryOrExpr(self, ctx:IEC61131Parser.BinaryOrExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryOrExpr.
    def exitBinaryOrExpr(self, ctx:IEC61131Parser.BinaryOrExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryCmpExpr.
    def enterBinaryCmpExpr(self, ctx:IEC61131Parser.BinaryCmpExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryCmpExpr.
    def exitBinaryCmpExpr(self, ctx:IEC61131Parser.BinaryCmpExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryModDivExpr.
    def enterBinaryModDivExpr(self, ctx:IEC61131Parser.BinaryModDivExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryModDivExpr.
    def exitBinaryModDivExpr(self, ctx:IEC61131Parser.BinaryModDivExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#parenExpr.
    def enterParenExpr(self, ctx:IEC61131Parser.ParenExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#parenExpr.
    def exitParenExpr(self, ctx:IEC61131Parser.ParenExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryXORExpr.
    def enterBinaryXORExpr(self, ctx:IEC61131Parser.BinaryXORExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryXORExpr.
    def exitBinaryXORExpr(self, ctx:IEC61131Parser.BinaryXORExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#unaryMinusExpr.
    def enterUnaryMinusExpr(self, ctx:IEC61131Parser.UnaryMinusExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#unaryMinusExpr.
    def exitUnaryMinusExpr(self, ctx:IEC61131Parser.UnaryMinusExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#primaryExpr.
    def enterPrimaryExpr(self, ctx:IEC61131Parser.PrimaryExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#primaryExpr.
    def exitPrimaryExpr(self, ctx:IEC61131Parser.PrimaryExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryPowerExpr.
    def enterBinaryPowerExpr(self, ctx:IEC61131Parser.BinaryPowerExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryPowerExpr.
    def exitBinaryPowerExpr(self, ctx:IEC61131Parser.BinaryPowerExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryMultExpr.
    def enterBinaryMultExpr(self, ctx:IEC61131Parser.BinaryMultExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryMultExpr.
    def exitBinaryMultExpr(self, ctx:IEC61131Parser.BinaryMultExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryPlusMinusExpr.
    def enterBinaryPlusMinusExpr(self, ctx:IEC61131Parser.BinaryPlusMinusExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryPlusMinusExpr.
    def exitBinaryPlusMinusExpr(self, ctx:IEC61131Parser.BinaryPlusMinusExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryEqExpr.
    def enterBinaryEqExpr(self, ctx:IEC61131Parser.BinaryEqExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryEqExpr.
    def exitBinaryEqExpr(self, ctx:IEC61131Parser.BinaryEqExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#binaryAndExpr.
    def enterBinaryAndExpr(self, ctx:IEC61131Parser.BinaryAndExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#binaryAndExpr.
    def exitBinaryAndExpr(self, ctx:IEC61131Parser.BinaryAndExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#primary_expression.
    def enterPrimary_expression(self, ctx:IEC61131Parser.Primary_expressionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#primary_expression.
    def exitPrimary_expression(self, ctx:IEC61131Parser.Primary_expressionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#invocation.
    def enterInvocation(self, ctx:IEC61131Parser.InvocationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#invocation.
    def exitInvocation(self, ctx:IEC61131Parser.InvocationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#statement_list.
    def enterStatement_list(self, ctx:IEC61131Parser.Statement_listContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#statement_list.
    def exitStatement_list(self, ctx:IEC61131Parser.Statement_listContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#statement.
    def enterStatement(self, ctx:IEC61131Parser.StatementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#statement.
    def exitStatement(self, ctx:IEC61131Parser.StatementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#empty_statement.
    def enterEmpty_statement(self, ctx:IEC61131Parser.Empty_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#empty_statement.
    def exitEmpty_statement(self, ctx:IEC61131Parser.Empty_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#jump_statement.
    def enterJump_statement(self, ctx:IEC61131Parser.Jump_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#jump_statement.
    def exitJump_statement(self, ctx:IEC61131Parser.Jump_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#label_statement.
    def enterLabel_statement(self, ctx:IEC61131Parser.Label_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#label_statement.
    def exitLabel_statement(self, ctx:IEC61131Parser.Label_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#assignment_statement.
    def enterAssignment_statement(self, ctx:IEC61131Parser.Assignment_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#assignment_statement.
    def exitAssignment_statement(self, ctx:IEC61131Parser.Assignment_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#mult_assignment_statement.
    def enterMult_assignment_statement(self, ctx:IEC61131Parser.Mult_assignment_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#mult_assignment_statement.
    def exitMult_assignment_statement(self, ctx:IEC61131Parser.Mult_assignment_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#invocation_statement.
    def enterInvocation_statement(self, ctx:IEC61131Parser.Invocation_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#invocation_statement.
    def exitInvocation_statement(self, ctx:IEC61131Parser.Invocation_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#variable.
    def enterVariable(self, ctx:IEC61131Parser.VariableContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#variable.
    def exitVariable(self, ctx:IEC61131Parser.VariableContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#variable_names.
    def enterVariable_names(self, ctx:IEC61131Parser.Variable_namesContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#variable_names.
    def exitVariable_names(self, ctx:IEC61131Parser.Variable_namesContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#symbolic_variable.
    def enterSymbolic_variable(self, ctx:IEC61131Parser.Symbolic_variableContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#symbolic_variable.
    def exitSymbolic_variable(self, ctx:IEC61131Parser.Symbolic_variableContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#subscript_list.
    def enterSubscript_list(self, ctx:IEC61131Parser.Subscript_listContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#subscript_list.
    def exitSubscript_list(self, ctx:IEC61131Parser.Subscript_listContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#direct_variable.
    def enterDirect_variable(self, ctx:IEC61131Parser.Direct_variableContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#direct_variable.
    def exitDirect_variable(self, ctx:IEC61131Parser.Direct_variableContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#return_statement.
    def enterReturn_statement(self, ctx:IEC61131Parser.Return_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#return_statement.
    def exitReturn_statement(self, ctx:IEC61131Parser.Return_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#param_assignment.
    def enterParam_assignment(self, ctx:IEC61131Parser.Param_assignmentContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#param_assignment.
    def exitParam_assignment(self, ctx:IEC61131Parser.Param_assignmentContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#if_statement.
    def enterIf_statement(self, ctx:IEC61131Parser.If_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#if_statement.
    def exitIf_statement(self, ctx:IEC61131Parser.If_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#case_statement.
    def enterCase_statement(self, ctx:IEC61131Parser.Case_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#case_statement.
    def exitCase_statement(self, ctx:IEC61131Parser.Case_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#case_entry.
    def enterCase_entry(self, ctx:IEC61131Parser.Case_entryContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#case_entry.
    def exitCase_entry(self, ctx:IEC61131Parser.Case_entryContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#case_condition.
    def enterCase_condition(self, ctx:IEC61131Parser.Case_conditionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#case_condition.
    def exitCase_condition(self, ctx:IEC61131Parser.Case_conditionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#for_statement.
    def enterFor_statement(self, ctx:IEC61131Parser.For_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#for_statement.
    def exitFor_statement(self, ctx:IEC61131Parser.For_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#while_statement.
    def enterWhile_statement(self, ctx:IEC61131Parser.While_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#while_statement.
    def exitWhile_statement(self, ctx:IEC61131Parser.While_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#repeat_statement.
    def enterRepeat_statement(self, ctx:IEC61131Parser.Repeat_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#repeat_statement.
    def exitRepeat_statement(self, ctx:IEC61131Parser.Repeat_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#exit_statement.
    def enterExit_statement(self, ctx:IEC61131Parser.Exit_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#exit_statement.
    def exitExit_statement(self, ctx:IEC61131Parser.Exit_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#continue_statement.
    def enterContinue_statement(self, ctx:IEC61131Parser.Continue_statementContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#continue_statement.
    def exitContinue_statement(self, ctx:IEC61131Parser.Continue_statementContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#sfc.
    def enterSfc(self, ctx:IEC61131Parser.SfcContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#sfc.
    def exitSfc(self, ctx:IEC61131Parser.SfcContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#sfc_network.
    def enterSfc_network(self, ctx:IEC61131Parser.Sfc_networkContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#sfc_network.
    def exitSfc_network(self, ctx:IEC61131Parser.Sfc_networkContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#init_step.
    def enterInit_step(self, ctx:IEC61131Parser.Init_stepContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#init_step.
    def exitInit_step(self, ctx:IEC61131Parser.Init_stepContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#step.
    def enterStep(self, ctx:IEC61131Parser.StepContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#step.
    def exitStep(self, ctx:IEC61131Parser.StepContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#action_association.
    def enterAction_association(self, ctx:IEC61131Parser.Action_associationContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#action_association.
    def exitAction_association(self, ctx:IEC61131Parser.Action_associationContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#actionQualifier.
    def enterActionQualifier(self, ctx:IEC61131Parser.ActionQualifierContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#actionQualifier.
    def exitActionQualifier(self, ctx:IEC61131Parser.ActionQualifierContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#transition.
    def enterTransition(self, ctx:IEC61131Parser.TransitionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#transition.
    def exitTransition(self, ctx:IEC61131Parser.TransitionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#steps.
    def enterSteps(self, ctx:IEC61131Parser.StepsContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#steps.
    def exitSteps(self, ctx:IEC61131Parser.StepsContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#transitionCond.
    def enterTransitionCond(self, ctx:IEC61131Parser.TransitionCondContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#transitionCond.
    def exitTransitionCond(self, ctx:IEC61131Parser.TransitionCondContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#action.
    def enterAction(self, ctx:IEC61131Parser.ActionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#action.
    def exitAction(self, ctx:IEC61131Parser.ActionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilBody.
    def enterIlBody(self, ctx:IEC61131Parser.IlBodyContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilBody.
    def exitIlBody(self, ctx:IEC61131Parser.IlBodyContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilInstruction.
    def enterIlInstruction(self, ctx:IEC61131Parser.IlInstructionContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilInstruction.
    def exitIlInstruction(self, ctx:IEC61131Parser.IlInstructionContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilSInstr.
    def enterIlSInstr(self, ctx:IEC61131Parser.IlSInstrContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilSInstr.
    def exitIlSInstr(self, ctx:IEC61131Parser.IlSInstrContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilInstr.
    def enterIlInstr(self, ctx:IEC61131Parser.IlInstrContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilInstr.
    def exitIlInstr(self, ctx:IEC61131Parser.IlInstrContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilSInstrList.
    def enterIlSInstrList(self, ctx:IEC61131Parser.IlSInstrListContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilSInstrList.
    def exitIlSInstrList(self, ctx:IEC61131Parser.IlSInstrListContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilSimple.
    def enterIlSimple(self, ctx:IEC61131Parser.IlSimpleContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilSimple.
    def exitIlSimple(self, ctx:IEC61131Parser.IlSimpleContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilExpr.
    def enterIlExpr(self, ctx:IEC61131Parser.IlExprContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilExpr.
    def exitIlExpr(self, ctx:IEC61131Parser.IlExprContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilFunctionCall.
    def enterIlFunctionCall(self, ctx:IEC61131Parser.IlFunctionCallContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilFunctionCall.
    def exitIlFunctionCall(self, ctx:IEC61131Parser.IlFunctionCallContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilFormalFunctionCall.
    def enterIlFormalFunctionCall(self, ctx:IEC61131Parser.IlFormalFunctionCallContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilFormalFunctionCall.
    def exitIlFormalFunctionCall(self, ctx:IEC61131Parser.IlFormalFunctionCallContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilJump.
    def enterIlJump(self, ctx:IEC61131Parser.IlJumpContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilJump.
    def exitIlJump(self, ctx:IEC61131Parser.IlJumpContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilCall.
    def enterIlCall(self, ctx:IEC61131Parser.IlCallContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilCall.
    def exitIlCall(self, ctx:IEC61131Parser.IlCallContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#ilOperand.
    def enterIlOperand(self, ctx:IEC61131Parser.IlOperandContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#ilOperand.
    def exitIlOperand(self, ctx:IEC61131Parser.IlOperandContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#jump_op.
    def enterJump_op(self, ctx:IEC61131Parser.Jump_opContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#jump_op.
    def exitJump_op(self, ctx:IEC61131Parser.Jump_opContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#call_op.
    def enterCall_op(self, ctx:IEC61131Parser.Call_opContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#call_op.
    def exitCall_op(self, ctx:IEC61131Parser.Call_opContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#simple_op.
    def enterSimple_op(self, ctx:IEC61131Parser.Simple_opContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#simple_op.
    def exitSimple_op(self, ctx:IEC61131Parser.Simple_opContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#exprOperator.
    def enterExprOperator(self, ctx:IEC61131Parser.ExprOperatorContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#exprOperator.
    def exitExprOperator(self, ctx:IEC61131Parser.ExprOperatorContext):
        pass


    # Enter a parse tree produced by IEC61131Parser#il_param_assignment.
    def enterIl_param_assignment(self, ctx:IEC61131Parser.Il_param_assignmentContext):
        pass

    # Exit a parse tree produced by IEC61131Parser#il_param_assignment.
    def exitIl_param_assignment(self, ctx:IEC61131Parser.Il_param_assignmentContext):
        pass



del IEC61131Parser