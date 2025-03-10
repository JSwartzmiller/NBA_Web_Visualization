import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

#map for team names to abbreviations
TeamAbrMap = {
    "Atlanta": "ATL",
    "Boston": "BOS",
    "Brooklyn": "BRK",
    "Charlotte": "CHO",
    "Chicago": "CHI",
    "Cleveland": "CLE",
    "Dallas": "DAL",
    "Denver": "DEN",
    "Detroit": "DET",
    "Golden State": "GSW",
    "Houston": "HOU",
    "Indiana": "IND",
    "LA": "LAC",
    "Los Angeles": "LAL",
    "Memphis": "MEM",
    "Miami": "MIA",
    "Milwaukee": "MIL",
    "Minnesota": "MIN",
    "New Orleans": "NOP",
    "New York": "NYK",
    "Oklahoma City": "OKC",
    "Orlando": "ORL",
    "Philadelphia": "PHI",
    "Phoenix": "PHO",
    "Portland": "POR",
    "Sacramento": "SAC",
    "San Antonio": "SAS",
    "Toronto": "TOR",
    "Utah": "UTA",
    "Washington": "WAS",
}

#function to scrape for all NBA teams
def getTeams():
    #url that displays all nba teams
    teams_url = "https://www.espn.com/nba/teams"   
    #copied headers from geeks for geeks
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"}

    #send a response and check if response is valid
    response = requests.get(teams_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve NBA teams data. Status Code: {response.status_code}")
        exit()

    #use beautiful soap to format html request
    data = BeautifulSoup(response.text, "html5lib")
    
    team_dictionary = {} #team dictionary
    
    #iterate through all divisions of teams
    for team_section in data.find_all("section", class_="TeamLinks"):
        #extract the <h2> tags associated
        team_data = team_section.find_previous("h2")

        if team_data:
            #Strip the team data to extract the team name
            team_name = team_data.text.strip()

            #extract the schedule link for each team
            schedule_link_data = team_section.find("a", text="Schedule")
            if schedule_link_data and "href" in schedule_link_data.attrs:
                #concat url and add to dictionary
                schedule_url = "https://www.espn.com" + schedule_link_data["href"]
                team_dictionary[team_name] = schedule_url

    #return created dictionary
    return team_dictionary      

#function that gets information about today's games
def getGamesToday():
    #URL that holds todays NBA schedule
    url = "https://www.espn.com/nba/schedule"
    #copied from geeks for geeks
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    }

    #check for valid response
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to retrieve schedule. Status Code: {response.status_code}")
        exit()
    
    #use Beautiful soup to format html request
    data = BeautifulSoup(response.text, "html5lib")
    
    #scrape page for table of games
    allGames = data.find("div", class_="Table__Scroller")
    if not allGames:
        print("Could not find the table container.")
        exit()

    todaysGames = allGames.find("table", class_="Table")

    while todaysGames:
        todayData = todaysGames.find("tbody")
        if not todayData:
            print("Error locating todays game data")
            exit()

        gameRows = todayData.find_all("tr", attrs={"data-idx": True})
        #check if games have been played already
        if gameRows and len(gameRows[0].find_all("td")) == 6:
            break
        else:
            #games already been played and use next table to pull data
            todaysGames = todaysGames.find_next("table", class_="Table")

    #pull the data for the correct table of future games
    todayData = todaysGames.find("tbody")
    gameRows = todayData.find_all("tr", attrs={"data-idx": True})
    
    games = [] #table to store game info

    #iterate through each game and schedule data
    for game in gameRows:
        gameContent = game.find_all("td")

        #filter useful information
        awayTeam = gameContent[0].get_text()
        homeTeam = gameContent[1].get_text()
        homeTeam = homeTeam.replace('@', '').strip()

        gamblingStats = gameContent[5].get_text()
        #if game stats are changing they won't show up on espn
        if gamblingStats and "O/U:" in gamblingStats:
            gameline, totalPoints = gamblingStats.split("O/U:")
            gameline = gameline.replace("Line:", "").strip()
            totalPoints = totalPoints.strip()
        else:
            gameline = ""
            totalPoints = ""
    
        #add information to dictionary and append to game array
        gameDetails = {
            "awayTeam": awayTeam,
            "homeTeam": homeTeam,
            "gameline": gameline,
            "overUnder": totalPoints
        }
        games.append(gameDetails)

    return games
    
#shows matchups for suer to select
def displayMatchup(games):
    print("Today's Matchups:")

    #iterate through all games and ad values for the user to select
    for i, game in enumerate(games, start=1):
        print(f"{i}. {game['awayTeam']} at {game['homeTeam']} "
              f"(Line: {game['gameline']}, O/U: {game['overUnder']})")

#function to allow user to investigate specific game
def userSelectGame(games):
    displayMatchup(games)
    while True:
        try:
            userInput = int(input("Enter the number of the matchup you want to see: "))
            #check for valid input
            if 1 <= userInput <= len(games):
                return games[userInput - 1]
            else:
                print(f"Please enter a number between 1 and {len(games)}.")
        except ValueError:
            print("Invalid input. Please enter a number.")

