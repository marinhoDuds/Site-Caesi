import os
import tokenize
import io

def strip_comments(source_code):
    result = []
    tokens = tokenize.generate_tokens(io.StringIO(source_code).readline)
    last_lineno = -1
    last_col = 0
    
    try:
        for tok in tokens:
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]
            
            if start_line > last_lineno:
                last_col = 0
            
            if start_col > last_col:
                result.append(" " * (start_col - last_col))
            
            if token_type == tokenize.COMMENT:
                pass # skip comment
            else:
                result.append(token_string)
                
            last_lineno = end_line
            last_col = end_col
    except tokenize.TokenError:
        return source_code # fallback
        
    return "".join(result)

for root, _, files in os.walk("backend/src"):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            stripped = strip_comments(code)
            with open(path, "w", encoding="utf-8") as f:
                f.write(stripped)

for root, _, files in os.walk("backend/tests"):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            stripped = strip_comments(code)
            with open(path, "w", encoding="utf-8") as f:
                f.write(stripped)
print("Python comments stripped.")
