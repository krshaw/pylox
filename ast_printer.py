from expr import Binary
from expr import Grouping
from expr import Literal
from expr import Unary
#from expr import Visitor
from tok import Token

#class ASTPrinter(Visitor):
class ASTPrinter():
	def display(self, expr):
		# self is a visitor in this case, and we are gonna have to define 
		# the visitor operation for each type of expression. 
		return expr.accept(self)
	# visit_binary_expr(expr: Binary)
	def visit_binary_expr(self, expr) -> str:
		return self.parenthesize(expr.operator_token.lexeme, (expr.left_expr, expr.right_expr))
	# visit_grouping_expr(expr: Grouping)
	def visit_grouping_expr(self, expr) -> str:
		return self.parenthesize("group", [expr.expression])
	# visit_literal_expr(expr: Literal)
	def visit_literal_expr(self, expr) -> str:
		if expr.value == None: return 'nil'
		return str(expr.value)
	# visit_unary_expr(expr: Unary)
	def visit_unary_expr(self, expr) -> str:
		return self.parenthesize(expr.operator_token.lexeme, [expr.expression])
	def visit_ternary_expr(self, expr) -> str:
		return self.parenthesize("Ternary", [expr.condition, expr.true_part, expr.false_part])
	# second argument needs to be passed as an iterable!!
	# parenthesize(name: str, exprs: Expr[])
	def parenthesize(self, name, exprs) -> str:
		res = f"({name}"
		for expr in exprs:
			res += ' '
			# for each expression, delve into the sub expressions; resursive algorithm
			res += expr.accept(self)
		res += ')'
		return res

#class RPN_Printer(Visitor):
class RPN_Printer():
	def display(self, expr):
		return expr.accept(self)
	def visit_binary_expr(self, expr):
		# still need things such as name and sub-expressions
		return self.rpn(expr.operator_token.lexeme, [expr.left_expr, expr.right_expr])
	def visit_grouping_expr(self, expr):
		return self.rpn("group" [expr.expression])
	def visit_literal_expr(self, expr):
		return str(expr.value) if expr.value != None else 'nil'
	def visit_unary_expr(self, expr):
		return self.rpn(expr.operator_token.lexeme, [expr.expression])
	def rpn(self, name, exprs):
		res = ""
		for expr in exprs:
			# resursive call again. This time we are appending the sub expressions first
			res += expr.accept(self)
			res += ' '
		res += name
		return res

