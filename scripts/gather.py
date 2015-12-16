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
        for i in soup.findAll('tr', {'class' : 'evenRow bodyCopy sortableRow'}):
		print i.find('td', {'class': 'sortablePF'}).text
		print i.find('td', {'class': 'sortablePA'}).text
		print i.find('td', {'class': 'sortableDIV'}).text
		quit()
                parsed = urlparse.urlparse(i.a['href']) #parse url parameters
                id = urlparse.parse_qs(parsed.query)['teamId'][0]
                name = i.a.text
                teams.append(TeamID(name,int(id)))
		print "%s %s" % (id, name)
	for i in soup.findAll('tr', {'class' : 'oddRow bodyCopy sortableRow'}):
                parsed = urlparse.urlparse(i.a['href']) #parse url parameters
                id = urlparse.parse_qs(parsed.query)['teamId'][0]
                name = i.a.text
                teams.append(TeamID(name,int(id)))
                print "%s %s" % (id, name)


def main():
	print "Gathering Teams"
	gather_teams()
if  __name__ =='__main__':main()

