import requests
import re
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. Configuration variables
BAM_IP = "enterprise-bam3.test.kp.org"  # Replace with your Address Manager IP or hostname
USERNAME = "Y912052"
PASSWORD = "4RecrUth1984"
config_name="KP"
viewName="default"
ObjectType = "IP4Address"
start=0
toGrab=5000000

bamurl=re.sub(r"\.$", "", BAM_IP)
url = "https://"+bamurl+"/Services/REST/v1/"
loginurl = url+"login?username="+USERNAME+"&password="+PASSWORD

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

selectCriteria=str({"selector":"get_entitytree","startEntityId":startPoint,"types":ObjectType,"children_only":"false"})
exportEntitiesParams={"start":start,"count":toGrab,"selectCriteria":selectCriteria}
exportEntities=requests.get(url+"exportEntities?",headers=header,params=exportEntitiesParams,stream=True)
exportEntities.raise_for_status
print("Headers are:",exportEntities.headers)

requests.get(url+"logout?",headers=header)