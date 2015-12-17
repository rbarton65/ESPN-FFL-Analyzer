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
settings={"League Name": None, "Number of Teams": None, "Regular Season Matchups": None, "Playoff Teams": None, "Playoff Seeding Tie Breaker": None}
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
		self.wins = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]
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

def gather_settings(settings):
	"""Gathers league settings"""
	url = "http://games.espn.go.com/ffl/leaguesetup/settings?leagueId=%s" % (args.league)
        ourUrl = opener.open(url).read()
        soup = BeautifulSoup(ourUrl)
	for setting in settings:
		for i in soup.findAll('td', {'class' : 'settingLabel'}):
			if setting == i.text:
				settings[setting] = i.findNext('td').text
	settings["Playoff Teams"] = settings["Playoff Teams"].split()[0]
	settings["Regular Season Matchups"] = settings["Regular Season Matchups"].split()[0]
	return settings

def gather_matchups(week, years):
	"""Gathers matchups, wins, scores for each team"""
	for year in years:
		url = "http://games.espn.go.com/ffl/scoreboard?leagueId=288077&matchupPeriodId=%s&seasonId=%s" % (week, year)
        	ourUrl = opener.open(url).read()
	        soup = BeautifulSoup(ourUrl)
        	for i in soup.findAll('table', {'class' : 'ptsBased matchup'}):
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
                                	        	parsed = urlparse.urlparse(i.findAll('a')[1]['href']) #parse url parameters
		                                        id = urlparse.parse_qs(parsed.query)['teamId'][0] # find opponents ID
	        	                                team.wins[int(id)-1] += 1 # place a 1 in the opponent ID spot in wins
                        	        	if float(scores[0].text) > 0:
                                	        	team.scores.append(float(score0))
		                                        team.mov.append(round(mov, 1)) # add margin of victory
                		        if team.name == matchup[1].text:
                                		if mov < 0:
		                                        parsed = urlparse.urlparse(i.findAll('a')[0]['href']) #parse url parameters
                		                        id = urlparse.parse_qs(parsed.query)['teamId'][0]
                                		        team.wins[int(id)-1] += 1
		                                if float(scores[1].text) > 0:
                		                        team.scores.append(float(score1))
                                		        team.mov.append(round(-mov, 1)) # add margin of victory

def main():
	print "Gathering Teams"
	gather_settings(settings)
	years = history()
	gather_teams(years)
	for matchup in range(1,int(settings["Regular Season Matchups"])):
		gather_matchups(matchup, years)
	teams.sort(key=operator.attrgetter('year', 'division'), reverse = False)
	for i in settings:
		print "%s: %s" % (i,settings[i])
	for i in teams:
		print ', '.join("%s: %s" % item for item in vars(i).items())
if  __name__ =='__main__':main()

