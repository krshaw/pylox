import sys
import scanner
import tok
import parser
import resolver
import interpreter
from ast_printer import ASTPrinter

class Lox:
	source_interpreter = None
	#had_error = False
	had_run_time_error = False
	is_REPL = False
	def __init__(self):
		self.had_error = False
	def run_file(self, source):
		Lox.source_interpreter = interpreter.Interpreter(Lox.is_REPL, self)
		# load file into string, pass it into run() method
		with open(source, "r") as f:
			# load file in as a string
			source_code = f.read()
			self.run(source_code)
			if self.had_error: sys.exit(65)
			if self.had_run_time_error: sys.exit(70)

	def runPrompt(self):
		Lox.is_REPL = True
		Lox.source_interpreter = interpreter.Interpreter(Lox.is_REPL, self)
		while True:
			self.run(input("> "))
			# should be reset after every command, so that prompt can continue running
			Lox.had_error = False

	def run(self, source):
		source_scanner = scanner.Scanner(source, self)
		tokens = source_scanner.scan_tokens()
		source_parser = parser.Parser(tokens, Lox.is_REPL, self)
		statements = source_parser.parse()
		if statements is None: self.had_error = True
		# stop if there was a syntax error
		if self.had_error: return
		source_resolver = resolver.Resolver(Lox.source_interpreter, self)
		source_resolver.resolve(statements)
		source_resolver.check_unused_variables()
		if self.had_error: return
		# else, just print out the resulting expresssion
		Lox.source_interpreter.interpret(statements)

	# error is of type RunTimeError and has fields 'message' and 'token'
	#@classmethod
	def run_time_error(self, error):
		print(f"{error.message} \n[line {error.token.line}]")
		self.had_run_time_error = True
		
	#@classmethod
	def error(self, message, line=None, token=None):
		if token is not None:
			if token.token_type == "EOF": 
				self.report(token.line, " at end", message)
			else:
				self.report(token.line, f" at '{token.lexeme}'", message)
		else:
			self.report(line, "",  message)
	
	def report(self, line, where, message):
		print(f"[Line {line}] Error{where}: {message}")
		self.had_error = True
	
if __name__ == "__main__":
	lox = Lox()
	if len(sys.argv) == 2:
		lox.run_file(sys.argv[1])
	elif len(sys.argv) > 1:
		print("Usage: python3 lox.py [script]")
		# exit code 64 when command used incorrectly, accoding to UNIX standards 
		sys.exit(64)
	else:
		print("running interpreter")
		lox.runPrompt()
