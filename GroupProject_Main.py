import os
import glob

def fileRead(folderPathName):
    folderPath = folderPathName.strip().strip('"').strip("'")  # tiny cleanup
    engineFileList = []

    # search .htm recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.htm'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            print(fileName)
            print(len(text))

    # search .html recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.html'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            print(fileName)
            print(len(text))

    return engineFileList

"""def fileRead():
    for filename in glob.glob('*.txt'):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:  # open in readonly mode
            ...
"""

if __name__ == '__main__':
    folderPath = input("Please input the folder path: ")
    engineFileList = fileRead(folderPath)
    engineList = []  # contains a list of all engines and the names of the titles
    tempList = []  # used in the loop to make a list for each engine. first item of the list will be the engine name. then each game name and app id will have an entry
    for lineString in engineFileList:
        tempList.clear()  # clearing the temp list so that we start fresh for each game engine
        titleStart = lineString.find("<title>") + 7
        titleEnd = lineString.find(" · SteamDB")
        # print(titleStart, titleEnd)
        tempList.append(lineString[titleStart:titleEnd])
        tempPosition = titleEnd
        # print(tempList)
        # print(len(lineString))
        while tempPosition < len(
                lineString):  # this loop finds appIDs, names, price, rating score, and top player count of the games in that order
            if lineString.find('<a class="b" href="', tempPosition) == -1:
                break
            # print("I GOT PASSED THE BREAK CHECK")
            nameStart = lineString.find('<a class="b" href="', tempPosition)
            tempPosition = nameStart
            nameEnd = lineString.find('</a>', tempPosition)
            nameStart = nameStart + len('<a class="b" href="')
            tempList.append(lineString[nameStart:nameEnd])
            tempList[len(tempList) - 1] = tempList[len(tempList) - 1].replace('/app/',
                                                                              '')  # cleaning up the string so its just the appID and name separated by >
            tempList[len(tempList) - 1] = tempList[len(tempList) - 1].replace('/"', '')
            tempPosition = nameEnd  # start of trying to get the extra data

            dataStart = lineString.find('<td>', tempPosition)
            # print(lineString[nameStart:nameEnd])
        engineList.append(tempList)
    print(engineList)

    # print(fileRead(folderPath))
