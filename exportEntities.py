#!/usr/bin/env python
from __future__ import print_function

import requests
from optparse import OptionParser
import getpass
import re
import urllib3
try:
        from urllib.parse import quote
except ImportError:
        from urllib import pathname2url as quote
import os
import datetime
import sys
sys.path.append(os.path.abspath("/usr/local/bin"))
from common import *

#Parameters
#config_name="KP"
viewName="default"
start=0
toGrab=5000000
count = toGrab
userName=os.getlogin()
logFile=open("C:\\Users\\Y912052\\logs\\bcn\\api-actions.log","a")
now = datetime.datetime.now()
date=now.strftime("%Y-%m-%d %H:%M")

#Command line options
usage = "Usage: %prog -n [BAM Hostname] -u [BAM UserID] -t [Object Type] -s [Search String] -m [Select mode: search or tree] [-e]"
parser = OptionParser(usage=usage)
parser.add_option("-u", dest="account", help="BAM UserID")
#parser.add_option("-p", dest="account_password", help="BAM Password")
parser.add_option("-n", dest="BAMAddress", help="BAM Hostname")
parser.add_option("-t", dest="objectType", help="Object Type")
parser.add_option("-s", dest="searchString", help="Search String (when -m is search)")
parser.add_option("-m", dest="selectMode", help="Select mode: search or tree")
parser.add_option("-e", action="store_true", dest="external", help="Run in KP-External")
(options, args) = parser.parse_args()
if not (options.account and options.BAMAddress and options.objectType and options.selectMode):
	parser.print_help()
	sys.exit()

account_password="4RecrUth1984"

if ( options.external ):
        config_name="KP-External"
else:
        config_name="KP"

BAMAddress=re.sub(r"\.$","",options.BAMAddress)

bamurl = re.sub(r"\.$", "", options.BAMAddress)
url = "https://"+bamurl+"/Services/REST/v1/"
password=quote(account_password.encode())
loginurl = url+"login?username="+options.account+"&password="+password


#login to api session
try:
	response = requests.get(loginurl)
	response.raise_for_status()
except requests.exceptions.HTTPError as error:
	print("Please check your password and try again")
	sys.exit()

# get the Token and put it into a variable
token = str(response.json())
token = token.split()[2]+" "+token.split()[3]
# set header value for the next methods
header={'Authorization':token,'Content-Type':'application/json'}


configInfoParams={"name":config_name,"parentId":"0","type":"Configuration"}
configInfo=requests.get(url+"getEntityByName?",headers=header,params=configInfoParams).json()
viewInfoParams={"name":viewName,"parentId":configInfo["id"],"type":"View"}
viewInfo=requests.get(url+"getEntityByName?",headers=header,params=viewInfoParams).json()

startPoint=configInfo["id"]

count=toGrab
while count == toGrab:
	try:
		if options.selectMode == "search":
			selectCriteria=str({"selector":"search","types":options.objectType,"keyword":options.searchString})
			
		if options.selectMode == "tree":
			selectCriteria=str({"selector":"get_entitytree","startEntityId":startPoint,"types":options.objectType,"children_only":"false"})
		exportEntitiesParams={"start":start,"count":toGrab,"selectCriteria":selectCriteria}
		exportEntities=requests.get(url+"exportEntities?",headers=header,params=exportEntitiesParams,stream=True)
		exportEntities.raise_for_status
		#print("Headers are:",exportEntities.headers)
		fetchedLines=0
		if options.selectMode == "search":
			for lines in exportEntities.iter_lines():
				print((lines.decode('utf-8')+"\n"))
				fetchedLines+=1
		else:
			with open(options.objectType + ".txt",'w') as fd:
				for lines in exportEntities.iter_lines():
					fd.write((lines.decode('utf-8')+"\n"))
					fetchedLines+=1
	except requests.exceptions.HTTPError as error:
		print(error)
		print(error.response.text)
		requests.get(url+"logout?",headers=header)
		sys.exit()
	count=fetchedLines
	#print("Count is",count)
	start+=toGrab
	#print("Start is",start)

#print(zoneObject.json())
#logFile.write("%s %s Added DNS Zone %s on %s in %s configuration\n" % (date,userName,options.zoneName,options.BAMAddress,config_name))
#props = dict(item.split("=",1) for item in hostRecord["properties"].rstrip("|").split("|"))

# logout of api session
requests.get(url+"logout?",headers=header)
