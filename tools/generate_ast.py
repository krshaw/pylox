import os
import sys

def main():
	if len(sys.argv) != 2:
		print("Usage: generate_ast <output directory>")
		sys.exit(64)
	output_dir = os.path.abspath(sys.argv[1])
	# class name: fields of class
	expr_classes = ["Binary   : left_expr, operator_token, right_expr",
					"Grouping : expression",
					"Literal  : value",
					"Unary    : operator_token, expression", 
					"Ternary  : condition, true_part, false_part",
					# simply a wrapper around the token for the variable name
					"Variable     : token_name",
					"Assign       : token_name, value",
					"Logic        : left_expr, operator_token, right_expr",
					"Call         : callee_expr, paren_token, arguments",
					"Anonymous    : param_tokens, body",
					"Get          : object_instance, name_token",
					"Set          : object_instance, name_token, value",
					"This         : keyword_token",
					"Super        : keyword_token, method_token",
					"Array        : bracket_token, elements",
					"SubscriptGet : array_instance, index, bracket",
					"SubscriptSet : array_instance, index, value, bracket"]
	stmt_classes = ["Expression : expression",
					"Print      : expression",
					"Var        : token_name, initial_expr",
					"Block      : statements",
					"If         : condition, true_branch, false_branch",
					"While      : condition, body",
					"Break      : loop",
					"Function   : name_token, param_tokens, body",
					"Return     : keyword, value",
					"Class      : name_token, methods, static_methods, superclasses"]
	define_ast(output_dir, "Expr", expr_classes)
	define_ast(output_dir, "Stmt", stmt_classes)

def define_ast(output_dir: str, base_name: str, classes: list) -> None:
	path = output_dir + '/' + base_name.lower() + '.py'
	with open(path, "w") as f:
		f.write(f"class {base_name}:\n")
		# define abstract accept() in the base class
		f.write("	def accept(self, visitor) -> any:\n")
		f.write("		pass\n")
		for sub_class in classes:
			class_name = sub_class.split(':')[0].strip()
			fields = sub_class.split(':')[1].strip()
			define_class(f, base_name, class_name, fields)

def define_visitor(f, base_name: str, classes: list) -> None:
	f.write("class Visitor:\n")
	for sub_class in classes:
		class_name = sub_class.split(':')[0].strip()
		f.write(f"	def visit_{class_name.lower()}_{base_name.lower()}(self, {base_name.lower()}) -> any:\n")
		f.write("		pass\n")

def define_class(f, base_name: str, class_name: str, fields: list):
	# declare class
	f.write(f"class {class_name}({base_name}):\n")
	# constructor
	f.write(f"	def __init__(self, {fields}):\n")
	# initialize fields in constructor
	for field in fields.split(', '):
		f.write(f"		self.{field} = {field}\n")
	# implement accept(visitor)
	f.write("	def accept(self, visitor) -> any:\n")
	f.write(f"		return visitor.visit_{class_name.lower()}_{base_name.lower()}(self)\n")

if __name__ == "__main__":
	main()
