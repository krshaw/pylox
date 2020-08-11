import interpreter
import lox_callable
class LoxInstance():
	def __init__(self, klass):
		self.__klass = klass
		self.__fields = {}
	
	def __str__(self):
		return f"{self.__klass.name} instance"
	def get(self, name):
		if name.lexeme in self.__fields:
			return self.__fields[name.lexeme]
		# if the name was not found in the map of fields, then it must be a method on the class
		# of the instance
		method = self.__klass.find_method(name.lexeme)
		#*** MY THOUGHTS:
		# method is just an object of type LoxFunction, so it is callable, and is a value
		# here, we need to return a new LoxFunction, that has the method.declaration as the 
		# first argument, and as the second argument, create a new environment who's link
		# is the environment already associated with the method, and define "this" in the 
		# environment, where the value associated with "this" is simply the current instance,
		# then we have achieved our goal!
		# NOTE: These thoughts were pretty much correct :)
		if method: 
			# returns a new function who's closure is a new environment that has a link to
			# the previous function's closure, but this new closure has a "this" variable
			# defined in it, which evaluates to the current instance, which allows for
			# access to get and set expressions from the "this" keyword
			return method.bind(self)
		else: raise interpreter.RunTimeError(name, f"Undefined property {name.lexeme}.")
	def set(self, name, value):
		self.__fields[name] = value;
# basically just an instance, but with an actual array as a field as well
class ArrayInstance(LoxInstance):
	def __init__(self, array):
		# we are doing everything in the instance, so we don't really need an array class
		super().__init__(None)
		self.array = array
		class LengthMethod(lox_callable.Callable):
			def call(self, interpreter, arguments):
				return len(array)
			def arity(self): return 0
			def __str__(self): return "<list method length>";
		class AppendMethod(lox_callable.Callable):
			def call(self, interpreter, arguments):
				# expect one argument, the thing being appended
				appendee = arguments[0]
				if type(appendee) == float and appendee % 1 == 0: appendee = int(appendee)
				array.append(appendee)
			def arity(self): return 1
			def __str__(self): return "<list method append>"
		self.set("length", LengthMethod())
		self.set("append", AppendMethod())
	def __str__(self):
		return f"{self.array}"
