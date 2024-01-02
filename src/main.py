from sys import argv
from .Lexer import Lexer

class Node:
	def __init__(self, type, value, children, parent=None):
		self.type = type
		self.value = value
		self.children = children
		self.parent = parent

	def __str__(self):
		if self.type == "NAT" or self.type == "EMPTY_LIST" or self.type == "ID" or self.type == "FUNCTION":
			return str(self.value)
		return str(self.type)
	
	def print_tree(self, level=0):
		print("\t" * level + self.__str__())
		for child in self.children:
			child.print_tree(level + 1)
	
class Parser:
	def __init__ (self, token_list):
		self.token_list = token_list
		self.index = 0

	def parse(self) -> Node:
		self.root = Node("ROOT", None, [])
		curr_node = self.root

		i = 0
		while i < len(self.token_list):
			match self.token_list[i][0]:
				case "NAT" | "EMPTY_LIST" | "ID":
					curr_node.children.append(Node(self.token_list[i][0], self.token_list[i][1], [], curr_node))
				case "++_FUNCTION":
					curr_node.children.append(Node("FUNCTION", "++", [], curr_node))
				case "+_FUNCTION":
					curr_node.children.append(Node("FUNCTION", "+", [], curr_node))
				case "LEFT_PARENTHESIS":
					if self.token_list[i + 1][0] not in ["LAMBDA", "++_FUNCTION", "+_FUNCTION"]:
						curr_node.children.append(Node("LIST", None, [], curr_node))
						curr_node = curr_node.children[-1]
					else:
						curr_node.children.append(Node("APPLICATION", None, [], curr_node))
						curr_node = curr_node.children[-1]
				case "RIGHT_PARENTHESIS":
					curr_node = curr_node.parent

			i += 1

		return self.root
	
	def append_all(self, node: Node) -> [Node]:
		ans = []

		for child in node.children:
			if child.type == "LIST":
				ans += self.append_all(child)
			elif child.type == "NAT" or child.type == "ID":
				ans.append(child)

		return ans
	
	def sum_all(self, node: Node) -> int:
		ans = 0

		for child in node.children:
			if child.type == "LIST":
				ans += self.sum_all(child)
			elif child.type == "NAT":
				ans += int(child.value)
			elif child.type == "EMPTY_LIST":
				ans += 0

		return ans

	def reduce_tree(self, node: Node):
		match node.type:
			case "ROOT" | "LIST":
				for child in node.children:
					self.reduce_tree(child)
			case "APPLICATION":
				node.type = "LIST"
				op = node.children[0].value
				node.children = node.children[1:]

				for child in node.children:
					self.reduce_tree(child)

				if op == "++":
					curr = node.children[0]

					if curr.type != "LIST":
						return

					for child in curr.children:
						if child.type == "LIST":
							for c in child.children:
								node.children.append(c)
						elif child.type == "NAT":
							node.children.append(child)

					node.children = node.children[1:]
				elif op == "+":
					node.type = "NAT"
					node.value = self.sum_all(node)
					node.children = []

	def print_tree(self, node: Node):
		match node.type:
			case "ROOT":
				for child in node.children:
					self.print_tree(child)
					print()
			case "LIST":
				print("(", end=" ")
				for child in node.children:
					self.print_tree(child)
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
		("++_FUNCTION", "\\+\\+"),
		("+_FUNCTION", "\\+"),
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
	tree = parser.parse()
	# tree.print_tree()

	parser.reduce_tree(tree)
	# tree.print_tree()

	parser.print_tree(tree)

if __name__ == '__main__':
    main()
