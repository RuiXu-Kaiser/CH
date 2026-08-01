#!/usr/bin/env python

from __future__ import print_function

import requests
from optparse import OptionParser
import getpass
import re
import urllib3
from xlsxwriter import Workbook
try:
        from urllib.parse import quote
except ImportError:
        from urllib import pathname2url as quote
import os
import datetime
import sys
from json import dumps
from json import loads
import ipaddress
import socket

userName=os.getlogin()
logFile=open("/logs/bcn/api-actions.log","a")
now = datetime.datetime.now()
date=now.strftime("%Y-%m-%d %H:%M")

ipDict={}
aliasDict={}
genericDict={}
netDict={}
ipCommentDict={}
hostCommentDict={}
aliasCommentDict={}
genericCommentDict={}
blockDict={}

allList=['STATIC','RESERVED','DHCP_RESERVED','GATEWAY','DHCP_ALLOCATED']

with open("IP4Address.txt",'r') as fd:
	for lines in fd:
		#Load all IPs into ipDict dictionary
		lineDict=loads(lines)
		if "kpIPAddressComment" in lineDict['properties']:
			ipCommentDict[lineDict['properties']['address']]=lineDict['properties']['kpIPAddressComment']
		if lineDict['properties']['state'] in allList:
			ipDict[lineDict['properties']['address']]={'state':lineDict['properties']['state'],"mac":""}
			#if IP is DHCP_ALLOCATED add MAC address
			if lineDict['properties']['state']=='DHCP_ALLOCATED':
				mac={'mac':lineDict['properties']['macAddress']}
				ipDict[lineDict['properties']['address']].update(mac)
with open("IP6Address.txt","r") as fd:
	for lines in fd:
		#Load all static IPv6 into ipDict dictionary
		lineDict=loads(lines)
		if lineDict['properties']['state']=="STATIC":
			#use exploded form to get consistent v6 notation (BAM is inconsistent!)
			v6addr=ipaddress.IPv6Address(lineDict['properties']['address']).exploded
			ipDict[v6addr]={'state':lineDict['properties']['state'],"mac":""}
with open("AliasRecord.txt","r") as fd:
	for lines in fd:
		#Load all aliases into aliasDict dictionary
		lineDict=loads(lines)
		aliasDict[lineDict['properties']['absoluteName']]={'aliasFqdn':lineDict['properties']['absoluteName'],'linkedRecord':lineDict['properties']['linkedRecordName']}
		if "comments" in lineDict['properties']:
			aliasCommentDict[lineDict['properties']['absoluteName']]=lineDict['properties']['comments']
			#comment={'comment':lineDict['properties']['comments']}
			#aliasDict[lineDict['properties']['absoluteName']].update(comment)
with open("GenericRecord.txt","r") as fd:
	for lines in fd:
		#Load all Generic Records into genericDict dictionary
		lineDict=loads(lines)
		if "comments" in lineDict['properties']:
			genericCommentDict[lineDict['properties']['absoluteName']]=lineDict['properties']['comments']
		if lineDict['properties']['type']=="A" or  lineDict['properties']['type']=="AAAA":
			if not lineDict['properties']['absoluteName'] in genericDict:
				genericDict[lineDict['properties']['absoluteName']]={'addresses':lineDict['properties']['rdata']}
			else:
				addresses={'addresses':genericDict[lineDict['properties']['absoluteName']]['addresses']+","+lineDict['properties']['rdata']}
				genericDict[lineDict['properties']['absoluteName']].update(addresses)


#Host Records
with open("HostRecord.txt","r") as fd:
	for lines in fd:
		lineDict=loads(lines)
		if "comments" in lineDict['properties']:
			hostCommentDict[lineDict['properties']['absoluteName']]=lineDict['properties']['comments']
		#Handle HostRecords with no addresses
		if "addresses" in lineDict['properties']:
			#Handle HostRecords with multiple addresses
			if "," in lineDict['properties']['addresses']:
				addresses=lineDict['properties']['addresses'].split(",")
				for address in addresses:
					#handle IPv6
					if ":" in address:
						#use exploded form to get consistent v6 notation (BAM is inconsistent!)
						address=ipaddress.IPv6Address(address).exploded
					if address in ipDict:
						#Add hostRecord absolutename to ipDict dictionary key of IP address - handle IPs with multiple hostrecords
						if "hostFqdn" in ipDict[address]:
							hostFqdn={'hostFqdn':lineDict['properties']['absoluteName']+","+ipDict[address]['hostFqdn']}
							ipDict[address].update(hostFqdn)
						else:
							hostFqdn={'hostFqdn':lineDict['properties']['absoluteName']}
							ipDict[address].update(hostFqdn)
			else:
				#Host with single IP address
				if lineDict['properties']['addresses'] in ipDict:
					#handle IPv6
					if ":" in lineDict['properties']['addresses']:
						#use exploded form to get consistent v6 notation (BAM is inconsistent!)
						lineDict['properties']['addresses']=ipaddress.IPv6Address(lineDict['properties']['addresses']).exploded
					#Add hostRecord absoluteName to ipDict dictionary key of IP address - handle IPs with multiple hostrecords
					if "hostFqdn" in ipDict[lineDict['properties']['addresses']]:
						hostFqdn={'hostFqdn':lineDict['properties']['absoluteName']+","+ipDict[lineDict['properties']['addresses']]['hostFqdn']}
						ipDict[lineDict['properties']['addresses']].update(hostFqdn)
					else:
						hostFqdn={'hostFqdn':lineDict['properties']['absoluteName']}
						ipDict[lineDict['properties']['addresses']].update(hostFqdn)

