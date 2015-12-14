import random
from __future__ import division
import urllib2
import urlparse
import numpy
import argparse
import operator
from datetime import datetime
from multiprocessing import Pool
from bs4 import BeautifulSoup

parser = argparse.ArgumentParser()
parser.add_argument("-l", "--league", help="ESPN league ID", required=True)
parser.add_argument("-w","--week", help="power ranking for this week", required=True)
parser.add_argument("-y","--year", help="power ranking for this year", required=True)
args = parser.parse_args()

opener = urllib2.build_opener()
opener.addheaders = [('User-agent', 'Mozilla/5.0')]
teams=[]

class TeamID:
	def __init__(self, name, ID):
			self.name = name
			self.ID = ID
			self.wins = [0,0,0,0,0,0,0,0,0,0,0,0,0,0]
			self.mov = []
			self.mova = None
			self.scores = []
			self.previous = 0
			self.current = 0
			self.position = None
			self.pr = None

def gather_teams():
	"""Gathers team names and ID numbers in the specified league"""
	url = "http://games.espn.go.com/ffl/standings?leagueId=%s&seasonId=%s" % (args.league, args.year)
	ourUrl = opener.open(url).read()
	soup = BeautifulSoup(ourUrl)
	for i in soup.findAll('tr', {'class' : 'tableBody'}):
		parsed = urlparse.urlparse(i.a['href']) #parse url parameters

def matchups(week):
	url = "http://games.espn.go.com/ffl/scoreboard?leagueId=%s&matchupPeriodId=%s&seasonId=%s" % (args.league, week, args.year)
	ourUrl = opener.open(url).read()
	soup = BeautifulSoup(ourUrl)
	for i in soup.findAll('table', {'class' : 'ptsBased matchup'}):
		for team in teams:
			matchup = i.findAll('a') #info for opponents in list
			scores = i.findAll('td', {'class' : 'score'}) #scores for opponents in list
			mov = (float(scores[0].get('title')) - float(scores[1].get('title'))) #only interested in margin of victory
			if team.name == matchup[0].text:
				if mov > 0: #if greater than 0, this is the winner
					parsed = urlparse.urlparse(i.findAll('a')[1]['href']) #parse url parameters
					id = urlparse.parse_qs(parsed.query)['teamId'][0] # find opponents ID
					team.wins[int(id)-1] += 1 # place a 1 in the opponent ID spot in wins
				team.mov.append(round(mov, 1)) # add margin of victory
				team.scores.append(float(scores[0].get('title')))
			if team.name == matchup[1].text:
				if mov < 0:
					parsed = urlparse.urlparse(i.findAll('a')[0]['href']) #parse url parameters
					id = urlparse.parse_qs(parsed.query)['teamId'][0]
					team.wins[int(id)-1] += 1
				team.mov.append(round(-(mov), 1))
				team.scores.append(float(scores[1].get('title')))

def main():
	print "Gathering Teams"
	gather_teams()
	week = int(arg.week)
	for i in range(1,week+1):
		matchups(i)
