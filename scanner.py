from tok import Token
import lox

class Scanner:
	# here the alphabet of the grammar are the characters of source code, and the scanner
	# decides which tokens (strings) are in the grammar
	def __init__(self, source, lox):
		self.lox = lox
		# actual source code in a string
		self.__source = source
		# list of Tokens created by scanning the source code
		self.__tokens = []
		# start and current indicate where in the file we are are. start is the first character
		# of the current lexeme being scanned, and current is the character currently being 
		# considered
		self.__start = 0
		self.__current = 0
		# where in the file we are. useful for reporting errors
		self.__line = 1
		# dictionary of keywords to be used when scanning potential identifiers
		self.__keywords = {}
		self.__keywords["and"] = "AND"
		self.__keywords["class"] = "CLASS"
		self.__keywords["else"] = "ELSE"
		self.__keywords["false"] = "FALSE"
		self.__keywords["for"] = "FOR"
		self.__keywords["fun"] = "FUN"
		self.__keywords["if"] = "IF"
		self.__keywords["nil"] = "NIL"
		self.__keywords["or"] = "OR"
		self.__keywords["print"] = "PRINT"
		self.__keywords["return"] = "RETURN"
		self.__keywords["this"] = "THIS"
		self.__keywords["true"] = "TRUE"
		self.__keywords["var"] = "VAR"
		self.__keywords["while"] = "WHILE"
		self.__keywords["break"] = "BREAK"
		self.__keywords["super"] = "SUPER"
		

	def scan_tokens(self):
		while not self.__is_at_end():
			# at the beginning of the next lexeme (the "chunk" of characters we are going to scan)
			self.__start = self.__current
			# take the current lexeme (denoted by start variable), and create a Token 
			# corresponding to the lexeme, and add the Token to tokens
			self.__scan_token()
		# add the Token for EOF
		self.__tokens.append(Token("EOF", "", None, self.__line))
		return self.__tokens

	def __scan_token(self):
		c = self.__advance()
		# implement some "switch-case like" control flow. dont want a bunch of if else statements
		def comment():
			curr_line = self.__line
			# okay to have opening >= closing, but not okay for closing > opening
			while not (self.__peek() == '*' and self.__peek_next() == '/') and not self.__is_at_end():
				if self.__peek() == '\n': self.__line += 1
				self.__advance()
			if self.__is_at_end(): 
				self.lox.error("Unterminated multi-line comment", curr_line)
				return
			# consume the "*/"
			self.__advance()
			self.__advance()
		def slash():
			if self.__match('/'):
				# keep consuming until new line is reached
				while self.__peek() != '\n' and not self.__is_at_end(): self.__advance()
			elif self.__match('*'): comment()
			else: self.__add_token("SLASH")
		def string():
			curr_line = self.__line
			while self.__peek() != '"' and not self.__is_at_end():
				if self.__peek() == '\n': self.__line += 1
				self.__advance()
			if self.__is_at_end():
				# python processes lines weird, so when it reaches the end of a file,
				# a new line is added for some reason. thats what is seams like at least
				self.lox.error("Unterminated string", curr_line)
				return
			# the next character must be '"'
			self.__advance()
			value = self.__source[self.__start + 1: self.__current - 1]
			self.__add_token("STRING", value)
		def inc_line():
			self.__line += 1
		def nothing():
			return
		def unexpected_char():
			self.lox.error("Unexpected character", self.__line)
		switcher = {
			'(' : (lambda: self.__add_token("LEFT_PAREN")),
			')' : (lambda: self.__add_token("RIGHT_PAREN")),
			'{' : (lambda: self.__add_token("LEFT_BRACE")),
			'}' : (lambda: self.__add_token("RIGHT_BRACE")),
			'[' : (lambda: self.__add_token("LEFT_BRACKET")),
			']' : (lambda: self.__add_token("RIGHT_BRACKET")),
			',' : (lambda: self.__add_token("COMMA")),
			'.' : (lambda: self.__add_token("DOT")),
			'-' : (lambda: self.__add_token("MINUS")),
			'+' : (lambda: self.__add_token("PLUS")),
			'*' : (lambda: self.__add_token("STAR")),
			';' : (lambda: self.__add_token("SEMICOLON")),
			'?' : (lambda: self.__add_token("QUESTION")),
			':' : (lambda: self.__add_token("COLON")),
			# for these, we need to look at the second character as well
			'!' : (lambda: self.__add_token("BANG_EQUAL" if self.__match('=') else "BANG")),
			'=' : (lambda: self.__add_token("EQUAL_EQUAL" if self.__match('=') else "EQUAL")),
			'<' : (lambda: self.__add_token("LESS_EQUAL" if self.__match('=') else "LESS")),
			'>' : (lambda: self.__add_token("GREATER_EQUAL" if self.__match('=') else "GREATER")),
			# need special case for '/' character because of comments
			'/' : slash,
			# do nothing for white space (except for incrementing line on '\n')
			' ' : nothing,
			'\r': nothing,
			'\t': nothing,
			'\n': inc_line,
			# now for longer lexemes
			'"' : string
		}
		def number():
			while self.__peek().isdigit(): self.__advance()
			if self.__peek() == '.' and self.__peek_next().isdigit():
				self.__advance()
				while self.__peek().isdigit(): self.__advance()
			self.__add_token("NUMBER", float(self.__source[self.__start: self.__current]))
		def identifier():
			# keep going until space is encountered or EOF 
			# (an identifier doesn't always have to end with a ' ')
			while self.__peek().isalnum(): self.__advance()
			lexeme = self.__source[self.__start: self.__current]
			# if the text IS a keyword, then create a token as normal with the token type 
			# as the value to the key (where the key is the actual lexeme)
			# if the lexeme is not a keyword, it must be an identifier
			token_type = self.__keywords.get(lexeme)
			if token_type == None: token_type = "IDENTIFIER"
			self.__add_token(token_type)
		def default():
			if c.isdigit(): return number
			elif c.isalpha(): return identifier
			else: return unexpected_char
		# if c is a a key in switcher dictionary, then the value of the key (which is a function)
		# will be returned by get, and then called
		# if c is not a key in switcher, then the lambda function in the second argument 
		# is returned by get(). so then what happens is:
		# the lambda function is called 
		# (it needs to be a lambda function to simulate lazy evaluation. 
		# we dont want default() being called immediately). this results in default() executing. 
		# when default() is executed, it returns a function. that is what the second () is for. 
		# when the second () is used on the returned function from the default() call, 
		# the returned function is then executed. 
		switcher.get(c, lambda: default()())()

	# method that "consumes" the next character and returns the current character
	def __advance(self):
		self.__current += 1
		return self.__source[self.__current - 1]
	def __is_at_end(self):
		return self.__current >= len(self.__source)

	# match() is like a conditional advance()
	def __match(self, expected):
		if self.__is_at_end(): return False
		#check for character at the current index, which is the "next" character after c
		if self.__source[self.__current] != expected: return False
		# if it is a match, "consume" the next character and return true
		self.__current += 1
		return True

	# like advance(), but not actually consuming the character, only returning it. 
	# called "look ahead"
	def __peek(self):
		if self.__is_at_end(): return '\0'
		return self.__source[self.__current]
	def __peek_next(self):
		if self.__current + 1 >= len(self.__source): return '\0'
		return self.__source[self.__current + 1]

	# given an token_type and literal, create a token from the current lexeme and 
	# add it to self.__tokens. this method is only for one or two character lexemes
	def __add_token(self, token_type, literal=None):
		lexeme = self.__source[self.__start:self.__current]
		self.__tokens.append(Token(token_type, lexeme, literal, self.__line))
