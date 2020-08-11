import time
from tok import Token
import expr
from stmt import Block
from expr import Set
import stmt
from environment import Environment
from lox_callable import *
from lox_instance import *
from return_exception import Return
import lox

class Interpreter():
	def __init__(self, is_REPL, lox):
		self.lox = lox
		self.globals = Environment()
		self.__environment = self.globals
		# {var_expr: (int, int)} (indicating number of hops and the index in the environment)
		self.__locals = {}
		self.__is_REPL = is_REPL
		# can use ducktyping here, the value for clock just needs to be any object
		# that has arity(), call(), and __str__()
		class clock_caller(Callable):
			def call(self, interpreter, arguments):
				return time.time()
			def arity(self): return 0
			def __str__(self): return "<native fn>"
		self.globals.define("clock", clock_caller())

	def interpret(self, stmts) -> None:
		try:
			for stmt in stmts:
				# now because we added support for expressions in the REPL, stmt could be an
				# expression or a statement
				if self.__is_REPL and isinstance(stmt, expr.Expr):
					value = self.evaluate(stmt)
					print(self.stringify(value))
				else:
					self.execute(stmt)
		except RunTimeError as error:
			self.lox.run_time_error(error)

	# method that gets the whole executing started. executes whatever visit method is associated
	# with the current statement (i.e. "self"). 
	def execute(self, stmt):
		stmt.accept(self)

	def stringify(self, value):
		if value is None: return "nil"
		if type(value) == float:
			text = str(value)
			return text[:-2] if text.endswith(".0") else text
		if type(value) == bool: value = str(value).lower()
		return str(value)

	def evaluate(self, expr) -> any:
		return expr.accept(self)
	
	def resolve(self, var_expr, depth, index):
		self.__locals[var_expr] = (depth, index)

	# visitor methods for statements
	def visit_var_stmt(self, stmt) -> None:
		value = None
		if stmt.initial_expr is None:
			# need to assign a special value to indicate to the other methods in the 
			# Environment object that this variable is not yet initialized. To do this, we 
			# can set value to something that is not in the lox language, so that the user 
			# couldn't have possibly initialized the variable yet. This way we know to handle it
			# differently in the .get() method. (if type(value) == list: report_error()...)
			value = []
		else:
			value = self.evaluate(stmt.initial_expr)
		self.__environment.define(stmt.token_name.lexeme, value)

	def visit_expression_stmt(self, stmt) -> None: # simply executes the expression
		self.evaluate(stmt.expression)

	def visit_print_stmt(self, stmt) -> None: # executes the expression, and print the result
		value = self.evaluate(stmt.expression)
		print(self.stringify(value))

	def visit_block_stmt(self, stmt):
		# pass in the list of statements, and create a new scope for this environment
		self.execute_block(stmt.statements, Environment(self.__environment))
	def execute_block(self, statements, environment):
		outer = self.__environment
		try:
			# update the environment to the new inner one (which will search the outer ones
			# as needed)
			self.__environment = environment
			for stmt in statements:
				self.execute(stmt)
		finally:
			self.__environment = outer;
	
	def visit_if_stmt(self, stmt):
		condition = self.evaluate(stmt.condition)
		if self.__is_truthy(condition):
			self.execute(stmt.true_branch)
		elif stmt.false_branch is not None:
			self.execute(stmt.false_branch)
	
	def visit_while_stmt(self, stmt):
		# need to be constantly evaluating condition, not just evaluating it once
		while self.__is_truthy(self.evaluate(stmt.condition)):
			self.execute(stmt.body)
	
	def visit_break_stmt(self, stmt):
		# need to break out of the while loop. this can be achieved by deleting all the remaining
		# statements in the loop body, which will automatically bring us back to check the 
		# condition (because there are no more statements to execute). However, along with 
		# deleting the remaining statements, set the condition to false, so that the loop will
		# exit
		# TODO: instead of passing in an empty array (very silly!) create a class made 
		# specifically for this. a sentient value
		# FIXME: also, create a copy of the statement first! this causes a bug when a break
		# stmt is made inside a function call, because now the body of the while loop
		# is gone for future calls to the function
		stmt.loop.body = Block([])
		stmt.loop.condition = expr.Literal(False)
	
	def visit_function_stmt(self, stmt):
		# literally just bind the function name to the function
		function = LoxFunction(stmt, self.__environment, False)
		self.__environment.define(stmt.name_token.lexeme, function)
	
	def visit_class_stmt(self, stmt):
		superclasses = []
		for i, superclass in enumerate(stmt.superclasses):
			superclass = self.evaluate(superclass)
			if not isinstance(superclass, LoxClass):
				# "superclass" now refers to the evaluated superclass, so we use indexing here
				raise RunTimeError(stmt.superclasses[i].token_name, "Superclass must be a class")
			superclasses.append(superclass)
		#if stmt.superclasses:
		#	superclass = self.evaluate(stmt.superclass)
		#	if not isinstance(superclass, LoxClass):
		#		raise RunTimeError(stmt.superclass.token_name, "Superclass must be a class")
		self.__environment.define(stmt.name_token.lexeme, None)
		if stmt.superclasses:
			self.__environment = Environment(self.__environment)
			# store the array of super classes, so that the superclasses can be searched for the
			# correct method when "super" is called according to the method resolution order,
			# which is just from left to right of the superclasses listed in the declaration
			self.__environment.define("super", superclasses)
		methods = {}
		# a LoxClass needs to store its superclass in order to have access to the methods and 
		# fields of the superclass
		klass = LoxClass(stmt.name_token.lexeme, methods, superclasses)
		for method in stmt.methods:
			function = LoxFunction(method, self.__environment, method.name_token.lexeme == "init")
			klass.methods[method.name_token.lexeme] = function
		for static_method in stmt.static_methods:
			function = LoxFunction(static_method, self.__environment, False)
			# NOTE: This is probably one of my favorite uses of object oriented programming I've 
			# done in a real project. Make LoxClass extend LoxInstance, and now we have access
			# to the .set() method of a LoxInstance. This means we can store all the static 
			# methods in this LoxClass as fields of an instance, which can also be accessed via 
			# a get-expression called on the LoxClass because the LoxClass is-a LoxInstance!
			klass.set(static_method.name_token.lexeme, function)
		if stmt.superclasses: self.__environment = self.__environment.outer
		self.__environment.assign(stmt.name_token, klass)

	def visit_super_expr(self, expr):
		distance, index = self.__locals.get(expr)
		superclasses = self.__environment.get_at(distance, index)
		# distance - 1 contains 'this' and we know it was the first (and only) variable
		# declared in that environment, so we can safely access it with index 0.
		current_instance = self.__environment.get_at(distance - 1, 0)
		# this is just the run time representation (LoxFunction) of the delcaration.
		#method = superclass.find_method(expr.method_token.lexeme)
		method = None
		# search the super classes from the first declared to the last declared for the method
		# associated with this super call
		for superclass in superclasses:
			method = superclass.find_method(expr.method_token.lexeme)
			if method: break
		if method is None:
			raise RunTimeError(expr.method_token, f"Undefined property '{expr.method_token.lexeme}'.")
		# now we can actually bind it to the current instance, so that it can be called
		return method.bind(current_instance)

	def visit_get_expr(self, expr):
		# when evaluate is called and object_instance is passed into it, it will return 
		# the actual LoxInstance object, because that is the value contained by the expression
		object_instance = self.evaluate(expr.object_instance)
		if isinstance(object_instance, LoxInstance): return object_instance.get(expr.name_token)
		else: raise RunTimeError(expr.name_token, "Only instances have properties")
	def visit_set_expr(self, expr):
		object_instance = self.evaluate(expr.object_instance)
		if not isinstance(object_instance, LoxInstance):
			raise RunTimeError(expr.name_token, "Only instances have fields")
		value = self.evaluate(expr.value)
		object_instance.set(expr.name_token.lexeme, value)
		return value
	def visit_return_stmt(self, stmt):
		value = stmt.value
		if value != None: value = self.evaluate(value)
		# now this can be caught in the call() method, so that the python call stack can 
		# "unwind" out of the function call, and after catching the Return "error", 
		# we return the value associated with it
		raise Return(value)

	def visit_array_expr(self, expr):
		# actually evaluate the elements
		elements = [self.evaluate(element) for element in expr.elements]
		# get rid of the decimal place on numbers with no decimal
		elements = [int(x) if type(x) == float and x % 1 == 0 else x for x in elements]
		return ArrayInstance(elements)
	def visit_subscriptget_expr(self, expr):
		array_instance = self.evaluate(expr.array_instance)
		index = self.evaluate(expr.index)
		# this mod operation is safe because if index is not a float, then the or will short 
		# circuit so the mod operation is never executed
		if type(index) != float or index % 1 != 0: 
			raise RunTimeError(expr.bracket, "Array index access must be a non negative integer")
		index = int(index)
		if index >= len(array_instance.array) or index < 0:
			raise RunTimeError(expr.bracket, "Array index out of range")
		if isinstance(array_instance, ArrayInstance): return array_instance.array[index]
		else: raise RunTimeError(expr.bracket, "Only arrays can be subscripted")
	def visit_subscriptset_expr(self, expr):
		array_instance = self.evaluate(expr.array_instance)
		index = self.evaluate(expr.index)
		value = self.evaluate(expr.value)
		if type(index) != float or index % 1 != 0: 
			raise RunTimeError(expr.bracket, "Array index access must be a non negative integer")
		index = int(index)
		if index >= len(array_instance.array) or index < 0:
			raise RunTimeError(expr.bracket, "Array index out of range")
		if isinstance(array_instance, ArrayInstance): 
			array_instance.array[index] = value
			return value
		else: raise RunTimeError(expr.bracket, "Only arrays can be subscripted")

	# this is the leaf of the expression tree, i.e the base case for recursion
	def visit_literal_expr(self, expr) -> any:
		return expr.value

	def visit_variable_expr(self, expr) -> any:
		# get the resolved variable from the environments linked list using the 
		# locals dictionary to know the depth of the correct environment associated with
		# this variable expression
		return self.__look_up_variable(expr.token_name, expr)
	def visit_this_expr(self, expr):
		return self.__look_up_variable(expr.keyword_token, expr)
	def __look_up_variable(self, name, expr):
		# if the variable is not in the look up table, it wasn't resolved, meaning it is just 
		# a global variable
		pair = self.__locals.get(expr)
		# pair corresponds to (hops, index), where index is the index of the value in the
		# values array of the environment
		if pair is not None: return self.__environment.get_at(pair[0], pair[1])
		else: return self.globals.get(name)

	def visit_assign_expr(self, expr) -> any:
		value = self.evaluate(expr.value)
		pair = self.__locals.get(expr)
		if pair is not None: self.__environment.assign_at(pair[0], pair[1], value)
		else: self.globals.assign(expr.token_name, value)
		# assignment is an expression, so it should return a value
		return value
	# the next simplest tree to evaluate is grouping, simply return the expression
	def visit_grouping_expr(self, expr) -> any:
		return self.evaluate(expr.expression)

	def visit_unary_expr(self, expr) -> any:
		# could either be '-' or '!'
		operand = self.evaluate(expr.expression)
		operator = expr.operator_token.token_type
		def minus():
			self.__check_number_operand(operator, operand)
			return -float(operand)
		switcher = {
			'MINUS' : minus,
			'BANG'  : lambda: not self.__is_truthy
		}
		return switcher.get(operator, lambda: None)()

	def visit_logic_expr(self, expr):
		left_operand = self.evaluate(expr.left_expr)
		if expr.operator_token.token_type == "OR":
			if self.__is_truthy(left_operand): return left_operand
		else: # the operator is AND
			if not self.__is_truthy(left_operand): return left_operand
		# if the method hasn't returned yet, then we have to evaluate the right_expr
		return self.evaluate(expr.right_expr)

	def visit_call_expr(self, expr):
		# a call has a callee expression, paren token, and an arguments list of expressions
		# if the callee is actually a function call, this will return a LoxFunction object,
		# so there is no need for casting, and it has a .call() method
		# callee_expr is an identifier, so it will be looked up in the environment 
		# just as any other variable. When evaluate() is called on an identifier expression, 
		# the value is returned from the environment. In this case, the value is a callable 
		# object, which has arity() and call() methods. The definition of this identifier
		# with the callable object is done in the visit method for function declaration
		callee = self.evaluate(expr.callee_expr)
		arguments = []
		for argument in expr.arguments:
			arguments.append(self.evaluate(argument))
		# check to make sure callee is a Callable
		if not isinstance(callee, Callable):
			raise RunTimeError(expr.paren_token, "Can only call functions and classes")
		if len(arguments) != callee.arity():
			raise RunTimeError(expr.paren_token, f"Expected {callee.arity()} arguments but got {len(arguments)}.")

		return callee.call(self, arguments)
	def visit_binary_expr(self, expr):
		# note: this choice of evaluating left first is not arbitrary
		left_operand = self.evaluate(expr.left_expr)
		right_operand = self.evaluate(expr.right_expr)
		operator = expr.operator_token
		def plus():
			# in order to assign variables in a closure declared outside the closure's scope,
			# you need to declare it as "nonlocal" in python.
			nonlocal right_operand
			nonlocal left_operand
			# check types (with support for implicit type casting on the '+' operator :( )
			if ((type(right_operand) == type(left_operand) == str) ^ # '^' is xor operator
				(type(left_operand) == type(right_operand) == float)):
				return left_operand + right_operand
			# add support for adding a string with a different type (like JS)
			elif type(left_operand) == str or type(right_operand) == str:
				# if its a number 
				if str(left_operand).endswith(".0"):
					left_operand = int(left_operand)
				if str(right_operand).endswith(".0"):
					right_operand = int(right_operand)
				# now check for Boolean values
				if type(left_operand) == bool: left_operand = str(left_operand).lower()
				if type(right_operand) == bool: right_operand = str(right_operand).lower()
				# now check for nil value
				if left_operand is None: left_operand = "nil"
				if right_operand is None: right_operand = "nil"
				return str(left_operand) + str(right_operand)
			raise RunTimeError(operator, "Operands must be two numbers or two strings")
		def minus():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand - right_operand
		def star():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand * right_operand
		def slash():
			if right_operand == 0: raise RunTimeError(operator, "Divide by zero error")
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand / right_operand
		def greater():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand > right_operand
		def greater_equal():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand >= right_operand
		def less():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand < right_operand
		def less_equal():
			self.__check_number_operand(operator, left_operand, right_operand)
			return left_operand <= right_operand
		def comma():
			# simply discard the left expression, (which is alread evaluated) and 
			# return the right expression
			return right_operand
		# don't need to check types for equality, because you should be able to test if any
		# object are equal to eachother, not just objects of the same type
		def is_equal(a, b):
			# nil is only equal to nil
			return True if a == b == None else a == b
		switcher = {
			'MINUS'         : minus,
			'STAR'          : star,
			'SLASH'         : slash,
			'PLUS'          : plus,
			'GREATER'       : greater,
			'GREATER_EQUAL' : greater_equal,
			'LESS'          : less,
			'LESS_EQUAL'    : less_equal,
			'COMMA'         : comma,
			'EQUAL_EQUAL'   : lambda: is_equal(left_operand, right_operand),
			'BANG_EQUAL'    : lambda: not is_equal(left_operand, right_operand)
		}
		return switcher.get(operator.token_type, lambda: None)()

	def visit_ternary_expr(self, expr):
		condition = self.evaluate(expr.condition)
		true_part = self.evaluate(expr.true_part)
		false_part = self.evaluate(expr.false_part)
		return true_part if self.__is_truthy(condition) else false_part

	def visit_anonymous_expr(self, expr):
		return LoxFunction(expr, self.__environment, False)

	def __is_truthy(self, operand):
		if operand is None: return False
		if type(operand) == bool: return operand
		return True

	def __check_number_operand(self, operator, left_operand, right_operand=None):
		if right_operand is None:
			if type(left_operand) == float: return
			else: raise RunTimeError(operator, "Operand must be a number")
		else:
			if type(left_operand) == type(right_operand) == float: return
			raise RunTimeError(operator, "Operands must be numbers")

class RunTimeError(TypeError):
	def __init__(self, token, message):
		self.message = message
		self.token = token
