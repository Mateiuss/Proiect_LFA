from sys import argv
from .Lexer import Lexer

class Node:
	def __init__(self, type, value, parent=None):
		self.type = type
		self.value = value
		self.parent = parent
		self.children = []

	def deep_copy(self):
		new_node = Node(self.type, self.value, self.parent)
		new_node.children = [child.deep_copy() for child in self.children]
		return new_node

	def add_child(self, child):
		self.children.append(child)

	def top_child(self):
		return self.children[-1]

class Parser:
	def __init__(self, token_list):
		self.token_list = token_list

	def sum(self, node):
		s = 0
		for child in node.children:
			if child.type == "NAT":
				s += int(child.value)
			elif child.type == "LIST":
				s += self.sum(child)

		return s
	
	def concat(self, node):
		concat_list = []

		for child in node.children:
			if child.type == "LIST":
				concat_list += child.children
			elif child.type == "NAT":
				concat_list.append(child)

		node.children = concat_list

	def replace_id(self, expr, id, value):
		if expr.type == "ID" and expr.value == id:
			value = value.deep_copy()

			expr.type = value.type
			expr.value = value.value
			expr.children = value.children
			for child in value.children:
				child.parent = expr
		elif expr.type == "LIST" or expr.type == "FUNCTION":
			for child in expr.children:
				self.replace_id(child, id, value)
		elif expr.type == "LAMBDA":
			if expr.children[0].value == id:
				return
			self.replace_id(expr.children[1], id, value)
	
	def parse(self):
		self.root = Node("ROOT", None)
		curr_node = self.root

		jump = 0
		num_paranthesis = 0
		last_func = []
		for token in self.token_list:
			match token[0]:
				case "NAT" | "ID" | "EMPTY_LIST":
					curr_node.add_child(Node(token[0], token[1], curr_node))
				case "FUNCTION":
					curr_node.add_child(Node("FUNCTION", token[1], curr_node))
					curr_node = curr_node.top_child()
					jump += 1
					last_func.append(num_paranthesis)
				case "LAMBDA":
					curr_node.add_child(Node("LAMBDA", token[1], curr_node))
					curr_node = curr_node.top_child()
				case "LAMBDA_SEPARATOR":
					continue
				case "LEFT_PARENTHESIS":
					curr_node.add_child(Node("LIST", token[1], curr_node))
					curr_node = curr_node.top_child()
					num_paranthesis += 1
				case "RIGHT_PARENTHESIS":
					while curr_node.type == "LAMBDA" and len(curr_node.children) == 2:
						curr_node = curr_node.parent

					curr_node = curr_node.parent
					num_paranthesis -= 1

					if jump > 0:
						tmp = last_func.pop()

					if jump > 0 and num_paranthesis == tmp:
						curr_node = curr_node.parent
						jump -= 1
					elif jump > 0:
						last_func.append(tmp)

	def reverse_lambda_replacement(self, node):
		if node.type == "LAMBDA":
			if len(node.children) < 3:
				self.reverse_lambda_replacement(node.children[1])
				return

			move_node = node
			while move_node.children[1].type == "LAMBDA":
				self.reverse_lambda_replacement(move_node.children[2])
				move_node = move_node.children[1]

			self.reverse_lambda_replacement(move_node.children[2])

			node_copy = node
			while node_copy != move_node and node_copy.parent != move_node:
				node_copy.children[2], move_node.children[2] = move_node.children[2], node_copy.children[2]
				node_copy = node_copy.children[1]
				move_node = move_node.parent
		else:
			for child in node.children:
				self.reverse_lambda_replacement(child)

	def move_arguments_up(self, node):
		if node.type != "LIST" or len(node.children) == 1:
			return
		
		if node.parent.type == "LIST":
			self.move_arguments_up(node.parent)

			node.parent.children += node.children[1:]
			for child in node.children[1:]:
				child.parent = node.parent

			node.children = [node.children[0]]


	def simplify(self, node):
		match node.type:
			case "ROOT" | "LIST":
				for child in node.children:
					self.simplify(child)
			case "FUNCTION":
				for child in node.children:
					self.simplify(child)

				if node.value == "+":
					node.parent.type = "NAT"
					node.parent.value = str(self.sum(node))
					node.parent.children = []
				elif node.value == "++":
					if node.top_child().type != "LIST":
						return
					
					self.concat(node.top_child())
					node.parent.type = "LIST"
					node.parent.children = node.children[0].children
			case "LAMBDA":
				if len(node.children) < 3:
					if node.parent.type == "LIST" and len(node.parent.children) == 2:
						node.children.append(node.parent.children[1])
						node.parent.children = [node]
						node.children[2].parent = node
					else:
						self.simplify(node.children[1])
						return
				self.move_arguments_up(node.parent)
				self.replace_id(node.children[1], node.children[0].value, node.children[2])

				node.parent.type = node.children[1].type
				node.parent.value = node.children[1].value
				node.parent.children = node.children[1].children
				for child in node.children[1].children:
					child.parent = node.parent

				node = node.parent
				
				self.simplify(node)

	def print(self, node):
		match node.type:
			case "ROOT":
				for child in node.children:
					self.print(child)
					print()
			case "LIST":
				print("(", end=" ")
				for child in node.children:
					self.print(child)
					print(" ", end="")
				print(")", end="")
			case "NAT" | "EMPTY_LIST" | "ID":
				print(node.value, end="")

def main():
	if len(argv) != 2:
		return
	
	filename = argv[1]

	spec = {
		("NAT", "[0-9]+"),
		("EMPTY_LIST", "\\(\\)"),
		("LAMBDA", "lambda\\ "),
		("ID", "([a-z] | [A-Z])+"),
		("FUNCTION", "\\+\\+"),
		("FUNCTION", "\\+"),
		("LEFT_PARENTHESIS", "\\("),
		("RIGHT_PARENTHESIS", "\\)"),
		("LAMBDA_SEPARATOR", ":"),
		("SPACE", "\\ "),
		("NEWLINE", "\n"),
		("TAB", "\t"),
	}

	lexer = Lexer(spec)

	token_list = []
	with open(filename, 'r') as f:
		for line in f:
			token_list += lexer.lex(line)

	token_list = list(filter(lambda x: x[0] not in ["SPACE", "NEWLINE", "TAB"], token_list))

	parser = Parser(token_list)
	parser.parse()
	parser.reverse_lambda_replacement(parser.root)
	parser.simplify(parser.root)
	parser.print(parser.root)

if __name__ == '__main__':
    main()
