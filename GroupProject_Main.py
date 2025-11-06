import os, glob

def fileRead(folderPathName):
    folderPath = folderPathName
    engineFileList = []
    for fileName in glob.glob(os.path.join(folderPath, '*.htm')):
        with open(fileName, 'r') as f:
            text = f.read()
            engineFileList.append(text)
            print(fileName)
            print(len(text))
            f.close()
    for fileName in glob.glob(os.path.join(folderPath, '*.html')):
        with open(fileName, 'r') as f:
            text = f.read()
            engineFileList.append(text)
            print(fileName)
            print(len(text))
            f.close()
    return engineFileList
"""def fileRead():
    for filename in glob.glob('*.txt'):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:  # open in readonly mode"""


if __name__ == '__main__':
    folderPath = input("Please input the folder path: ")
    print(fileRead(folderPath))