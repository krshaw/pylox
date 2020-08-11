from tok import Token
from expr import *
from stmt import *
import lox
class Parser:
	# stack to keep track of while loops for break statements
	while_stmt_stack = []
	# recall: the parser takes a set of tokens (expression), and decides if expression is 
	# in the grammer. So a "string" in this grammar is an expression, and a "letter" is a token
	def __init__(self, tokens, is_REPL, lox):
		self.lox = lox
		self.__tokens = tokens
		self.__is_REPL = is_REPL
		# "current points to the next token awaiting to be used"
		self.__current = 0
	
	# method to actually start the parse
	# parse() -> Stmt[]:
	def parse(self):
		# each statement might be composed of some expressions ('has a' relationship)
		# so then each expression inside the statements is represented by the expression
		# syntax trees, and the statements have their own trees (which will be executed in 
		# interpreter.py)
		statements = []
		while not self.__is_at_end():
			stmt = self.__declaration()
			statements.append(stmt)
		return statements
	
	def __declaration(self): 
		try:
			# interesting note: declaration statements are the only ones that actually contain
			# tokens as a fields in their AST nodes
			if self.__match("VAR"): return self.__var_declaration()
			if self.__match("FUN"): return self.__fun_declaration("function")
			if self.__match("CLASS"): return self.__class_declaration()
			else: return self.__statement()
		except ParseError:
			# "get out" of current statement and go onto the next one, to continue parsing
			self.__synchronize()
			return Stmt()
	
	def __class_declaration(self):
		name = self.__consume("IDENTIFIER", "Expect class name")
		superclasses = []
		if self.__match("LESS"):
			superclass_name = self.__consume("IDENTIFIER", "Expect super class name")
			superclasses.append(Variable(superclass_name))
			# support for multiple inheritance, which has the same semantics as python
			while self.__match("COMMA"):
				superclass_name = self.__consume("IDENTIFIER", "Expect super class name")
				superclasses.append(Variable(superclass_name))
		self.__consume("LEFT_BRACE", "Expect opening brace after class name")
		methods = []
		static_methods = []
		while not self.__check("RIGHT_BRACE") and not self.__is_at_end():
			if self.__match("CLASS"): 
				static_methods.append(self.__fun_declaration("static method"))
			else: 
				methods.append(self.__fun_declaration("method"))
		self.__consume("RIGHT_BRACE", "Expect closing brace after class declaration")
		return Class(name, methods, static_methods, superclasses)

	def __fun_declaration(self, kind):
		#name = self.__consume("IDENTIFIER", f"Expect {kind} name")
		name = ""
		if self.__check("IDENTIFIER"): name = self.__consume("IDENTIFIER", "blah blah blah")
		function = self.__anonymous_function(kind)
		#return Function(name, function.param_tokens, function.body)
		return Function(name, function.param_tokens, function.body) if name else function
	
	def __var_declaration(self):
		# the VAR token is already consumed, so get the variable name (which is an identifier)
		name = self.__consume("IDENTIFIER", "Expect variable name")
		initial_expr = None
		if self.__match("EQUAL"): initial_expr = self.__expression()
		self.__consume("SEMICOLON", "Expect ';' after variable declaration")
		# just leaf node essentially, used to hold the variable name and value
		# name is a token representing the lexeme of the identifier
		return Var(name, initial_expr)

	# this is how each statement in the program is parsed
	def __statement(self):
		# if it is a print statement
		if self.__match("PRINT"): 
			return self.__print_stmt()
		# if it is a block statement
		if self.__match("LEFT_BRACE"):
			return Block(self.__block())
		if self.__match("IF"):
			return self.__if_stmt()
		if self.__match("WHILE"):
			return self.__while_stmt()
		if self.__match("FOR"):
			return self.__for_stmt()
		if self.__match("BREAK"):
			return self.__break_stmt()
		if self.__match("RETURN"):
			return self.__return_stmt()
		return self.__expression_stmt()

	# __return_stmt(self) -> Return(Stmt)
	def __return_stmt(self):
		keyword = self.__previous()
		value = None
		if not self.__check("SEMICOLON"):
			value = self.__expression()
		self.__consume("SEMICOLON", "Expect ';' after return statement")
		return Return(keyword, value)

	# __for_stmt(self) -> Block(Stmt)
	# a for loop is just syntactic sugar for a block wrapped around a while loop
	def __for_stmt(self):
		while_loop = While(Expr(), Stmt())
		Parser.while_stmt_stack.append(while_loop)
		statements = []
		self.__consume("LEFT_PAREN", "Expect '(' after for statement")
		# initializer is either a varDecl, exprStmt, or semicolon
		initializer = None
		if self.__match("VAR"): initializer = self.__var_declaration()
		# if there is no initializer, just set it to be a generic Stmt
		elif self.__match("SEMICOLON"): initializer = Stmt()
		# else, the initializer must be an expression statement (or an error, which the call 
		# to expression_stmt() should catch)
		else: initializer = self.__expression_stmt()
		# should be the very first statement executed in the block statement to be returned
		statements.append(initializer)
		# the condition should just be an expression, followed by a semicolon
		# there doesn't necessarily need to be a condition, in which case it can just be "true"
		condition = None
		if self.__match("SEMICOLON"): condition = Literal(True)
		else: # else, the condition must be an expression followed by a semicolon
			condition = self.__expression()
			self.__consume("SEMICOLON", "Expect ';' after for loop condition")
		increment = None
		# if there is no increment, then it can just be a generic Expr
		if self.__match("RIGHT_PAREN"): increment = Expr()
		else: 
			increment = self.__expression()
			self.__consume("RIGHT_PAREN", "Expect ')' after increment clause in for loop")
		# now we have all the clauses, its time to get the body of the for loop
		body = self.__statement()
		# fill in the fields of the while loop
		while_loop.condition = condition
		while_loop.body = Block([body, Expression(increment)])
		statements.append(while_loop)
		return Block(statements)
	
	# __while_stmt(self) -> While(Stmt)
	def __while_stmt(self):
		while_loop = While(Expr(), Stmt())
		Parser.while_stmt_stack.append(while_loop)
		# already consumed "while", so the next token should be a left paren
		self.__consume("LEFT_PAREN", "Expect '(' after while statement")
		condition = self.__expression()
		self.__consume("RIGHT_PAREN", "Expect ')' after condition for while loop")
		body = self.__statement()
		while_loop.condition = condition
		while_loop.body = body
		return while_loop
	# __break_stmt(self) -> Break(Stmt)
	def __break_stmt(self):
		break_token = self.__previous()
		self.__consume("SEMICOLON", "Expect ';' after break statement")
		if not Parser.while_stmt_stack:
			raise self.__error(break_token, "Break statement outside while loop")
		while_stmt = Parser.while_stmt_stack.pop()
		return Break(while_stmt)
	# __if_stmt(self) -> If(Stmt)
	def __if_stmt(self):
		# already consumed "if", so the next token should be the condition expression
		self.__consume("LEFT_PAREN", "Expect '(' after if statement")
		condition = self.__expression()
		self.__consume("RIGHT_PAREN", "Expect ')' after condition for if statement")
		# now the true part should just be a statement
		true_part = self.__statement()
		false_part = None
		if self.__match("ELSE"):
			false_part = self.__statement()
		return If(condition, true_part, false_part)
	# __block() -> stmt[]
	def __block(self):
		statements = []
		while not self.__check("RIGHT_BRACE") and not self.__is_at_end():
			statements.append(self.__declaration())
		self.__consume("RIGHT_BRACE", "Expect '}' after block")
		return statements
	# __print_stmt() -> Stmt
	def __print_stmt(self):
		value = self.__expression()
		self.__consume('SEMICOLON', "Expect ';' after value")
		return Print(value)

	# __expression_stmt() -> Stmt | Expr
	def __expression_stmt(self):
		value = self.__expression()
		# so that we can evaluate expressions in the REPL without making a print statement
		if self.__is_REPL:
			# this logic can, and should, be refactored. it is redundant.
			if self.__match("SEMICOLON"): return Expression(value)
			else: return value
		else:
			self.__consume("SEMICOLON", "Expect ';' after value")
		return Expression(value)

	# __expression() -> Expr:
	def __expression(self):
		return self.__assignment()

	def __anonymous_function(self, kind):
		self.__consume("LEFT_PAREN", "Expect '(' after function expression")
		params = []
		if not self.__check("RIGHT_PAREN"):
			params.append(self.__consume("IDENTIFIER", "Expect parameter name"))
			while self.__match("COMMA"):
				if len(params) >= 255:
					self.__error(self.__peek(), "Cannot have more than 255 parameters")
				params.append(self.__consume("IDENTIFIER", "Expect parameter name"))
		self.__consume("RIGHT_PAREN", "Expect ')' after parameters")
		self.__consume("LEFT_BRACE", f"Expect '{{' before {kind} body")
		body = self.__block()
		return Anonymous(params, body)

	# __assignment() -> Expr
	def __assignment(self):
		# simply evaluate the next expression
		expr = self.__comma()
		if self.__match("EQUAL"):
			equals_token = self.__previous()
			# right associative, so we can use recursion to "build up" the right hand side
			value = self.__assignment()
			# check to make sure the left hand expression (l-value) is a variable
			if isinstance(expr, Variable):
				# expr was previously a r-value node, but now we are representing it as an l-value
				name = expr.token_name
				return Assign(name, value)
			elif isinstance(expr, Get):
				return Set(expr.object_instance, expr.name_token, value)
			elif isinstance(expr, SubscriptGet):
				return SubscriptSet(expr.array_instance, expr.index, value, expr.bracket)
			else: self.__error(equals_token, "Invalid assignment target")
		return expr

	def __comma(self):
		if self.__match("FUN"): return self.__anonymous_function("function")
		return self.__bin_op_expr(self.__ternary, "COMMA")
	
	# __ternary() -> Expr
	def __ternary(self):
		expr = self.__or()
		if self.__match("QUESTION"):
			true_part = self.__or()
			self.__consume("COLON", "Expect ':' after '?' for ternary operator")
			false_part = self.__ternary()
			expr = Ternary(expr, true_part, false_part)
		return expr
	
	# __or() -> Expr
	def __or(self):
		return self.__logical("OR", self.__and)
	def __and(self):
		return self.__logical("AND", self.__equality)
	# helper to refactor logical operator parsing
	# __logical(operator: str, higher_presedence: () => Expr): Logic
	def __logical(self, operator, higher_presedence):
		expr = higher_presedence()
		if self.__match(operator):
			operator_token = self.__previous()
			right_expr = higher_presedence()
			expr = Logic(expr, operator_token, right_expr)
		return expr
	# matches an eqaulity operator or anything of higher presedence
	# __equality() -> Expr:
	def __equality(self):
		return self.__bin_op_expr(self.__comparison, "EQUAL_EQUAL", "BANG_EQUAL")

	# __comparison(self) -> Expr
	def __comparison(self):
		return (self.__bin_op_expr(self.__addition, 
								  "GREATER", "LESS", "GREATER_EQUAL", "LESS_EQUAL"))

	# __addition() -> Expr
	def __addition(self):
		return self.__bin_op_expr(self.__multiplication, "PLUS", "MINUS")

	# __multiplication() -> Expr
	def __multiplication(self):
		return self.__bin_op_expr(self.__unary, "STAR", "SLASH")

	# __bin_op_expr(higher_presedence: Expr -> Expr, token_types[str]) -> Expr
	def __bin_op_expr(self, higher_presedence, *token_types):
		#left sub expression in nonterminal body
		expr = higher_presedence()
		while self.__match(token_types):
			# get the previous token, which is whatever token matched the binary operator
			operator_token = self.__previous()
			# now get the right hand expression (works because we've already consumed the 
			# operator token, so the current index is at the token of right hand subexpression
			right_expr = higher_presedence()
			# combine operator and expressions into a new Binary syntax tree now, then loop around
			# to make left associativity (works because we make expr the left operand)
			expr = Binary(expr, operator_token, right_expr)
		return expr

	# __unary() -> Expr
	def __unary(self):
		if self.__match("BANG", "MINUS"):
			operator_token = self.__previous()
			right = self.__unary()
			return Unary(operator_token, right)
		return self.__call()

	# __call() -> Expr
	def __call(self):
		expr = self.__primary()
		# this must be a while loop because we can have curried functions like fn(1)(2)(3)
		while True:
			if self.__match("LEFT_PAREN"): expr = self.__finish_call(expr)
			elif self.__match("DOT"): 
				name = self.__consume("IDENTIFIER", "Expect property name after '.'")
				expr = Get(expr, name)
			elif self.__match("LEFT_BRACKET"):
				bracket = self.__previous()
				index = self.__expression()
				self.__consume("RIGHT_BRACKET", "Expect ']' after array index access")
				expr = SubscriptGet(expr, index, bracket)
			else: break
		return expr

	# __finish_call(expr: Expr) -> Expr
	def __finish_call(self, expr):
		arguments = []
		# if there are arguments
		if not self.__check("RIGHT_PAREN"):
			# calling self.__expression can result in the comma operator being called, 
			# meaning a binary operator expression is stored rather than just the arguments
			argument_tree = self.__expression()
			# very hacky, but we need to traverse the tree and store the nodes in an array.
			# this is so that the arguments list can actually be filled rather than just have
			# a comma binary operator as its only item (which would happen if we just looped 
			# until a comma isnt reached, and kept appending self.__expression())
			self.__fill(arguments, argument_tree)
			if len(arguments) >= 255:
				self.__error(self.__peek(), "Cannot have more than 255 arguments")
		# and now consume the closing paren, either after breaking, or just for thunk call
		paren_token = self.__consume("RIGHT_PAREN", "Expect ')' after function call")
		return Call(expr, paren_token, arguments)

	# __fill(arguments: Expr[], node: Expr) -> None
	def __fill(self, values, node):
		# if the node is not a comma operator, then it is a value, 
		# so append it to the values list
		if not (isinstance(node, Binary) and node.operator_token.token_type == "COMMA"):
			values.append(node)
		# else, append the left node first, and the right node second
		else:
			self.__fill(values, node.left_expr)
			self.__fill(values, node.right_expr)

	# comma operator: pack a series of expressions where only one is expected
	# __primary() -> Expr
	def __primary(self):
		if self.__match("FALSE"): return Literal(False)
		if self.__match("TRUE"): return Literal(True)
		if self.__match("NIL"): return Literal(None)
		# need to get the literal of previous, because match will call advance()
		if self.__match("NUMBER", "STRING"): return Literal(self.__previous().literal)
		if self.__match("SUPER"):
			keyword = self.__previous()
			self.__consume("DOT", "Expect '.' after 'super'")
			method = self.__consume("IDENTIFIER", "Expect superclass method name")
			return Super(keyword, method)
		if self.__match("LEFT_BRACKET"):
			elements = []
			if not self.__check("RIGHT_BRACKET"):
				# same idea as in finish_call method
				element_tree = self.__expression()
				self.__fill(elements, element_tree)
			bracket_token = self.__consume("RIGHT_BRACKET", "Expect ']' after array declaration")
			return Array(bracket_token, elements)
		# need to check for syntax errors on '(', so it is more complicated
		if self.__match("LEFT_PAREN"):
			# get the expression directly after opening paren
			expr = self.__expression()
			# after that expression, the next token MUST be a closing paren
			self.__consume("RIGHT_PAREN", "Expect ')' after expression.")
			return Grouping(expr)
		if self.__match("THIS"): return This(self.__previous())
		if self.__match("IDENTIFIER"): return Variable(self.__previous())
		# if the token doesn't match any of the production rules, then the current token
		# can't start an expression
		raise self.__error(self.__peek(), "Expect expression")

	# __match(token_types[str]) -> bool:
	def __match(self, *token_types):
		# in the case where token_types was passed in as a list from bin_op_expr
		if type(token_types[0]) == tuple:
			token_types = token_types[0]
		for token_type in token_types:
			# return true if the current token matches at least one of the types
			if (self.__check(token_type)):
				self.__advance()
				return True
		return False

	# check to see if the current token is the same kind as the argument
	# __check(token_type: str) -> bool:
	def __check(self, token_type):
		if self.__is_at_end(): return False
		return self.__peek().token_type == token_type
	# method to consume the next token, and return the current one
	# __advance() -> Token:
	def __advance(self):
		if not self.__is_at_end(): self.__current += 1
		return self.__previous()

	# __peek() -> Token:
	def __peek(self):
		return self.__tokens[self.__current]

	# __is_at_end() -> bool:
	def __is_at_end(self):
		return self.__peek().token_type == "EOF"

	# __previous() -> Token:
	def __previous(self):
		return self.__tokens[self.__current - 1]
	
	# like advance(), but check for syntax errors
	# __consume(token_type: str, message: str) -> Token
	def __consume(self, token_type, message):
		if self.__check(token_type): return self.__advance()
		raise self.__error(self.__peek(), message)
	# __error(token: Token, message: str) -> ParseError
	def __error(self, token, message):
		# this is being called as i want
		self.lox.error(message, None, token)
		# now the user knows of the error, but the parser must return a ParseError
		# the parser uses the ParseError exception as a "sentinal value" i.e. a value
		# whose existence notifies the parser of a certain condition
		return ParseError()

	# this will be called after catching a ParseError exception
	# __synchronize() -> None
	def __synchronize(self):
		self.__advance()
		while not self.__is_at_end():
			if self.__previous().token_type == "SEMICOLON": return 
			def nothing(): return
			# for now, just do nothing
			switcher =  {
				"CLASS": (nothing),
				"FUN": (nothing),
				"VAR": (nothing),
				"FOR": (nothing),
				"IF": (nothing),
				"WHILE": (nothing),
				"PRINT": (nothing),
				"RETURN": (nothing)
			}
			switcher.get(self.__previous().token_type, lambda: None)()
			self.__advance()
class ParseError(Exception):
	pass
