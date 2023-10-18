import re
import tlsh
import subprocess

# Generate TLSH
def computeTlsh(string):
	string 	= str.encode(string)
	hs 		= tlsh.forcehash(string)
	return hs


def removeComment(string):
	# Code for removing C/C++ style comments. (Imported from VUDDY and ReDeBug.)
	# ref: https://github.com/squizz617/vuddy
	c_regex = re.compile(
		r'(?P<comment>//.*?$|[{}]+)|(?P<multilinecomment>/\*.*?\*/)|(?P<noncomment>\'(\\.|[^\\\'])*\'|"(\\.|[^\\"])*"|.[^/\'"]*)',
		re.DOTALL | re.MULTILINE)
	return ''.join([c.group('noncomment') for c in c_regex.finditer(string) if c.group('noncomment')])

def normalize(string):
	# Code for normalizing the input string.
	# LF and TAB literals, curly braces, and spaces are removed,
	# and all characters are lowercased.
	# ref: https://github.com/squizz617/vuddy
	return ''.join(string.replace('\n', '').replace('\r', '').replace('\t', '').replace('{', '').replace('}', '').split(' ')).lower()

ctagsPath = "/usr/local/bin/ctags" 			# Ctags binary path (please specify your own ctags path)
repoPath = "/mnt/c/Users/kdy/Desktop/project/Centris-public/src/osscollector/repo_src/redis@@redis"
filePath = "example.java"

fileCnt = 0
functionList = subprocess.check_output(ctagsPath + ' -f - --kinds-C=* --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode()

f = open(filePath, 'r', encoding = "UTF-8")
lineCnt = 0
funcCnt = 0
# For parsing functions
lines 		= f.readlines()
allFuncs 	= str(functionList).split('\n')
func   		= re.compile(r'(method)')
number 		= re.compile(r'(\d+)')
funcSearch	= re.compile(r'{([\S\s]*)}')
tmpString	= ""
funcBody	= ""

fileCnt 	+= 1
resDict = {}

for i in allFuncs:
	elemList	= re.sub(r'[\t\s ]{2,}', '', i)
	elemList 	= elemList.split('\t')
	funcBody 	= ""

	if i != '' and elemList[3] == 'method':
		funcStartLine 	 = int(number.search(elemList[4]).group(0))
		funcEndLine 	 = int(number.search(elemList[6]).group(0))


		tmpString	= ""
		tmpString	= tmpString.join(lines[funcStartLine - 1 : funcEndLine])

		if funcSearch.search(tmpString):
			funcBody = funcBody + funcSearch.search(tmpString).group(1)
		else:
			funcBody = " "
		
		funcBody = removeComment(funcBody)
		funcBody = normalize(funcBody)
		funcHash = computeTlsh(funcBody)
		if len(funcHash) == 72 and funcHash.startswith("T1"):
			funcHash = funcHash[2:]
		elif funcHash == "TNULL" or funcHash == "" or funcHash == "NULL":
			continue

		storedPath = filePath.replace(repoPath, "")
		if funcHash not in resDict:
			resDict[funcHash] = []
		resDict[funcHash].append(storedPath)

		lineCnt += len(lines)
		funcCnt += 1
