
"""
Dataset Collection Tool.
Author:		Seunghoon Woo (seunghoonwoo@korea.ac.kr)
Modified: 	December 16, 2020.
"""

import os
import ast
import sys
import subprocess
import re
import tlsh # Please intall python-tlsh

"""GLOBALS"""

currentPath	= os.getcwd()
gitCloneURLS= currentPath + "/sample" 			# Please change to the correct file (the "sample" file contains only 10 git-clone urls)
clonePath 	= currentPath + "/repo_src/"		# Default path
tagDatePath = currentPath + "/repo_date/"		# Default path
resultPath	= currentPath + "/repo_functions/"	# Default path
ctagsPath	= "/usr/local/bin/ctags" 			# Ctags binary path (please specify your own ctags path)

# Generate directories
shouldMake = [clonePath, tagDatePath, resultPath]
for eachRepo in shouldMake:
	if not os.path.isdir(eachRepo):
		os.mkdir(eachRepo)


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

# python 주석 제거
def removePyComment(code):
	# 큰 따옴표
	code = re.sub(r'(""".+?"""|\'\'\'.+?\'\'\')', '', code, flags=re.DOTALL)
	# 작은따옴표
	code = re.sub(r"('''|\"\"\").*?('''|\"\"\")", "", code, flags=re.DOTALL)
	return code

# python 함수 추출
def extractPyFunction(node):
	function_bodies = []
	for item in node.body:
		if isinstance(item, ast.FunctionDef):
			function_code = removePyComment(ast.unparse(item))
			function_node = ast.parse(function_code)
			function_body = function_node.body[0]  # 함수 정의 노드
			function_bodies.append(function_body)
	return function_bodies

def hashing(repoPath):
	# This function is for hashing C/C++ functions
	# Only consider ".c", ".cc", and ".cpp" files
	possible_c = (".c", ".cc", ".cpp")
	possible_py = (".py")
	possible_java = (".java")
	
	fileCnt  = 0
	funcCnt  = 0
	lineCnt  = 0

	resDict  = {}

	for path, dir, files in os.walk(repoPath):
		for file in files:
			filePath = os.path.join(path, file)
			print(filePath)
			if file.endswith(possible_c):
				try:
					# Execute Ctgas command
					functionList = subprocess.check_output(ctagsPath + ' -f - --kinds-C=* --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode()

					f = open(filePath, 'r', encoding = "UTF-8")

					# For parsing functions
					lines 		= f.readlines()
					allFuncs 	= str(functionList).split('\n')
					func   		= re.compile(r'(function)')
					number 		= re.compile(r'(\d+)')
					funcSearch	= re.compile(r'{([\S\s]*)}')
					tmpString	= ""
					funcBody	= ""

					fileCnt 	+= 1

					for i in allFuncs:
						elemList	= re.sub(r'[\t\s ]{2,}', '', i)
						elemList 	= elemList.split('\t')
						funcBody 	= ""
						if i != '' and len(elemList) >= 8 and func.fullmatch(elemList[3]):
							funcStartLine 	 = int(number.search(elemList[4]).group(0))
							funcEndLine 	 = int(number.search(elemList[7]).group(0))

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

				except subprocess.CalledProcessError as e:
					print("Parser Error:", e)
					continue
				except Exception as e:
					print ("Subprocess failed", e)
					continue

			elif file.endswith(possible_py):
				with open(filePath, 'r', encoding="UTF-8") as file:
					python_code = file.readlines()
					lineCnt += len(python_code)
					python_code = "\n".join(python_code)
					fileCnt += 1

				parsed_code = ast.parse(python_code)
				module_node = ast.Module(body=parsed_code.body, type_ignores=[])
				function_bodies = extractPyFunction(module_node)
				# 함수 본문을 문자열로 추출
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


			elif file.endswith(possible_java):
				try:
					# Execute Ctgas command
					functionList = subprocess.check_output(ctagsPath + ' -f - --kinds-C=* --fields=neKSt "' + filePath + '"', stderr=subprocess.STDOUT, shell=True).decode()

					f = open(filePath, 'r', encoding = "UTF-8")

					# For parsing functions
					lines 		= f.readlines()
					allFuncs 	= str(functionList).split('\n')
					func		= re.compile(r'(method)')
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

				except subprocess.CalledProcessError as e:
					print("Parser Error:", e)
					continue
				except Exception as e:
					print ("Subprocess failed", e)
					continue

	return resDict, fileCnt, funcCnt, lineCnt 

def indexing(resDict, title, filePath):
	# For indexing each OSS

	fres = open(filePath, 'w')
	fres.write(title + '\n')

	for hashval in resDict:
		if hashval == '' or hashval == ' ':
			continue

		fres.write(hashval)
		
		for funcPath in resDict[hashval]:
			fres.write('\t' + funcPath)
		fres.write('\n')

	fres.close()


def main():
	with open(gitCloneURLS, 'r', encoding = "UTF-8") as fp:
		funcDateDict = {}
		lines		 = [l.strip('\n\r') for l in fp.readlines()]
		
		for eachUrl in lines:
			os.chdir(currentPath)
			repoName 	= eachUrl.split("github.com/")[1].replace(".git", "").replace("/", "@@") # Replace '/' -> '@@' for convenience
			print ("[+] Processing", repoName)

			try:
				cloneCommand 	= eachUrl + ' ' + clonePath + repoName
				cloneResult 	= subprocess.check_output(cloneCommand, stderr = subprocess.STDOUT, shell = True).decode()

				os.chdir(clonePath + repoName)

				dateCommand 	= 'git log --tags --simplify-by-decoration --pretty="format:%ai %d"'  # For storing tag dates
				dateResult		= subprocess.check_output(dateCommand, stderr = subprocess.STDOUT, shell = True).decode()
				tagDateFile 	= open(tagDatePath + repoName, 'w')
				tagDateFile.write(str(dateResult))
				tagDateFile.close()


				tagCommand		= "git tag"
				tagResult		= subprocess.check_output(tagCommand, stderr = subprocess.STDOUT, shell = True).decode()

				resDict = {}
				fileCnt = 0
				funcCnt = 0
				lineCnt = 0


				if tagResult == "":
					# No tags, only master repo

					resDict, fileCnt, funcCnt, lineCnt = hashing(clonePath + repoName)
					if len(resDict) > 0:
						if not os.path.isdir(resultPath + repoName):
							os.mkdir(resultPath + repoName)
						title = '\t'.join([repoName, str(fileCnt), str(funcCnt), str(lineCnt)])
						resultFilePath 	= resultPath + repoName + '/fuzzy_' + repoName + '.hidx' # Default file name: "fuzzy_OSSname.hidx"
						
						indexing(resDict, title, resultFilePath)

				else:
					for tag in str(tagResult).split('\n'):
						# Generate function hashes for each tag (version)

						checkoutCommand	= subprocess.check_output("git checkout -f " + tag, stderr = subprocess.STDOUT, shell = True)
						resDict, fileCnt, funcCnt, lineCnt = hashing(clonePath + repoName)
						
						if len(resDict) > 0:
							if not os.path.isdir(resultPath + repoName):
								os.mkdir(resultPath + repoName)
							title = '\t'.join([repoName, str(fileCnt), str(funcCnt), str(lineCnt)])
							resultFilePath 	= resultPath + repoName + '/fuzzy_' + tag + '.hidx'
						
							indexing(resDict, title, resultFilePath)
						

			except subprocess.CalledProcessError as e:
				print("Parser Error:", e)
				continue
			except Exception as e:
				print ("Subprocess failed", e)
				continue

""" EXECUTE """
if __name__ == "__main__":
	main()
