import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

def fileRead(folderPathName):
    folderPath = folderPathName.strip().strip('"').strip("'")  # tiny cleanup
    engineFileList = []

    # search .htm recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.htm'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            #engineFileList.append("NEXT SET OF TEXT AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n")
            print(fileName)
            print(len(text))

    # search .html recursively
    for fileName in glob.glob(os.path.join(folderPath, '**', '*.html'), recursive=True):
        with open(fileName, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read()
            engineFileList.append(text)
            #engineFileList.append("NEXT SET OF TEXT AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\n\n")
            print(fileName)
            print(len(text))

    return engineFileList

"""def fileRead():
    for filename in glob.glob('*.txt'):
        with open(os.path.join(os.getcwd(), filename), 'r') as f:  # open in readonly mode
            ...
"""
def htmlToList(engineFileList): #takes in a list of the read files with each entry of the list being an entire html text document.
    engineList = []  # contains a list of all engines and the names of the titles
    tempList = []  # used in the loop to make a list for each engine. first item of the list will be the engine name. then each game name and app id will have an entry
    for lineString in engineFileList:
        tempList.clear()  # clearing the temp list so that we start fresh for each game engine
        titleStart = lineString.find("<title>") + 7
        titleEnd = lineString.find(" · SteamDB")
        # print(titleStart, titleEnd)
        tempList.append(lineString[titleStart:titleEnd])
        tempPosition = titleEnd
        #print(tempList)
        # print(len(lineString))
        while tempPosition < len(lineString):  # this loop finds appIDs, names, price, rating score, and top player count of the games in that order
            if lineString.find('<a class="b" href="', tempPosition) == -1:
                break
            # print("I GOT PASSED THE BREAK CHECK")
            nameStart = lineString.find('<a class="b" href="', tempPosition)
            tempPosition = nameStart
            nameEnd = lineString.find('</a>', tempPosition)
            nameStart = nameStart + len('<a class="b" href="')
            tempName = lineString[nameStart:nameEnd]
            #tempList.append(lineString[nameStart:nameEnd])
            #print(tempList)
            #break
            #cleaning stuff up for the game class
            tempName = tempName.replace('/app/', '')
            tempName = tempName.replace('/"', '')
            tempName = tempName.replace("&apos;", "'")
            tempName = tempName.replace("&quot;", '"')
            nameStart = tempName.find(">")
            tempID = tempName[:nameStart] #the id for the game class
            tempName = tempName[nameStart:] #the name for the game class
            """
            tempList[len(tempList) - 1] = tempList[len(tempList) - 1].replace('/app/', '')  # cleaning up the string so its just the appID and name separated by >
            tempList[len(tempList) - 1] = tempList[len(tempList) - 1].replace('/"', '')"""
            tempPosition = nameEnd  # start of trying to get the extra data
            dataStart = lineString.find('</td>', tempPosition)
            tempPosition = dataStart
            #dataEnd = lineString.find('</tr>', tempPosition)
            dataStart = lineString.find('<td data-sort="', tempPosition) #getting the position of the discount
            dataEnd = lineString.find('>', dataStart)
            tempPosition = dataEnd

            costStart = lineString.find('"', tempPosition)
            #costStart = lineString.find('<td data-sort="', tempPosition) #getting the position of the cost
            costEnd = lineString.find('>', costStart)
            tempCost = lineString[costStart:costEnd]
            tempCost = tempCost.replace('"', '')
            print(tempCost)
            tempPosition = costEnd

            ratingStart = lineString.find('"', tempPosition)
            #ratingStart = lineString.find('<td data-sort="', tempPosition)
            ratingEnd = lineString.find('>', ratingStart)
            tempRating = lineString[ratingStart:ratingEnd]
            tempRating = tempRating.replace('"', '')
            """if len(tempRating) < 2:
                tempRating = -1"""
            tempPosition = ratingEnd

            releaseStart = lineString.find('"', tempPosition)
            #releaseStart = lineString.find('<td data-sort="', tempPosition)
            releaseEnd = lineString.find('>', releaseStart)
            tempRelease = lineString[releaseStart:releaseEnd]
            tempRelease = tempRelease.replace('"', '')
            print(tempRelease)
            tempPosition = releaseEnd


            dataStart = lineString.find('="', tempPosition)  #position of following count
            tempPosition = dataStart
            dataStart = lineString.find('<td data-sort="', tempPosition) #position of online count
            tempPosition = dataStart
            dataStart = lineString.find('>', tempPosition)
            tempPosition = dataStart

            topPlayerCountStart = lineString.find('"', tempPosition)
            #topPlayerCountStart = lineString.find('<td data-sort="', tempPosition)
            topPlayerCountEnd = lineString.find('>', topPlayerCountStart)
            tempTopPlayerCount = lineString[topPlayerCountStart:topPlayerCountEnd]
            tempTopPlayerCount = tempTopPlayerCount.replace('"', '')
            """if len(tempTopPlayerCount) < 1:
                tempTopPlayerCount = -1"""

            tempGame = Game(tempID, tempName, tempCost, tempRating, tempRelease, tempTopPlayerCount)
            tempList.append(tempGame)

        engineList.append(tempList.copy())
    return engineList

class Game:
    def __init__(self, id, title, cost, rating, releaseDate, topPlayerCount):
        self.id = id
        self.title = title
        try:
            #self.cost = cost
            self.cost = float(cost)
        except:
            self.cost = -1
        try:
            self.rating = float(rating)
        except:
            self.rating = -1
        #self.releaseDate = releaseDate
        try:
            #self.releaseDate = releaseDate
            self.releaseDate = datetime.fromtimestamp(int(releaseDate))
        except:
            self.releaseDate = "Unreleased"
        try:
            #self.topPlayerCount = topPlayerCount
            self.topPlayerCount = float(topPlayerCount) #will be -1 if no top player count
        except:
            self.topPlayerCount = -1
        try:
            #self.revenueEstimate = "estimated"
            self.revenueEstimate = float(cost) * float(topPlayerCount) #changing this to just make it quick to push
        except:
            self.revenueEstimate = -1

"""def engineListToDict(engineList):
    engineDict = {}
    idList = []
    nameList = []
    costList = []
    ratingList = []
    releaseDateList = []
    topPlayerCountList = []
    revenueEstimateList = []
    for list in engineList:
        tempKey = list[0]
        index = 1
        while index < len(list):
            idList.append(list[index].id.copy())
            nameList.append(list[index].name.copy())
            costList.append(list[index].cost.copy())
            ratingList.append(list[index].rating.copy())
            releaseDateList.append(list[index].releaseDate.copy())
            topPlayerCountList.append(list[index].topPlayerCount.copy())
            revenueEstimateList.append(list[index].revenueEstimate.copy())
            index += 1
        data = {
            "ID": idList.copy(),
            "Name": nameList.copy(),
            "Cost": costList.copy(),
            "Rating": ratingList.copy(),
            "ReleaseDate": releaseDateList.copy(),
            "Top Player Count": topPlayerCountList.copy(),
            "Estimated Revenue": revenueEstimateList.copy(),
        }
        df = pd.DataFrame(data)
        engineDict[tempKey] = df.copy()
    return engineDict"""


if __name__ == '__main__':
    folderPath = input("Please input the folder path: ")
    engineFileList = fileRead(folderPath)

    engineList = htmlToList(engineFileList)
    #engineDict = engineListToDict(engineList)
    for list in engineList:
        index = 1
        while index < len(list):
            print(list[index].id)
            print(list[index].title)
            print(list[index].cost)
            print(list[index].rating)
            print(list[index].releaseDate)
            print(list[index].topPlayerCount)
            print(list[index].revenueEstimate)
            index += 1

        #engineList[]
        #print(engineList[0])
    #print(len(engineList))
    #print(engineDict)

    # print(fileRead(folderPath))
