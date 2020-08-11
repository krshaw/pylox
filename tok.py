class Token:
	# args: token_type: string, lexeme: string, literal: Any, line: int
	def __init__(self, token_type, lexeme, literal, line):
		self.token_type = token_type
		self.lexeme = lexeme
		self.literal = literal
		self.line = line
	def __str__(self):
		return f"{self.token_type} {self.lexeme} {self.literal}"
