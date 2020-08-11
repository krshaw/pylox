from environment import Environment
from return_exception import Return
from lox_instance import *

class Callable():
	# the implementers job is to return the value that the call expression produces
	def call(self, interpreter, arguments): 
		pass
	def arity(self):
		pass
class LoxFunction(Callable):
	def __init__(self, declaration, closure, is_initializer):
		# declaration could either be a statement (a function delcaration) or 
		# it could be an expression (for anonymous expressions)
		self.declaration = declaration
		self.closure = closure
		self.__is_initializer = is_initializer
	def call(self, interpreter, arguments):
		# create a new environment that has its own scope, one chain down from the globals
		environment = Environment(self.closure)
		# this is where the parameters and arguments are binded together!
		# the actual value of the parameters are from the "arguments" parameter in the call 
		# function, and the names of the parameters come from the delcaration stmt object
		var_names = self.declaration.param_tokens
		# arguments are already evaluated (from the call visit method), so no need
		# to do anything with them (accept assigning them to the parameters)
		for var_name, value in zip(var_names, arguments):
			# the define method takes the variable token lexeme and value
			environment.define(var_name.lexeme, value)
		# now just execute the block (which has environment as its local scope, and now
		# all the parameters are binded to values
		try:
			interpreter.execute_block(self.declaration.body, environment)
		except Return as return_value:
			# if returning from the initializer (for control flow purposes), return the 
			# instance, naturally
			if self.__is_initializer: return self.closure.get_at(0, 0)
			return return_value.value
		if self.__is_initializer: 
			# the index of "this" variable should be 0 because it is the first variable 
			# initialized when a method is binded
			return self.closure.get_at(0, 0)
		return None
	def arity(self):
		return len(self.declaration.param_tokens)
	def bind(self, instance):
		environment = Environment(self.closure)
		environment.define("this", instance)
		return LoxFunction(self.declaration, environment, self.__is_initializer)
	def __str__(self):
		# need to check if declaration is a stmt or expr
		return f"<fn {self.declaration.name_token.lexeme} >"
class LoxClass(LoxInstance, Callable):
	def __init__(self, name, methods, superclasses):
		self.name = name
		self.methods = methods
		self.superclasses = superclasses
		# initialize the instance which will have the static methods as fields
		super().__init__(self)
	def __str__(self):
		return self.name
	def call(self, interpreter, arguments):
		instance = LoxInstance(self)
		initializer = self.find_method("init")
		# if the an initiaLier was found, simply give it access to the "this" keyword
		# and call the method
		if initializer:
			# the arguments passed into the call to create an instance are the arguments to the
			# constructor!
			initializer.bind(instance).call(interpreter, arguments)
		return instance
	def arity(self):
		initializer = self.find_method("init")
		if initializer: return initializer.arity()
		return 0
	def find_method(self, name):
		method = self.methods.get(name)
		# when multiple inheritance is implemented, we can simpy iterate through the 
		# superclasses until method is not None
		if not method and self.superclasses: 
			for superclass in self.superclasses:
				method = superclass.find_method(name)
				if method: break
		return method