#Networks
with open("IP4Network.txt","r") as fd:
	for lines in fd:
		lineDict=loads(lines)
		netDict[ipaddress.ip_network(lineDict['properties']['CIDR'])]={'name':lineDict.get('name'),'defaultDomains':lineDict.get('properties').get('defaultDomains'),'cafmAddress':lineDict.get('properties').get('kpCafmAddress'),'cafmBuildingId':lineDict.get('properties').get('kpCafmBuildingId'),'cafmBuildingName':lineDict.get('properties').get('kpCafmBuildingName'),'cafmCity':lineDict.get('properties').get('kpCafmCity'),'cafmLocationId':lineDict.get('properties').get('kpCafmLocationId'),'cafmLocationName':lineDict.get('properties').get('kpCafmLocationName'),'cafmSiteId':lineDict.get('properties').get('kpCafmSiteId'),'cafmState':lineDict.get('properties').get('kpCafmState'),'cafmZip':lineDict.get('properties').get('kpCafmZip'),'comment':lineDict.get('properties').get('kpComment'),'cafmNDECode':lineDict.get('properties').get('kpNdeCode')}
		if netDict[ipaddress.ip_network(lineDict['properties']['CIDR'])].get('defaultDomains') is not None:
			domainList=list(netDict[ipaddress.ip_network(lineDict['properties']['CIDR'])]['defaultDomains'].split(","))
			domainList=domainList[1::2]
			newDomainString=' '.join(domainList).replace('"','').replace(']','').replace(' ',',')
			newDomain={'defaultDomains':newDomainString}
			netDict[ipaddress.ip_network(lineDict['properties']['CIDR'])].update(newDomain)

#Blocks
with open("IP4Block.txt","r") as fd:
	for lines in fd:
		lineDict=loads(lines)
		blockDict[lineDict['properties']['CIDR']]={'name':lineDict.get('name'),"type":lineDict.get('type')}
		
		
staticList=['STATIC','RESERVED','DHCP_RESERVED','GATEWAY']

DnsFile=open("DnsRecords.txt","w")
CommentsFile=open("BlueCatComments.txt","w")
blockFile=open("blocks.txt","w")

#Static Hosts

ip6keys=[]
ip4keys=[]
for key in ipDict:
	if ":" in key:
		ip6keys.append(key)
	else:
		ip4keys.append(key)
		

#for key in sortedip4Keys:
#TIM ETL is looking for a "blank header line" so print one in DnsRecords.txt
DnsFile.write("\n")
for key in sorted(ip4keys,key= ipaddress.ip_address):
	#Treat STATIC, RESERVED, DHCP_RESERVED, GATEWAY all as "Static" in DnsRecords.txt file
	if ipDict[key]['state'] in staticList:
		#Skip allocated IPs with no dependent host record
		if "hostFqdn" in ipDict[key]:
			#Handle IPs with multiple HostRecords
			if "," in ipDict[key]['hostFqdn']:
				FQDN=ipDict[key]['hostFqdn'].split(",")
				for FQ in FQDN:
					#print("Static|",key,"|",FQ,"|",sep="")
					DnsFile.write("Static|"+key+"|"+FQ+"|\n")
			else:
				#print("Static|",key,"|",ipDict[key]['hostFqdn'],"|",sep="")
				DnsFile.write("Static|"+key+"|"+ipDict[key]['hostFqdn']+"|\n")

for key in sorted(ip6keys,key=ipaddress.ip_address):
	if "hostFqdn" in ipDict[key]:
		#Handle IPs with multiple HostRecords
		if "," in ipDict[key]['hostFqdn']:
			FQDN=ipDict[key]['hostFqdn'].split(",")
			for FQ in FQDN:
				#print("Static|",key,"|",FQ,"|",sep="")
				DnsFile.write("Static|"+key+"|"+FQ+"|\n")
		else:
			#print("Static|",key,"|",ipDict[key]['hostFqdn'],"|",sep="")
			DnsFile.write("Static|"+key+"|"+ipDict[key]['hostFqdn']+"|\n")

#Generic Hosts
for key in genericDict:
	if "," in genericDict[key]['addresses']:
		addresses=genericDict[key]['addresses'].split(",")
		for address in addresses:
			#print("Static|",address,"|",key,"|",sep="")
			DnsFile.write("Static|"+address+"|"+key+"|\n")
	else:
		#print("Static|",genericDict[key]['addresses'],"|",key,"|",sep="")
		DnsFile.write("Static|"+genericDict[key]['addresses']+"|"+key+"|\n")

