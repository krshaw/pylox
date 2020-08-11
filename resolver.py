import expr
import stmt
import lox
from dataclasses import dataclass

#class Resolver(expr.Visitor, stmt.Visitor):
class Resolver():
	def __init__(self, interpreter, lox):
		self.lox = lox
		self.__interpreter = interpreter
		# bool represents if the variable is defined, int represents the index to be used when
		# accessing the value via an array in the interpreter
		# scopes: list[{str: (bool, int), ... , str: (bool, int)}]
		self.__scopes = []
		self.indices = [0]
		self.__unused_variables = []
		self.__current_function = "NONE"
		self.__current_class = "NONE"
	
	def visit_block_stmt(self, block):
		self.__begin_scope()
		self.resolve(block.statements)
		self.__end_scope()

	def visit_var_stmt(self, var_declaration):
		self.__declare(var_declaration.token_name)
		# if the variable is declared to an initial value
		if var_declaration.initial_expr != None:
			self.resolve(var_declaration.initial_expr)
		self.__define(var_declaration.token_name)
	
	def visit_this_expr(self, expr):
		if self.__current_class == "NONE":
			self.lox.error("Cannot use 'this' outside of class", token=expr.keyword_token)
			return
		self.__resolve_local(expr, expr.keyword_token)
	def visit_super_expr(self, expr):
		if self.__current_class == "NONE":
			self.lox.error("Cannot use 'super' outside of class", token=expr.keyword_token)
			return
		elif self.__current_class == "CLASS":
			self.lox.error("Cannot use 'super' in a class with no super class", token=expr.keyword_token)
			return
		self.__resolve_local(expr, expr.keyword_token)
	def visit_variable_expr(self, expr):
		# why can we conclude that a reference to a local variable in its own initializer 
		# it occuring from this condition?
		# ANSWER: we can conclude that if we use .get() instead of bracket accessing on the 
		# dictionary, so that it can return None if the variable is not found
		# this condition being true means the variable has been declared, and now we are 
		# resolving the variable expression as the initial expression, so it is not defined yet
		if self.__scopes and self.__scopes[-1].get(expr.token_name.lexeme) == False:
			self.lox.error("Cannot read local variable in its own initializer", token=expr.token_name)
		self.__resolve_local(expr, expr.token_name)
		self.__use_variable(expr.token_name)
	def __use_variable(self, var_name):
		for idx, variable in enumerate(self.__unused_variables[::-1]):
			if var_name.lexeme == variable.lexeme:
				del self.__unused_variables[len(self.__unused_variables) - idx - 1]
				break

	def visit_assign_expr(self, assignment):
		self.resolve(assignment.value)
		self.__resolve_local(assignment, assignment.token_name)
	
	def visit_class_stmt(self, class_dec):
		@dataclass
		class DummyToken():
			lexeme: str
		enclosing_class = self.__current_class
		self.__current_class = "CLASS"
		self.__declare(class_dec.name_token)
		# it is safe to define before checking for self reference in the class definition
		# because this allows for recursive structures such as a linked list or tree
		self.__define(class_dec.name_token)
		if class_dec.superclasses:
			for superclass in class_dec.superclasses:
				if superclass.token_name.lexeme == class_dec.name_token.lexeme:
					self.lox.error("A class cannot inherit from itself")
		if class_dec.superclasses: 
			self.__current_class = "SUBCLASS"
			self.resolve(class_dec.superclasses)
		# begin a new scope for the new environment containing the 'super' definition
		if class_dec.superclasses:
			self.__begin_scope()
			super_token = DummyToken("super")
			self.__declare(super_token)
			self.__define(super_token)
			self.__use_variable(super_token)
		self.__begin_scope()
		this_token = DummyToken("this")
		self.__declare(this_token)
		self.__define(this_token)
		for method in class_dec.methods:
			declaration = "METHOD"
			if method.name_token.lexeme == "init": declaration = "INITIALIZER"
			self.__resolve_function(method, declaration)
		for static_method in class_dec.static_methods:
			declaration = "STATIC_METHOD"
			self.__resolve_function(static_method, declaration)
		self.__end_scope()
		if class_dec.superclasses: self.__end_scope()
		self.__current_class = enclosing_class
	def visit_get_expr(self, expr):
		self.resolve(expr.object_instance)
	def visit_set_expr(self, expr):
		self.resolve(expr.object_instance)
		self.resolve(expr.value)
	def visit_function_stmt(self, function_dec):
		self.__declare(function_dec.name_token)
		self.__define(function_dec.name_token)
		self.__resolve_function(function_dec, "FUNCTION")
	
	def visit_anonymous_expr(self, function):
		# anonymous function is same as function declaration without the name binded to it
		self.__resolve_function(function, "FUNCTION")

	# these are the "boring" nodes to resolve, not much going on here
	def visit_expression_stmt(self, stmt):
		self.resolve(stmt.expression)
	def visit_print_stmt(self, stmt):
		self.resolve(stmt.expression)
	def visit_if_stmt(self, stmt):
		self.resolve(stmt.condition)
		self.resolve(stmt.true_branch)
		if stmt.false_branch != None: self.resolve(stmt.false_branch)
	def visit_while_stmt(self, stmt):
		self.resolve(stmt.condition)
		self.resolve(stmt.body)
	def visit_return_stmt(self, stmt):
		if self.__current_function == "NONE":
			# this creates a problem, because now the return exception is never caught by the 
			# interpreter. it is fixed by only running the interpreter in lox.py if
			# there are no errors in the resolver
			self.lox.error("Cannot return from top-level code", token=stmt.keyword)
		if self.__current_function == "INITIALIZER" and stmt.value is not None:
			self.lox.error("Cannot return a value from initializer", token=stmt.keyword)
		if stmt.value != None: self.resolve(stmt.value)
	def visit_break_stmt(self, stmt):
		# there is nothing to resolve, so just return
		return
	
	# these are also "boring" nodes, but they are expressions instead of statements
	def visit_binary_expr(self, expr):
		self.resolve(expr.left_expr)
		self.resolve(expr.right_expr)
	def visit_grouping_expr(self, expr):
		self.resolve(expr.expression)
	def visit_literal_expr(self, expr):
		return # there is no sub expression or sub statement (it is a leaf node), so just return
	def visit_unary_expr(self, expr):
		self.resolve(expr.expression)
	def visit_ternary_expr(self, expr):
		self.resolve(expr.condition)
		self.resolve(expr.true_part)
		self.resolve(expr.false_part)
	def visit_logic_expr(self, expr):
		self.resolve(expr.left_expr)
		self.resolve(expr.right_expr)
	def visit_call_expr(self, expr):
		self.resolve(expr.callee_expr)
		# we don't need to walk the list of arguments here because the resolve() method
		# can also take a list of expressions as its argument and resolve each one
		self.resolve(expr.arguments)
	def visit_array_expr(self, expr):
		self.resolve(expr.elements)
	def visit_subscriptget_expr(self, expr):
		self.resolve(expr.array_instance)
		self.resolve(expr.index)
	def visit_subscriptset_expr(self, expr):
		self.resolve(expr.array_instance)
		self.resolve(expr.index)
		self.resolve(expr.value)

	def __resolve_function(self, function, function_type):
		enclosing_function = self.__current_function
		self.__current_function = function_type
		self.__begin_scope()
		for param in function.param_tokens:
			self.__declare(param)
			self.__define(param)
		# will call accept() on the block, which then visits the block node, which then 
		# resolves as expected
		self.resolve(function.body)
		self.__end_scope()
		self.__current_function = enclosing_function

	def __resolve_local(self, expr, name):
		# this is where the counting of "hops" is done from the current scope where the variable
		# is used, to the scope where the variable is actually declared
		for idx, scope in enumerate(self.__scopes[::-1]):
			# if the variable declaration has been found in this scope
			if name.lexeme in scope: 
				# returning idx as the number of hops works perfectly fine
				self.__interpreter.resolve(expr, idx, scope[name.lexeme][1])
				return
		
	def __begin_scope(self):
		# this dictionary appended to scopes will consist of <str, bool> key-value pairs
		self.__scopes.append({})
		# new scope is started, so start "new" index starting at 0 for the array accessing
		# of variables in the interpreter
		self.indices.append(0)

	# resolvee is either a single statement or expr, or a list of statements (from a block stmt)
	def resolve(self, resolvee):
		if isinstance(resolvee, list):
			for statement in resolvee:
				self.resolve(statement)
		else:
			resolvee.accept(self)
	
	def check_unused_variables(self):
		if self.__unused_variables: 
			self.lox.error("Unused variable", token=self.__unused_variables[-1])
	def __end_scope(self):
		self.__scopes.pop()
		self.indices.pop()

	def __declare(self, token_name):
		if not self.__scopes: return
		scope = self.__scopes[-1]
		if token_name.lexeme in scope: 
			self.lox.error("Variable with this name already declared in scope", token=token_name)
		scope[token_name.lexeme] = (False, self.indices[-1])
		self.indices[-1] += 1
		if token_name.lexeme != "this": self.__unused_variables.append(token_name)
	def __define(self, token_name):
		if not self.__scopes: return
		self.__scopes[-1][token_name.lexeme] = (True, self.__scopes[-1][token_name.lexeme][1])
