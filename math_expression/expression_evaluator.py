import operator
import re

OPERATORS = {
    '+': operator.add,
    '-': operator.sub,
    '*': operator.mul,
    '/': operator.truediv
}
LEFT_PAREN = '('
RIGHT_PAREN = ')'

def print_tree(tree, depth):

    for i in range(depth):
        print(" ", end='')

    if 'value' in tree:
        print(tree['value'])

    if 'left' in tree:
        print_tree(tree['left'], depth+1)

    if 'right' in tree:
        print_tree(tree['right'], depth+1)

def print_stack(stack):
    i = 0
    for x in stack:

        print(i, " ", x)
        i = i + 1


def build_parse_tree(expression):
    tree = {}
    stack = [tree]
    node = tree
    for token in expression:
        if token == LEFT_PAREN:
            node['left'] = {}
            print("PUSH", len(stack))
            stack.append(node)
            node = node['left']
        elif token == RIGHT_PAREN:
            print("POP", len(stack))
            node = stack.pop()
        elif token in OPERATORS:
            node['val'] = token
            node['right'] = {}
            stack.append(node)
            node = node['right']
        else:
            node['val'] = int(token)
            parent = stack.pop()
            node = parent
    return tree


def build_parse_tree3(expression):
    print("build_parse_tree3:" + expression)

    tree = {}


    for i in range(0, len(expression)):

        print("i == ", i, " len", len(expression))
        if (i < len(expression) - 1):
            (tree, i) = bpt(expression, i, tree)

        


    return tree


def bpt(expression, i, node):

    token = expression[i]

    print("bpt: i == ", i, ", token == " + token)

    p = re.compile('[0-9]')
    if p.match(token):
        print("assigning value:" + token)
        node['value'] = token

    if token == '+':
        print("building toekn node: " + token)
        left = node
        node = {}

        node['left'] = left
        node['value'] = token
        (right, newi) = bpt(expression, i+1, {})
        node['right'] = right
        i = i+1

    i = i+1


    return (node, i)
    






def build_parse_tree2(expression):

    print("build_parse_tree2:" + expression)

    tree = {}
    stack = [tree]
    node = tree

    for token in expression:
        if token == LEFT_PAREN:
            print("(")

            node['left'] = {}

            stack.append(node)
            node = node['left']

            continue

        if token == RIGHT_PAREN:
            print(")")
            
            if (len(stack) > 0):
                node = stack.pop()

            continue
        
        if token == '+':
            print("+ building node")
            left = node
            node = {}
            node['left'] = left
            node['value'] = token
            node['right'] = {}
            stack.append(node)
            node = node['right']
            print("TREE from operator")
            print_tree(tree, 0)

            continue
        
        p = re.compile('[0-9]')
        if p.match(token):
            print("assigning value:" + token)
            node['value'] = token
            parent = stack.pop()
            node = parent
            print("TREE from numeric value")
            print_tree(tree, 0)
            
            continue


    return node


#expr = "(7+3) * (5-2)"
#expr = "(7+3) + 2"
#expr = "(7+3)+2"
#expr = "(9+1)+(6+4)"
#expr = "(2)(2)"

#expr = "(2+1)"
expr = "7+1+2"
#pass expr = "7+1+3"



tree = build_parse_tree3(expr)

print("TREE")
print_tree(tree, 0)
print(tree)