#function gets teams basketball refrence url based on entering city name
def getTeamUrl(team):
    #get mapped abbreviation
    teamAbbr = TeamAbrMap[team]
    #format the new url and return it
    url = f"https://www.basketball-reference.com/teams/{teamAbbr}/2025.html"
    return url

#function to scrape data from table
def scrapeTeamDetailPage(teamURL):
    #check for valid url and html data
    response = requests.get(teamURL)
    if response.status_code != 200:
        print("Can't reach team page")
        exit()
    
    #Remove html comments
    repsonse = re.sub(r'<!--|-->', '', response.text)

    #get data of url and pass through beautiful soup
    data = BeautifulSoup(repsonse, 'html.parser')

    #returns the data on the page
    return data

#function returns df of team injuries
def getInjuryTable(pageData):
    #pageData = BeautifulSoup(pageData, "html5lib")

    #Check if injury table dowsn't exist
    noInjuryMessege = pageData.find("p", string="No current injuries to report.")
    if noInjuryMessege:
        print("No current injuries")
        return None
    
    #find table by id of injuries and check if valid
    table = pageData.find("table", id="injuries")
    if not table:
        print("Injury table not found")
        exit()

    #get the column headers and save in array
    header = table.find("thead").find("tr")
    columnNames= [th.get_text(strip=True) for th in header.find_all("th")]

    rows = [] #array for row data

    #iterate through table and scrape each row for data
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all(["th", "td"])
        rowData = [cell.get_text(strip=True) for cell in cells]
        rows.append(rowData)

    #create data frame with columns and rows found
    df = pd.DataFrame(rows, columns=columnNames)
    return df

#function returns df of the team stats per game
def getTeamStats(pageData):
    #find table by id of per_game_stats and check if valid
    table = pageData.find("table", id="per_game_stats")
    if not table:
        print("Couldn't find stats table")
        exit()
    
    #get column headers and save in array
    header = table.find("thead").find("tr")
    columnNames= [th.get_text(strip=True) for th in header.find_all("th")]
    
    rows = [] #array for row data
    playerLinks = {} #dictionary to store indiv player links

    #iterate through table and scrape each row for data
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all(["th", "td"])
        rowData = [cell.get_text(strip=True) for cell in cells]
        
        #Find the player link in the row with 'name_display'
        nameDisplayCell = [cell for cell in cells if cell.get('data-stat') == 'name_display']
        if nameDisplayCell:
            linkTag = nameDisplayCell[0].find("a")
            if linkTag:
                #concat correct link together
                link = linkTag["href"]
                #chnage end of link with correct ending
                if link.endswith(".html"):
                    # Remove the last 5 characters (".html")
                    link = link[:-5]
                    # Append the game log path
                    link += "/gamelog/2025/"
                link = "https://www.basketball-reference.com" + link

                #find playerName and add link to dictionary
                playerName = linkTag.get_text(strip=True)
                playerLinks[playerName] = link

        rows.append(rowData)

    #create data frame with columns and rows found
    df = pd.DataFrame(rows, columns=columnNames)
    #clean df to remove double index and awards column
    df.drop(['Rk', 'Awards'], axis=1, inplace=True) 

    #return the data frame and dictionary with player links
    return df, playerLinks


#function to return df with player game logs
def getPlayerGames(playerURL):
    #check for valid url and html data
    response = requests.get(playerURL)
    if response.status_code != 200:
        print("Can't reach team page")
        exit()

    #Remove html comments
    repsonse = re.sub(r'<!--|-->', '', response.text)

    #get data of url and pass through beautiful soup
    data = BeautifulSoup(repsonse, 'html.parser')

    #find table
    table = data.find("table", id="pgl_basic")
    if not table:
        print("Can't find player gamelog")
        exit()

    #get column headers and save in array
    header = table.find("thead").find("tr")
    columnNames= [th.get_text(strip=True) for th in header.find_all("th")]

    rows = [] #array for row data

    #iterate through table and scrape each row for data
    for row in table.find("tbody").find_all("tr"):
        cells = row.find_all(["th", "td"])
        rowData = [cell.get_text(strip=True) for cell in cells]
        rows.append(rowData)

    #create data frame with columns and rows found
    df = pd.DataFrame(rows, columns=columnNames)
    #clean df to remove double index and awards column
    df.drop(['Rk', 'G'], axis=1, inplace=True) 
    return df


def main():
    #get user to pick a game
    selectedGame = userSelectGame(getGamesToday())
    teamUrl = getTeamUrl(selectedGame["awayTeam"]) #away team example

    teamDetailHtml = scrapeTeamDetailPage(teamUrl) #get team page data

    #check for team injuries
    teamInjuryTable = getInjuryTable(teamDetailHtml)
    

    #Get df of Team Stats and dictionary for each player page {name: url}
    teamStatsDf, playerDict = getTeamStats(teamDetailHtml)

    #test get player stats
    playerUrl = playerDict[teamStatsDf["Player"][1]]
    randomStats = getPlayerGames(playerUrl)
