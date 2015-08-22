from __future__ import division
import scraperwiki
import mechanize

from lxml import html

#nodrop - 0 if you want to drop, 1 if you don't
nodrop=1

racebets=['belgian-grand-prix/winner']
seasonbets=['constructors-championship','drivers-championship']

bets={'racebets':racebets, 'seasonbets':seasonbets}

bookies=['LD','B3','WH','SK','BX','FR','PP','EE']

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
		br = mechanize.Browser()
		#print '>>>',r.history
		r=br.open(url)
		#ret= BeautifulSoup(r.read())
		ret=html.fromstring(r.read())
		if r.code==302: ret==""
	except: ret=""
	return ret
	
def makeSoup2(url):
	try:
		r = requests.get(url)
		#print '>>>',r.history
		ret= BeautifulSoup(r.text)
		for s in r.history:
			if s.status_code==302: ret==""
	except: ret=""
	return ret

def oddsGrabber(tree,default=None):
    if default is None: allbets={}
    else: allbets=default
    allbets['time']=datetime.datetime.utcnow()
    bets={}
    allbets['odds']=bets
  
    if tree=="" or tree is None: return allbets

    for row in tree.xpath('//tbody[@id="t1"]/tr'):
        name=row[1].text
        bets[name]={}
        for cell in row[3:]:
            if cell.text is not None:
                try:
                    bets[name][ cell.get('id').split('_')[1] ]=cell.text
                except: pass
    allbets['odds']=bets
    #print(allbets)
    return allbets
    
def oddsGrabber2(soup):
  allbets={}
  allbets['time']=datetime.datetime.utcnow()
  bets={}
  allbets['odds']=bets
  
  if soup=="": return allbets

  table=soup.find( "tbody", {"id":"t1"} )
  if table is None: return allbets

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
  return '{0}/{1}/{2}'.format(path.strip('/'),stub.strip('/'),bet)

def oddsGrabber_generic(url):
	soup=makeSoup(url)
	if soup=='':
		return {}
	return oddsGrabber(soup)

def oddsParser_generic(odds,bookies=[],default=None):
  if default is None: default={}
  if 'odds' not in odds: return []
  bigodds=[]
  oddsdata=odds['odds']
  for outcome in oddsdata:
    #data in tidy format
    data=default.copy()
    data['time']=odds['time']
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

def tableCheck(table,base=None):
	if base is None: base=[]
	dropper(table)
	base=base+[ \
			('time','datetime'), \
			('bookie','text'), \
			('outcome','text'), \
			('odds', 'real'), \
			('oddsraw','text'), \
			('decodds', 'real') 	]
	fields=', '.join([' '.join( map(str,item) ) for item in base ])
  	tabledef="CREATE TABLE IF NOT EXISTS '{table}' ( {fields} )".format(table=table,fields=fields)
  	scraperwiki.sqlite.execute( tabledef )

playnice=2.0

def betgrabber(path,stub,bet,bookies,default=None):
	if default is None: default={'def':[],'entry':{},'table':bet}
	table=default['table']
	
	tableCheck(table,default['def'])
	
	url=urlbuilder_generic(path, stub, bet)
	odds=oddsGrabber_generic(url)
	oddsdata=oddsParser_generic(odds,bookies,default['entry'])
	print('Adding {} rows for {}'.format(len(oddsdata),bet))
	scraperwiki.sqlite.save(unique_keys=[],table_name=table, data=oddsdata)
	sleep(playnice)
    
def scraper(path,stub,bets,bookies):
	for bet in bets['seasonbets']:
		betgrabber(path,stub,bet,bookies)
	
	for bet in bets['racebets']:
		race=bet.split('/')[0]
		typ=bet.split('/')[1]
		racedefault={'table':race,'def':[('typ','text')],'entry':{'typ':typ}}
		betgrabber(path,stub,bet,bookies,racedefault)

 



scraper(path,stub,bets,bookies)


