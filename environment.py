import interpreter

class Environment:
	def __init__(self, outer=None):
		#keys will be strings (just the name of the variable token, not the token itself)
		#values will be any value the initial expression evaluates to
		self.values = {}
		#self.values = []
		if outer is not None:
			# if we are in a local scope, the value is going to be looked up via array access
			self.values = []
			#self.outer = outer
		#else:
			#self.outer = None
		self.outer = outer
	# !!! define takes the lexeme itself, assign and get take the variable token
	def define(self, name, value):
		# we are not checking if the variable is already initialized. this is on purpose
		# for the implementation of the lox language. according to the creator of lox, this 
		# is both inspired by Scheme, and just for simplicity
		# if we are in local scope, then we can just append the value to the array. 
		# This works because in the resolver, the indices are incremented only when variables
		# are declared, so we have a one-to-one correspondence between the array values here 
		# and the indices associated with variable declarations in the resolver
		if self.outer is not None: self.values.append(value)
		else: self.values[name] = value

	def assign(self, name, value):
		# if name (the token) is in the environment, then the variable is not yet initialized, 
		# but now the user is assigning it a value
		# recursive calls are redundant because we know for a fact that assign() is only called
		# when the assignment is made at the global level, so there is no need to search 
		if name.lexeme in self.values: self.values[name.lexeme] = value
		#elif self.outer is not None: self.outer.assign(name, value)
		else: raise interpreter.RunTimeError(name, f"Undefined variable '{name.lexeme}'.")
	def assign_at(self, hops, index, value):
		scope = self.__ancestor(hops).values
		# we don't need to worry about the variable not being defined, because if it wasn't
		# defined, then the resolver wouldn't call resolve() on the interpreter for this
		# assignment, meaning the interpreter would just call assign(), thinking we have a 
		# global variable. then, the error will be caught in assign().
		scope[index] = value 

	# get(name: Token) -> any
	def get(self, name):
		if name.lexeme in self.values: 
			# if the value is an empty array (which is impossible in lox), then the variable 
			# is not yet initialized 
			if self.values[name.lexeme] == []:
				raise interpreter.RunTimeError(name, f"Can't access uninitialized variable '{name.lexeme}'")
			else: return self.values[name.lexeme]
		# recursively traverse the linked list
		if self.outer is not None: return self.outer.get(name)
		raise interpreter.RunTimeError(name, f"Undefined variable '{name.lexeme}' .")

	# get(name: Token) -> any
	def get_at(self, hops, index): # TODO: get rid of name parameter in get_at()
		#return self.__ancestor(hops).get(name)
		return self.__ancestor(hops).values[index]
	def __ancestor(self, hops):
		environment = self
		for i in range(hops):
			environment = environment.outer
		return environment