#DHCP Allocated Hosts
for key in ipDict:
	if ipDict[key]['state']=="DHCP_ALLOCATED":
		try:
			#Handle IPs with multiple HostRecords
			if "," in ipDict[key]['hostFqdn']:
				FQDN=ipDict[key]['hostFqdn'].split(",")
				for FQ in FQDN:
					#print("DHCP|",key,"|",ipDict[key]['mac'].lower(),"|",FQ,sep="")
					DnsFile.write("DHCP|"+key+"|"+ipDict[key]['mac'].lower()+"|"+FQ+"\n")
			else:
				#print("DHCP|",key,"|",ipDict[key]['mac'].lower(),"|",ipDict[key]['hostFqdn'],sep="")
				DnsFile.write("DHCP|"+key+"|"+ipDict[key]['mac'].lower()+"|"+ipDict[key]['hostFqdn']+"\n")
		except KeyError:
			pass

#Aliases
for key in aliasDict:
	#print("CNAME|",key,"|",aliasDict[key]['linkedRecord'],"|",sep="")
	DnsFile.write("CNAME|"+key+"|"+aliasDict[key]['linkedRecord']+"|\n")

#Blocks

def f(x):
	if "/" in x:
		x,Cidr=x.split("/")
		x=ipaddress.ip_address(x)
	else:
		x=x.split(" ",1)
		x=ipaddress.ip_address(x[0])
	
	return(x)
	
#sortedBlockDict=sorted(blockDict.keys(), key=lambda ip: f(ip))
#for key in sortedBlockDict:
for key in sorted(blockDict.keys(), key=lambda ip: f(ip)):
	blockFile.write(key+"|"+blockDict[key]['type']+"|"+str(blockDict[key]['name'])+"|"+"\n")
	
#Comments
sortedipCommentDict=sorted(ipCommentDict.keys(),key=ipaddress.ip_address)
for key in sortedipCommentDict:
	CommentsFile.write(key+"|"+ipCommentDict[key]+"\n")
for key in hostCommentDict:
	CommentsFile.write(key+"|"+hostCommentDict[key]+"\n")
for key in aliasCommentDict:
	CommentsFile.write(key+"|"+aliasCommentDict[key]+"\n")
for key in genericCommentDict:
	CommentsFile.write(key+"|"+genericCommentDict[key]+"\n")

#Networks
CafmStuff=open("CafmStuff_10.0.0.0_255.255.255.255.txt","w")
#TIM ETL is looking for a "blank header line" so print one in CafmStuff_10.0.0.0_255.255.255.255.txt
CafmStuff.write("\n")

CafmStuffExcel=Workbook("CafmStuff_10.0.0.0_255.255.255.255.xlsx")
CafmStuffInteger=open("CafmStuffInteger.txt","w")
worksheet=CafmStuffExcel.add_worksheet()
columnNames=["Subnet Address","Subnet Description","Default Domain","CAFM Address","CAFM Building ID","CAFM Building Name","CAFM City","CAFM Location ID","CAFM Location Name","CAFM Site ID","CAFM State","CAFM Zip","Comment","NDE Code"]
row=0
column=-1
for header in columnNames:
	column+=1
	worksheet.write(0,column,header)

row=1
column=0
#Standard dictionaries are ordered as of python3.6 so we can rely on the ordering of the fields to be correct
for key in sorted(netDict):
	#print(key,"|",sep="",end="")
	subnetStartInt=int(key.network_address)
	subnetEndInt=int(key.broadcast_address)
	print(subnetStartInt,subnetEndInt,sep="|",end="",file=CafmStuffInteger)
	intFieldList=['defaultDomains','cafmAddress','cafmBuildingId','cafmBuildingName','cafmCity','cafmLocationId','cafmLocationName','cafmSiteId','cafmState','cafmZip','comment','cafmNDECode','name']
	for field in intFieldList:
		if netDict[key][field] is None:
			print("|",file=CafmStuffInteger,end="")
		else:
			print("|"+netDict[key][field].replace("|","-"),end="",file=CafmStuffInteger)
	print("|",file=CafmStuffInteger)
	CafmStuff.write(str(key)+"|")
	worksheet.write(row,column,str(key))
	column+=1
	for key2,value in netDict[key].items():
		if value is None:
			#print("|",sep="",end="")
			CafmStuff.write("|")
			worksheet.write(row,column,"")
			column+=1
		else:
			#print(value,"|",sep="",end="")
			CafmStuff.write(value.replace("|","-")+"|")
			worksheet.write(row,column,value.replace("|","-"))
			column+=1
	#print()
	CafmStuff.write("\n")
	row+=1
	column=0
	
CafmStuffExcel.close()
CafmStuff.close()
CafmStuffInteger.close()
DnsFile.close()
#print(zoneObject.json())
#logFile.write("%s %s Added DNS Zone %s on %s in %s configuration\n" % (date,userName,options.zoneName,options.BAMAddress,config_name))
#props = dict(item.split("=",1) for item in hostRecord["properties"].rstrip("|").split("|"))

# logout of api session
