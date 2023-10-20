import ast
import astor

def removeDocstring(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
        node.body = [item for item in node.body if not (isinstance(item, ast.Expr) and hasattr(item, 'value') and isinstance(item.value, ast.Str))]

def process_ast_tree(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            node.body = [item for item in node.body if not (isinstance(item, ast.Expr) and hasattr(item, 'value') and isinstance(item.value, ast.Str))]
        else:
            removeDocstring(node)
    return astor.to_source(parsed)

if __name__ == "__main__":
    parsed = ast.parse(open('test.py').read())
    rem_code = process_ast_tree(parsed)
    print(rem_code)
    
