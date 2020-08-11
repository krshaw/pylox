class Stmt:
	def accept(self, visitor) -> any:
		pass
class Expression(Stmt):
	def __init__(self, expression):
		self.expression = expression
	def accept(self, visitor) -> any:
		return visitor.visit_expression_stmt(self)
class Print(Stmt):
	def __init__(self, expression):
		self.expression = expression
	def accept(self, visitor) -> any:
		return visitor.visit_print_stmt(self)
class Var(Stmt):
	def __init__(self, token_name, initial_expr):
		self.token_name = token_name
		self.initial_expr = initial_expr
	def accept(self, visitor) -> any:
		return visitor.visit_var_stmt(self)
class Block(Stmt):
	def __init__(self, statements):
		self.statements = statements
	def accept(self, visitor) -> any:
		return visitor.visit_block_stmt(self)
class If(Stmt):
	def __init__(self, condition, true_branch, false_branch):
		self.condition = condition
		self.true_branch = true_branch
		self.false_branch = false_branch
	def accept(self, visitor) -> any:
		return visitor.visit_if_stmt(self)
class While(Stmt):
	def __init__(self, condition, body):
		self.condition = condition
		self.body = body
	def accept(self, visitor) -> any:
		return visitor.visit_while_stmt(self)
class Break(Stmt):
	def __init__(self, loop):
		self.loop = loop
	def accept(self, visitor) -> any:
		return visitor.visit_break_stmt(self)
class Function(Stmt):
	def __init__(self, name_token, param_tokens, body):
		self.name_token = name_token
		self.param_tokens = param_tokens
		self.body = body
	def accept(self, visitor) -> any:
		return visitor.visit_function_stmt(self)
class Return(Stmt):
	def __init__(self, keyword, value):
		self.keyword = keyword
		self.value = value
	def accept(self, visitor) -> any:
		return visitor.visit_return_stmt(self)
class Class(Stmt):
	def __init__(self, name_token, methods, static_methods, superclasses):
		self.name_token = name_token
		self.methods = methods
		self.static_methods = static_methods
		self.superclasses = superclasses
	def accept(self, visitor) -> any:
		return visitor.visit_class_stmt(self)
