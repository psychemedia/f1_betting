from __future__ import division
import scraperwiki
#nodrop - 0 if you want to drop, 1 if you don't
nodrop=1

bets=['constructors-championship','drivers-championship']
bookies=['LD','B3','WH','SK','BX','FR']

path='http://www.oddschecker.com/'
stub='motorsport/formula-one/'

import requests
import datetime
from time import sleep
from bs4 import BeautifulSoup

def dropper(table):
    """ Helper function to drop a table """
    if nodrop==1: return
    print "dropping",table
    if table!='':
        try: scraperwiki.sqlite.execute('drop table "'+table+'"')
        except: pass
        
def makeSoup(url):
	try:
		r = requests.get(url)
		#print '>>>',r.history
		ret= BeautifulSoup(r.text)
		for s in r.history:
			if s.status_code==302: ret==""
	except: ret=""
	return ret

def oddsGrabber(soup,default):
  if soup=="": return {}
  #soup=makeSoup(url)
  table=soup.find( "tbody", {"id":"t1"} )
  allbets=default
  allbets['time']=datetime.datetime.utcnow()
  bets={}
  for row in table.findAll('tr'):
    name=row('td')[1].string
    tds = row('td')[3:]
    bets[name]={}
    for td in tds:
      if td.string!=None:
        try:
          bets[name][ td['id'].split('_')[1] ]=td.string
        except: pass
  allbets['odds']=bets
  return allbets


def urlbuilder_generic(path,stub,bet):
  return {0}/{1}/{2}'.format(path.strip('/'),stub.strip('/'),bet)

def oddsGrabber_generic(url,default):
  soup=makeSoup(url)
  if soup=='':
    return {}
  return oddsGrabber(soup,default)

def oddsParser_generic(odds,bookies=[]):
  bigodds=[]
  oddsdata=odds['odds']
  for outcome in oddsdata:
    #data in tidy format
    data={'time':odds['time']}
    for bookie in oddsdata[outcome]:
      if bookies==[] or bookie in bookies:
      	data['outcome']=str(outcome)
      	data['bookie']=str(bookie)
      	data['oddsraw']=str(oddsdata[outcome][bookie])
      	try:
      		data['odds']=eval(str(data['oddsraw']))
      		data['decodds']=1.0+data['odds']
      		bigodds.append(data.copy()) 
      	except: pass
      	
  return bigodds

def tableCheck(table):
  dropper(table)
  scraperwiki.sqlite.execute("CREATE TABLE IF NOT EXISTS '{table}' (  'time' datetime , \
                                                                      'bookie' text, \
                                                                      'outcome' text, \
                                                                      'odds' real, \
                                                                      'oddsraw' text, \
                                                                      'decodds' real   )".format(table=table))

playnice=0.1

def scraper(path,stub,bets,bookies):
  for bet in bets:
    tableCheck(bet)
    url=urlbuilder_generic(path, stub, bet)
    odds=oddsGrabber_generic(url,{})
    oddsdata=oddsParser_generic(odds,bookies)
    scraperwiki.sqlite.save(unique_keys=[],table_name=bet, data=oddsdata)
    sleep(playnice)
 



scraper(path,stub,bets,bookies)


