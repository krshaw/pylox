class Expr:
	def accept(self, visitor) -> any:
		pass
class Binary(Expr):
	def __init__(self, left_expr, operator_token, right_expr):
		self.left_expr = left_expr
		self.operator_token = operator_token
		self.right_expr = right_expr
	def accept(self, visitor) -> any:
		return visitor.visit_binary_expr(self)
class Grouping(Expr):
	def __init__(self, expression):
		self.expression = expression
	def accept(self, visitor) -> any:
		return visitor.visit_grouping_expr(self)
class Literal(Expr):
	def __init__(self, value):
		self.value = value
	def accept(self, visitor) -> any:
		return visitor.visit_literal_expr(self)
class Unary(Expr):
	def __init__(self, operator_token, expression):
		self.operator_token = operator_token
		self.expression = expression
	def accept(self, visitor) -> any:
		return visitor.visit_unary_expr(self)
class Ternary(Expr):
	def __init__(self, condition, true_part, false_part):
		self.condition = condition
		self.true_part = true_part
		self.false_part = false_part
	def accept(self, visitor) -> any:
		return visitor.visit_ternary_expr(self)
class Variable(Expr):
	def __init__(self, token_name):
		self.token_name = token_name
	def accept(self, visitor) -> any:
		return visitor.visit_variable_expr(self)
class Assign(Expr):
	def __init__(self, token_name, value):
		self.token_name = token_name
		self.value = value
	def accept(self, visitor) -> any:
		return visitor.visit_assign_expr(self)
class Logic(Expr):
	def __init__(self, left_expr, operator_token, right_expr):
		self.left_expr = left_expr
		self.operator_token = operator_token
		self.right_expr = right_expr
	def accept(self, visitor) -> any:
		return visitor.visit_logic_expr(self)
class Call(Expr):
	def __init__(self, callee_expr, paren_token, arguments):
		self.callee_expr = callee_expr
		self.paren_token = paren_token
		self.arguments = arguments
	def accept(self, visitor) -> any:
		return visitor.visit_call_expr(self)
class Anonymous(Expr):
	def __init__(self, param_tokens, body):
		self.param_tokens = param_tokens
		self.body = body
	def accept(self, visitor) -> any:
		return visitor.visit_anonymous_expr(self)
class Get(Expr):
	def __init__(self, object_instance, name_token):
		self.object_instance = object_instance
		self.name_token = name_token
	def accept(self, visitor) -> any:
		return visitor.visit_get_expr(self)
class Set(Expr):
	def __init__(self, object_instance, name_token, value):
		self.object_instance = object_instance
		self.name_token = name_token
		self.value = value
	def accept(self, visitor) -> any:
		return visitor.visit_set_expr(self)
class This(Expr):
	def __init__(self, keyword_token):
		self.keyword_token = keyword_token
	def accept(self, visitor) -> any:
		return visitor.visit_this_expr(self)
class Super(Expr):
	def __init__(self, keyword_token, method_token):
		self.keyword_token = keyword_token
		self.method_token = method_token
	def accept(self, visitor) -> any:
		return visitor.visit_super_expr(self)
class Array(Expr):
	def __init__(self, bracket_token, elements):
		self.bracket_token = bracket_token
		self.elements = elements
	def accept(self, visitor) -> any:
		return visitor.visit_array_expr(self)
class SubscriptGet(Expr):
	def __init__(self, array_instance, index, bracket):
		self.array_instance = array_instance
		self.index = index
		self.bracket = bracket
	def accept(self, visitor) -> any:
		return visitor.visit_subscriptget_expr(self)
class SubscriptSet(Expr):
	def __init__(self, array_instance, index, value, bracket):
		self.array_instance = array_instance
		self.index = index
		self.value = value
		self.bracket = bracket
	def accept(self, visitor) -> any:
		return visitor.visit_subscriptset_expr(self)
