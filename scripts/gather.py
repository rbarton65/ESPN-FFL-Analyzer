from __future__ import division
import urllib2
import re
import urlparse
import string
import numpy
import argparse
import operator
from datetime import datetime
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--league", help="ESPN league ID", required=True)
args = parser.parse_args()

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
teams=[]
template={"League Name": None, "Number of Teams": None, "Regular Season Matchups": None, "Playoff Teams": None, "Playoff Seeding Tie Breaker": None}
settings={}
schedule = {}

class TeamID:
        def __init__(self, name, owner, ID, pf, pa, year, division):
			self.name = name
			self.owner = owner
			self.ID = ID
			self.pf = pf
			self.pa = pa
			self.year = year
			self.division = division
			self.wins = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0] #up to 32 different IDs incase new members replace old ones
			self.mov = []
			self.scores = []

def history():
	"""Finds the years for the league"""
	years=[]
	url = "http://games.espn.go.com/ffl/standings?leagueId=%s" % (args.league)
        ourUrl = opener.open(url).read()
        soup = BeautifulSoup(ourUrl)
        for year in soup.findAll('option'):
			years.append(year.text)
			schedule[year.text] = {}
	return years

def gather_teams(years):
        """Gathers team names and ID numbers in the specified league"""
        for year in years:
		url = "http://games.espn.go.com/ffl/standings?leagueId=%s&seasonId=%s" % (args.league, year)
        	ourUrl = opener.open(url).read()
	        soup = BeautifulSoup(ourUrl)
		for num,division in enumerate(soup.findAll(bgcolor = '#ffffff', id = re.compile(r'\d'))):
	        	for i in division.findAll('tr', {'class' : 'evenRow bodyCopy sortableRow'}):
				title = i.find('td').text
				owner = string.capwords(title[title.find("(")+1:title.find(")")])
				pf = i.find('td', {'class': 'sortablePF'}).text
				pa = i.find('td', {'class': 'sortablePA'}).text
		                parsed = urlparse.urlparse(i.a['href']) #parse url parameters
        		        id = urlparse.parse_qs(parsed.query)['teamId'][0]
	                	name = i.a.text
		                teams.append(TeamID(name,owner,int(id),pf,pa,year,num+1))
			for i in division.findAll('tr', {'class' : 'oddRow bodyCopy sortableRow'}):
				title = i.find('td').text
		                owner = string.capwords(title[title.find("(")+1:title.find(")")])
        		        pf = i.find('td', {'class': 'sortablePF'}).text
                		pa = i.find('td', {'class': 'sortablePA'}).text
				parsed = urlparse.urlparse(i.a['href']) #parse url parameters
	        	        id = urlparse.parse_qs(parsed.query)['teamId'][0]
        	        	name = i.a.text
                		teams.append(TeamID(name,owner,int(id),pf,pa,year,num+1))

def gather_settings(years):
	"""Gathers league settings"""
	for year in years:
		url = "http://games.espn.go.com/ffl/leaguesetup/settings?leagueId=%s&seasonId=%s" % (args.league, year)
		ourUrl = opener.open(url).read()
		soup = BeautifulSoup(ourUrl)
		settings[year] = {}
		for i in soup.findAll('td', {'class' : 'settingLabel'}):
			for setting in template:
				if setting == i.text:
					settings[year][setting] = i.findNext('td').text
		settings[year]["Playoff Teams"] = int(settings[year]["Playoff Teams"].split()[0])
		settings[year]["Regular Season Matchups"] = int(settings[year]["Regular Season Matchups"].split()[0])
		settings[year]["Number of Teams"] = int(settings[year]["Number of Teams"])

def gather_matchups(years):
	"""Gathers matchups, wins, scores for each team"""
	for year in years:
		for week in range(1, settings[year]["Regular Season Matchups"]+1):
			url = "http://games.espn.go.com/ffl/scoreboard?leagueId=%s&matchupPeriodId=%s&seasonId=%s" % (args.league, week, year)
			ourUrl = opener.open(url).read()
			soup = BeautifulSoup(ourUrl)
			schedule[year][week] = []
			for i in soup.findAll('table', {'class' : 'ptsBased matchup'}):
				parsed1 = urlparse.urlparse(i.findAll('a')[1]['href'])
				id1 = urlparse.parse_qs(parsed1.query)['teamId'][0]
				parsed2 = urlparse.urlparse(i.findAll('a')[0]['href'])
				id2 = urlparse.parse_qs(parsed2.query)['teamId'][0]
				schedule[year][week].append([id1, id2])
				for team in teams:
					if team.year == year:
						matchup = i.findAll('a') #info for opponents in list
						scores = i.findAll('td', {'class' : 'score'}) #scores for opponents in list					
						try:
							score0 = float(scores[0].get('title'))
							score1 = float(scores[1].get('title'))
						except:
							score0 = float(scores[0].text)
							score1 = float(scores[1].text)
						mov = score0 - score1 #only interested in margin of victory
						if team.name == matchup[0].text:
							if mov > 0: #if greater than 0, this is the winner
								team.wins[int(id1)-1] += 1 # place a 1 in the opponent ID spot in wins
							if float(scores[0].text) > 0:
								team.scores.append(float(score0))
								team.mov.append(round(mov, 1)) # add margin of victory
						if team.name == matchup[1].text:
							if mov < 0:
								team.wins[int(id2)-1] += 1
							if float(scores[1].text) > 0:
								team.scores.append(float(score1))
								team.mov.append(round(-mov, 1)) # add margin of victory

def main():
	print "Gathering Teams"
	years = history()
	gather_settings(years)
	gather_teams(years)
	gather_matchups(years)
	teams.sort(key=operator.attrgetter('year', 'division'), reverse = False)
	for i in settings:
		print "%s: %s" % (i,settings[i])
	for i in teams:
		#print "%s %s: %s scores, %s mov" % (i.year, i.owner, len(i.scores), len(i.mov))
		print ', '.join("%s: %s" % item for item in vars(i).items())
	for i in schedule:
		print "Season: %s" % i 
		print schedule[i]
if  __name__ =='__main__':main()

