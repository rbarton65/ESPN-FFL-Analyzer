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
		id = urlparse.parse_qs(parsed.query)['teamId'][0]
		name = i.a.text
		teams.append(TeamID(name,int(id)))

def matchups(week):
#	print "Week %s" % week
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

def square_matrix(X):
	result = numpy.zeros(shape=(len(X), len(X[0])))
	# iterate through rows of X
	for i in range(len(X)):
	   # iterate through columns of X
	   for j in range(len(X[0])):
		   # iterate through rows of X
		   for k in range(len(X)):
			   result[i][j] += X[i][k] * X[k][j]
	return result

def add_matrix(X,Y):
	result = numpy.zeros(shape=(len(X), len(X[0])))
	for i in range(len(X)):
   # iterate through columns
	   for j in range(len(X[0])):
		   result[i][j] = X[i][j] + Y[i][j]
	return result

def formula_calc():
	matrix = []
	for i in teams:
		matrix.append(i.wins)
	matrix2 = square_matrix(matrix)
	result = add_matrix(matrix, matrix2)
	return result

def main():
	startTime = datetime.now()
	print "Gathering teams"
	gather_teams()
	week = int(args.week)
	nums = []
	if week > 1:
		for i in range(1,week):
			matchups(i)
		teams.sort(key=operator.attrgetter('ID'), reverse = False)
		final_matrix = formula_calc()
		for i,j in zip(final_matrix, teams):
			j.pr= round(float(sum(i)*0.8) + float((sum(j.scores)/len(j.scores)*0.15)) + float((sum(j.mov)/len(j.mov)*0.05)), 2)
		teams.sort(key=operator.attrgetter('pr'), reverse = True)
	
		for standing, i in enumerate(teams):
			i.previous = standing+1

	matchups(week)
	teams.sort(key=operator.attrgetter('ID'), reverse = False)
        final_matrix = formula_calc()
        for i,j in zip(final_matrix, teams):
		j.pr= round(float(sum(i)*0.8) + float((sum(j.scores)/len(j.scores)*0.15)) + float((sum(j.mov)/len(j.mov)*0.05)), 2)
	
	teams.sort(key=operator.attrgetter('pr'), reverse = True)

	for standing, i in enumerate(teams):
		i.current = standing+1
		i.position = i.previous-i.current

	print "----------------------------------\nWEEK %s POWER RANKINGS\n----------------------------------" % args.week
	for j,i in enumerate(teams):
		if week > 1:
			if i.position > 0:
				print "%s %s (%s-%s): %s [+%s]" % (j+1, i.name, sum(i.wins), (week-sum(i.wins)), i.pr, i.position)
			elif i.position == 0:
				print "%s %s (%s-%s): %s [--]" % (j+1, i.name, sum(i.wins), (week-sum(i.wins)), i.pr)
			else:
				print "%s %s (%s-%s): %s [%s]" % (j+1, i.name, sum(i.wins), (week-sum(i.wins)), i.pr, i.position)
		else:
			print "%s %s (%s-%s): %s" % (j+1, i.name, sum(i.wins), (week-sum(i.wins)), i.pr)
	print "----------------------------------"
	print "Total time to execute: %s" % (datetime.now()-startTime)


if  __name__ =='__main__':main()
