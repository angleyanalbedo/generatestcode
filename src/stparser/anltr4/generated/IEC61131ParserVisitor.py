# Generated from IEC61131Parser.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .IEC61131Parser import IEC61131Parser
else:
    from IEC61131Parser import IEC61131Parser

# This class defines a complete generic visitor for a parse tree produced by IEC61131Parser.

class IEC61131ParserVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by IEC61131Parser#start.
    def visitStart(self, ctx:IEC61131Parser.StartContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#namespace_declaration.
    def visitNamespace_declaration(self, ctx:IEC61131Parser.Namespace_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#namespace_elements.
    def visitNamespace_elements(self, ctx:IEC61131Parser.Namespace_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#full_qualified_identifier.
    def visitFull_qualified_identifier(self, ctx:IEC61131Parser.Full_qualified_identifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#using_directive.
    def visitUsing_directive(self, ctx:IEC61131Parser.Using_directiveContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#library_element_declaration.
    def visitLibrary_element_declaration(self, ctx:IEC61131Parser.Library_element_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#constant.
    def visitConstant(self, ctx:IEC61131Parser.ConstantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#cast.
    def visitCast(self, ctx:IEC61131Parser.CastContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#integer.
    def visitInteger(self, ctx:IEC61131Parser.IntegerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#bits.
    def visitBits(self, ctx:IEC61131Parser.BitsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#real.
    def visitReal(self, ctx:IEC61131Parser.RealContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#string.
    def visitString(self, ctx:IEC61131Parser.StringContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#time.
    def visitTime(self, ctx:IEC61131Parser.TimeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#timeofday.
    def visitTimeofday(self, ctx:IEC61131Parser.TimeofdayContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#date.
    def visitDate(self, ctx:IEC61131Parser.DateContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#datetime.
    def visitDatetime(self, ctx:IEC61131Parser.DatetimeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ref_null.
    def visitRef_null(self, ctx:IEC61131Parser.Ref_nullContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#data_type_name.
    def visitData_type_name(self, ctx:IEC61131Parser.Data_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#non_generic_type_name.
    def visitNon_generic_type_name(self, ctx:IEC61131Parser.Non_generic_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#elementary_type_name.
    def visitElementary_type_name(self, ctx:IEC61131Parser.Elementary_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#numeric_type_name.
    def visitNumeric_type_name(self, ctx:IEC61131Parser.Numeric_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#integer_type_name.
    def visitInteger_type_name(self, ctx:IEC61131Parser.Integer_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#signed_integer_type_name.
    def visitSigned_integer_type_name(self, ctx:IEC61131Parser.Signed_integer_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#unsigned_integer_type_name.
    def visitUnsigned_integer_type_name(self, ctx:IEC61131Parser.Unsigned_integer_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#real_type_name.
    def visitReal_type_name(self, ctx:IEC61131Parser.Real_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#date_type_name.
    def visitDate_type_name(self, ctx:IEC61131Parser.Date_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#bit_string_type_name.
    def visitBit_string_type_name(self, ctx:IEC61131Parser.Bit_string_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#generic_type_name.
    def visitGeneric_type_name(self, ctx:IEC61131Parser.Generic_type_nameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#data_type_declaration.
    def visitData_type_declaration(self, ctx:IEC61131Parser.Data_type_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#type_declaration.
    def visitType_declaration(self, ctx:IEC61131Parser.Type_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#initializations_constant.
    def visitInitializations_constant(self, ctx:IEC61131Parser.Initializations_constantContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#initializations_identifier.
    def visitInitializations_identifier(self, ctx:IEC61131Parser.Initializations_identifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#initializations_array_initialization.
    def visitInitializations_array_initialization(self, ctx:IEC61131Parser.Initializations_array_initializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#initializations_structure_initialization.
    def visitInitializations_structure_initialization(self, ctx:IEC61131Parser.Initializations_structure_initializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#subrange_spec_init.
    def visitSubrange_spec_init(self, ctx:IEC61131Parser.Subrange_spec_initContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#subrange.
    def visitSubrange(self, ctx:IEC61131Parser.SubrangeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#enumerated_specification.
    def visitEnumerated_specification(self, ctx:IEC61131Parser.Enumerated_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#array_specification.
    def visitArray_specification(self, ctx:IEC61131Parser.Array_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#array_initialization.
    def visitArray_initialization(self, ctx:IEC61131Parser.Array_initializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#array_initial_elements.
    def visitArray_initial_elements(self, ctx:IEC61131Parser.Array_initial_elementsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#array_initial_element.
    def visitArray_initial_element(self, ctx:IEC61131Parser.Array_initial_elementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#structure_declaration.
    def visitStructure_declaration(self, ctx:IEC61131Parser.Structure_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#name.
    def visitName(self, ctx:IEC61131Parser.NameContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#structure_initialization.
    def visitStructure_initialization(self, ctx:IEC61131Parser.Structure_initializationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#string_type_declaration.
    def visitString_type_declaration(self, ctx:IEC61131Parser.String_type_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#reference_specification.
    def visitReference_specification(self, ctx:IEC61131Parser.Reference_specificationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#reference_value.
    def visitReference_value(self, ctx:IEC61131Parser.Reference_valueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#identifier_list.
    def visitIdentifier_list(self, ctx:IEC61131Parser.Identifier_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#function_declaration.
    def visitFunction_declaration(self, ctx:IEC61131Parser.Function_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#var_decls.
    def visitVar_decls(self, ctx:IEC61131Parser.Var_declsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#var_decl.
    def visitVar_decl(self, ctx:IEC61131Parser.Var_declContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#var_decl_inner.
    def visitVar_decl_inner(self, ctx:IEC61131Parser.Var_decl_innerContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#variable_keyword.
    def visitVariable_keyword(self, ctx:IEC61131Parser.Variable_keywordContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#access_specifier.
    def visitAccess_specifier(self, ctx:IEC61131Parser.Access_specifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#function_block_declaration.
    def visitFunction_block_declaration(self, ctx:IEC61131Parser.Function_block_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#body.
    def visitBody(self, ctx:IEC61131Parser.BodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#funcBody.
    def visitFuncBody(self, ctx:IEC61131Parser.FuncBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#interface_declaration.
    def visitInterface_declaration(self, ctx:IEC61131Parser.Interface_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#class_declaration.
    def visitClass_declaration(self, ctx:IEC61131Parser.Class_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#methods.
    def visitMethods(self, ctx:IEC61131Parser.MethodsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#method.
    def visitMethod(self, ctx:IEC61131Parser.MethodContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#program_declaration.
    def visitProgram_declaration(self, ctx:IEC61131Parser.Program_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#global_variable_list_declaration.
    def visitGlobal_variable_list_declaration(self, ctx:IEC61131Parser.Global_variable_list_declarationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#stl_list.
    def visitStl_list(self, ctx:IEC61131Parser.Stl_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#stl_expression.
    def visitStl_expression(self, ctx:IEC61131Parser.Stl_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#stl_call.
    def visitStl_call(self, ctx:IEC61131Parser.Stl_callContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#unaryNegateExpr.
    def visitUnaryNegateExpr(self, ctx:IEC61131Parser.UnaryNegateExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryOrExpr.
    def visitBinaryOrExpr(self, ctx:IEC61131Parser.BinaryOrExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryCmpExpr.
    def visitBinaryCmpExpr(self, ctx:IEC61131Parser.BinaryCmpExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryModDivExpr.
    def visitBinaryModDivExpr(self, ctx:IEC61131Parser.BinaryModDivExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#parenExpr.
    def visitParenExpr(self, ctx:IEC61131Parser.ParenExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryXORExpr.
    def visitBinaryXORExpr(self, ctx:IEC61131Parser.BinaryXORExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#unaryMinusExpr.
    def visitUnaryMinusExpr(self, ctx:IEC61131Parser.UnaryMinusExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#primaryExpr.
    def visitPrimaryExpr(self, ctx:IEC61131Parser.PrimaryExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryPowerExpr.
    def visitBinaryPowerExpr(self, ctx:IEC61131Parser.BinaryPowerExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryMultExpr.
    def visitBinaryMultExpr(self, ctx:IEC61131Parser.BinaryMultExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryPlusMinusExpr.
    def visitBinaryPlusMinusExpr(self, ctx:IEC61131Parser.BinaryPlusMinusExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryEqExpr.
    def visitBinaryEqExpr(self, ctx:IEC61131Parser.BinaryEqExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#binaryAndExpr.
    def visitBinaryAndExpr(self, ctx:IEC61131Parser.BinaryAndExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#primary_expression.
    def visitPrimary_expression(self, ctx:IEC61131Parser.Primary_expressionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#invocation.
    def visitInvocation(self, ctx:IEC61131Parser.InvocationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#statement_list.
    def visitStatement_list(self, ctx:IEC61131Parser.Statement_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#statement.
    def visitStatement(self, ctx:IEC61131Parser.StatementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#empty_statement.
    def visitEmpty_statement(self, ctx:IEC61131Parser.Empty_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#jump_statement.
    def visitJump_statement(self, ctx:IEC61131Parser.Jump_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#label_statement.
    def visitLabel_statement(self, ctx:IEC61131Parser.Label_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#assignment_statement.
    def visitAssignment_statement(self, ctx:IEC61131Parser.Assignment_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#mult_assignment_statement.
    def visitMult_assignment_statement(self, ctx:IEC61131Parser.Mult_assignment_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#invocation_statement.
    def visitInvocation_statement(self, ctx:IEC61131Parser.Invocation_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#variable.
    def visitVariable(self, ctx:IEC61131Parser.VariableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#variable_names.
    def visitVariable_names(self, ctx:IEC61131Parser.Variable_namesContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#symbolic_variable.
    def visitSymbolic_variable(self, ctx:IEC61131Parser.Symbolic_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#subscript_list.
    def visitSubscript_list(self, ctx:IEC61131Parser.Subscript_listContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#direct_variable.
    def visitDirect_variable(self, ctx:IEC61131Parser.Direct_variableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#return_statement.
    def visitReturn_statement(self, ctx:IEC61131Parser.Return_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#param_assignment.
    def visitParam_assignment(self, ctx:IEC61131Parser.Param_assignmentContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#if_statement.
    def visitIf_statement(self, ctx:IEC61131Parser.If_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#case_statement.
    def visitCase_statement(self, ctx:IEC61131Parser.Case_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#case_entry.
    def visitCase_entry(self, ctx:IEC61131Parser.Case_entryContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#case_condition.
    def visitCase_condition(self, ctx:IEC61131Parser.Case_conditionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#for_statement.
    def visitFor_statement(self, ctx:IEC61131Parser.For_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#while_statement.
    def visitWhile_statement(self, ctx:IEC61131Parser.While_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#repeat_statement.
    def visitRepeat_statement(self, ctx:IEC61131Parser.Repeat_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#exit_statement.
    def visitExit_statement(self, ctx:IEC61131Parser.Exit_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#continue_statement.
    def visitContinue_statement(self, ctx:IEC61131Parser.Continue_statementContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#sfc.
    def visitSfc(self, ctx:IEC61131Parser.SfcContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#sfc_network.
    def visitSfc_network(self, ctx:IEC61131Parser.Sfc_networkContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#init_step.
    def visitInit_step(self, ctx:IEC61131Parser.Init_stepContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#step.
    def visitStep(self, ctx:IEC61131Parser.StepContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#action_association.
    def visitAction_association(self, ctx:IEC61131Parser.Action_associationContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#actionQualifier.
    def visitActionQualifier(self, ctx:IEC61131Parser.ActionQualifierContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#transition.
    def visitTransition(self, ctx:IEC61131Parser.TransitionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#steps.
    def visitSteps(self, ctx:IEC61131Parser.StepsContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#transitionCond.
    def visitTransitionCond(self, ctx:IEC61131Parser.TransitionCondContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#action.
    def visitAction(self, ctx:IEC61131Parser.ActionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilBody.
    def visitIlBody(self, ctx:IEC61131Parser.IlBodyContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilInstruction.
    def visitIlInstruction(self, ctx:IEC61131Parser.IlInstructionContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilSInstr.
    def visitIlSInstr(self, ctx:IEC61131Parser.IlSInstrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilInstr.
    def visitIlInstr(self, ctx:IEC61131Parser.IlInstrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilSInstrList.
    def visitIlSInstrList(self, ctx:IEC61131Parser.IlSInstrListContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilSimple.
    def visitIlSimple(self, ctx:IEC61131Parser.IlSimpleContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilExpr.
    def visitIlExpr(self, ctx:IEC61131Parser.IlExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilFunctionCall.
    def visitIlFunctionCall(self, ctx:IEC61131Parser.IlFunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilFormalFunctionCall.
    def visitIlFormalFunctionCall(self, ctx:IEC61131Parser.IlFormalFunctionCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilJump.
    def visitIlJump(self, ctx:IEC61131Parser.IlJumpContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilCall.
    def visitIlCall(self, ctx:IEC61131Parser.IlCallContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#ilOperand.
    def visitIlOperand(self, ctx:IEC61131Parser.IlOperandContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#jump_op.
    def visitJump_op(self, ctx:IEC61131Parser.Jump_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#call_op.
    def visitCall_op(self, ctx:IEC61131Parser.Call_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#simple_op.
    def visitSimple_op(self, ctx:IEC61131Parser.Simple_opContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#exprOperator.
    def visitExprOperator(self, ctx:IEC61131Parser.ExprOperatorContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by IEC61131Parser#il_param_assignment.
    def visitIl_param_assignment(self, ctx:IEC61131Parser.Il_param_assignmentContext):
        return self.visitChildren(ctx)



del IEC61131Parser