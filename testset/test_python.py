import ast
import re
import tlsh

def computeTlsh(string):
    string  = str.encode(string)
    hs      = tlsh.forcehash(string)
    return hs

def normalize(string):
    # Code for normalizing the input string.
    # LF and TAB literals, curly braces, and spaces are removed,
    # and all characters are lowercased.
    # ref: https://github.com/squizz617/vuddy
    return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

def removePyComment(code):
    # 큰 따옴표
    code = re.sub(r'(""".+?"""|\'\'\'.+?\'\'\')', '', code, flags=re.DOTALL)
    # 작은따옴표
    code = re.sub(r"('''|\"\"\").*?('''|\"\"\")", "", code, flags=re.DOTALL)
    return code

def extractPyFunction(node):
    function_bodies = []
    for item in node.body:
        if isinstance(item, ast.FunctionDef):
            function_code = removePyComment(ast.unparse(item))
            function_node = ast.parse(function_code)
            function_body = function_node.body[0]  # 함수 정의 노드
            function_bodies.append(function_body)
    return function_bodies
lineCnt = 0
fileCnt = 0
funcCnt = 0
resDict = {}
filePath = "example.py"
repoPath = "/mnt/c/Users/kdy/Desktop/project/Centris-public/src/osscollector/repo_src/redis@@redis"

with open(filePath, 'r', encoding="UTF-8") as file:
    python_code = file.readlines()
    lineCnt += len(python_code)
    python_code = "\n".join(python_code)
    fileCnt += 1


parsed_code = ast.parse(python_code)
module_node = ast.Module(body=parsed_code.body, type_ignores=[])
function_bodies = extractPyFunction(module_node)

# 함수 본문을 문자열로 추출합니다.
for func in function_bodies:
    function_code = ast.unparse(func)
    function_lines = function_code.split("\n")
    function_code = "\n".join(function_lines[1:])
    funcBody = normalize(function_code)
    funcHash = computeTlsh(funcBody)

    if len(funcHash) == 72 and funcHash.startswith("T1"):
        funcHash = funcHash[2:]
    elif funcHash == "TNULL" or funcHash == "" or funcHash == "NULL":
        continue

    storedPath = filePath.replace(repoPath, "")
    if funcHash not in resDict:
        resDict[funcHash] = []

    resDict[funcHash].append(storedPath)

    funcCnt += 1

print(resDict)
