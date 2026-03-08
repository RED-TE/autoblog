import ast
filepath = r"C:\Users\jhxox\Desktop\blolg_aoto\bot_app.py"

with open(filepath, "r", encoding="utf-8") as f:
    source = f.read()

tree = ast.parse(source)

for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "BotApp":
        for stmt in node.body:
            if isinstance(stmt, ast.FunctionDef) and stmt.name == "__init__":
                args = [arg.arg for arg in stmt.args.args]
                print(f"BotApp.__init__ args: {args}")
                line_no = stmt.lineno
                print(f"BotApp.__init__ is defined at line {line_no}")
