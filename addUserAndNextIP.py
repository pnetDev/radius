#!/usr/bin/python



"""
 CM 04-11-2019 This code does the following.
 When the script is ran you are prompted for the customer ID and a password.
 The script then finds the next free managment and public IP addresses which can be allocated to a PPPoE users.
 PPPoE Shared Neworks are named as follows:
 white.cam.pnet
 johnswell.cam.pnet
 balling.cam.pnet
 
 These will be declared in dhcpd.conf on 10.1.1.75 but no pool will be allocated.
 Once a public IP has been assigned to a user the Leased field in IPAM is set to 'PPPoE-User'. This means the IP can't be used again.
 The user is then generated on the radius database on 10.1.1.24.
 The config file is also written to the configFile directory and this can be uploaded to the SM. 
 Onnce a private IP has been assigned for managment the availble field in cambiumMagementSubnets is set to 'No'

 SQL QUERIES:
 add user to radcheck and radreply
 "insert into radcheck (username,attribute,op,value) values('$ID', 'Cleartext-Password',':=', '$PASSWORD')"
 "insert into radreply (username,attribute,op,value) values('$ID', 'Framed-IP-Address', ':=', '$IP')"

 Find next free IP address:
 SELECT IPADDR from IPAM where sharedNetwork = "<$network>" and Leased = "NotLeased" and TYPE <> 'Reserved' limit 1;
 
 Python Update Example
 "UPDATE IPAM SET LEASED ='PPPoE-USER', TYPE=%s WHERE IPADDR = %s" , ("PPPoE-USER",IP))
 
 Using Variables:
 sql = "select MAC, IPADDR from IPAM where MAC='" + MAC + "'  and TYPE = 'Static' and LEASED ='Yes';"

 Log Changes here

 200203 Rewrite, using better use of functions. 
 200121 This script will also generate school config file is school option is selected.
 200107 This script will also generate a config file which can be uploaded to the SM. Configs are in Cambium directory. 
 191231 Need to ask the operator if it is a school. If so the PPPoE creds are not needed.
 191212 Now we also generate the mgnt IP address for the network area.
 191206 Logic problem an IP already assigned could be assigned again adding TYPE <> 'PPPoE-USER'to the mySQL query solves this.
 191106 Made more visually appealing for the operator.
 191106 Fixed bug, wrong sql query was being called in the IPAM verification section. 
 191104	New code.
"""

import MySQLdb
import math
import re
import subprocess
import datetime
import string
import random

now = datetime.date.today()
currDate = str(now)
currDate = currDate.replace('-', '')
currDate = str(currDate)

#---------------------------------------------------------------------#

def yes_or_no(question):
    reply = str(raw_input(question+' (y/n): ')).lower().strip()
    if reply[0] == 'y':
        return True
    if reply[0] == 'n':
        return False
    else:
        return yes_or_no("please enter ")

def pass_generator(size=12, chars=string.ascii_letters + string.digits):	
	return ''.join(random.choice(chars) for _ in range(size))

def findNetworkArea():
	## Get information from the operator.
	print ""
	print ""
	print "Select Network Area"
	print "-------------------"
	print "1.       WhiteMountain"
	print "2.       Johnswell"
	print "3.       Ballingarry"
	print ""
	choice = input("Enter your choice: ")
	print "You chose",choice
	if choice == 1:
        	sharedNetwork="white.cam.pnet"
        	realm="@white.pnet.cam.net"
	if choice == 2:
        	realm="@johnswell.pnet.cam.net"
        	sharedNetwork="johnswell.cam.pnet"
	if choice == 3:
        	realm="@balling.pnet.cam.net"
        	sharedNetwork="balling.cam.pnet"

	print "Choice",choice, sharedNetwork

	result = yes_or_no("Do you wish to Continue")
	if result == False:
        	print "Exiting."
        	quit ()
	return sharedNetwork, realm

def getNextManIP(sharedNetwork):
	## Getting next available MNGT IP address.
	#print "Finding ManIP for", sharedNetwork
	dbRadius = MySQLdb.connect("localhost","radius","D0xl1nk$","radius" )
	cur = dbRadius.cursor()
	sql="select ipaddr from cambiumMngtSubnets where network = '" + sharedNetwork + "' and available='Yes' limit 1;"
	RESULT = cur.execute(sql)
	if RESULT == 0:
        	print "No MNGT IP AVAILABLE. Contact Engineering."
        	quit ()
	for result in cur.fetchall():
        	print
        	manIP = result[0]
	print  manIP, " ManIP for", sharedNetwork
	return manIP

def generateSchoolConfig(sharedNetwork,manIP,custID):
	#print "This is generateSchoolConfig."
        ##### Generate School Config File
        if sharedNetwork == 'white.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName='PMP450-School ' + site + "-145" + "-" + custID
                naptRFPublicIP=manIP
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.cfg'
                print siteName, naptRFPublicIP
                replacements = {'changeSiteName':siteName, '10.1.55.254':naptRFPublicIP}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/PMP450-School.generic-146Pri.145Sec.cfg') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated.'
                print ""
                print ""

        if sharedNetwork == 'balling.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName="F300-School " + custID + " " + site
                mgmtIFIPAddr=manIP
                systemConfigDeviceName=siteName
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.json'
                print siteName, mgmtIFIPAddr, systemConfigDeviceName
                replacements = {'changeSiteName':siteName, '10.1.52.254':mgmtIFIPAddr}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/F300-School.Balllingarry-generic.json') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated.'
                print ""
                print ""

        if sharedNetwork == 'johnswell.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName="F300-School " + custID + " " + site
                mgmtIFIPAddr=manIP
                systemConfigDeviceName=siteName
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.json'
                print mgmtIFIPAddr, systemConfigDeviceName
                replacements = {'changeSiteName':siteName, '10.1.58.254':mgmtIFIPAddr}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/F300-School.Johnswell-generic.json') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated'
                print ""
                print ""

def generateResidentialConfig(sharedNetwork,manIP,userName,password):
	#print "PASSED VARIABLES ",sharedNetwork,manIP,userName,password
        if sharedNetwork == 'white.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName='PMP450-' + site + "-145" + "-" + custID
                pppoeUserName=userName
                networkWanPPPoEPassword=password
                naptRFPublicIP=manIP
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.cfg'
                print siteName, naptRFPublicIP, pppoeUserName, networkWanPPPoEPassword
                replacements = {'changeSiteName':siteName, 'changeMe@white.pnet.cam.net':pppoeUserName, 'changeMePppoePassword':networkWanPPPoEPassword, '10.1.55.254':naptRFPublicIP}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/PMP450-generic.cfg') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated.'
                print ""
                print ""

        if sharedNetwork == 'balling.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName="F300-" + custID + " " + site
                networkWanPPPoEUsername=userName
                networkWanPPPoEPassword=password
                mgmtIFIPAddr=manIP
                systemConfigDeviceName=siteName
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.json'
                print siteName, networkWanPPPoEUsername, networkWanPPPoEPassword, mgmtIFIPAddr, systemConfigDeviceName
                replacements = {'changeSiteName':siteName, 'changeMe@balling.pnet.cam.net':networkWanPPPoEUsername, 'pppoePassword':networkWanPPPoEPassword, '10.1.52.254':mgmtIFIPAddr}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/F300-Balling-generic.json') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated.'
                print ""
                print ""

        if sharedNetwork == 'johnswell.cam.pnet':
                site=sharedNetwork.split('.')[0]
                print "Generating Config File with these settings."
                siteName="F300-" + custID + " " + site
                networkWanPPPoEUsername=userName
                networkWanPPPoEPassword=password
                mgmtIFIPAddr=manIP
                systemConfigDeviceName=siteName
                configFileName='/pnetadmin/RADIUS_ADMIN/configFiles/' + custID + '.json'
                print networkWanPPPoEUsername, networkWanPPPoEPassword, mgmtIFIPAddr, systemConfigDeviceName
                replacements = {'changeSiteName':siteName, 'changeMe@johnswell.pnet.cam.net':networkWanPPPoEUsername, 'pppoePassword':networkWanPPPoEPassword, '10.1.58.254':mgmtIFIPAddr}
                with open('/pnetadmin/RADIUS_ADMIN/configFiles/F300-Johnswell-generic.json') as infile, open(configFileName, 'w') as outfile:
                        for line in infile:
                                for src, target in replacements.iteritems():
                                        line = line.replace(src, target)
                                outfile.write(line)
                print configFileName + ' generated'
                print ""
                print ""
	return siteName

def getNextPubIP(sharedNetwork):
	dbIPAM = MySQLdb.connect("10.1.1.51","ipam","ipam$2o18$","docsis" )
	cur = dbIPAM.cursor()
	sql = "select IPADDR, SharedNetwork from IPAM where SharedNetwork='" + sharedNetwork + "'  and LEASED = 'NotLeased' and TYPE <> 'Reserved' and TYPE <> 'PPPoE-USER' limit 1;"
	RESULT = cur.execute(sql)
	if RESULT == 0:
        	print sharedNetwork, "NO PUBLIC IP AVAILABLE. Contact Engineering."
        	quit ()

	for result in cur.fetchall():
        	IP = result[0]
		return IP

def updateRadiusSchool(custID,manIP):
	#print "updateRadiusSchool Passed Variables", custID, manIP
	dbRadius = MySQLdb.connect("localhost","radius","D0xl1nk$","radius" )
	cur = dbRadius.cursor()
	#print "SQL UPDATE cambiumMngtSubnets SET available = %s, custid = %s WHERE ipaddr = %s (no)" ,custID,manIP
	cur.execute("UPDATE cambiumMngtSubnets SET available = %s, custid = %s WHERE ipaddr = %s" , ("No",custID,manIP))
	dbRadius.commit()
	dbRadius.close()

def updateRadiusResidential(custID,userName,password,manIP,publicIP):
	#print "updateRadius Passed Variables", custID,userName,password,manIP,publicIP
	dbRadius = MySQLdb.connect("localhost","radius","D0xl1nk$","radius" )
	cur = dbRadius.cursor()
	try:
		cur.execute("insert into radcheck (username,attribute,op,value) values (%s,%s,%s,%s)" , (userName,'Cleartext-Password',':=',password))
		cur.execute("insert into radreply (username,attribute,op,value) values (%s,%s,%s,%s)" , (userName,'Framed-IP-Address',':=',publicIP))
		#cur.execute("UPDATE cambiumMngtSubnets SET available = %s, custid = %s WHERE ipaddr = %s" , ("No",custID,manIP))
		dbRadius.commit
		updateID = "SELECT id FROM radcheck where username = '" + str(userName) + "';"
		cur.execute(updateID)
		for result in  cur.fetchall():
        		radcheck_id=result[0]
		print "radcheck_id is ",radcheck_id
		cur.execute("UPDATE cambiumMngtSubnets SET available = %s, custid = %s, radcheck_id = %s  WHERE ipaddr = %s" , ("No",custID,radcheck_id,manIP))
		dbRadius.commit()
		dbRadius.close()	
	except:
        	print "Unable to create credentials " + userName + " already exists check getppp."
         	print ""
         	quit ()

def updateIpam(publicIP):
	dbIPAM = MySQLdb.connect("10.1.1.51","ipam","ipam$2o18$","docsis" )
	cur = dbIPAM.cursor()	
	cur.execute("UPDATE IPAM SET LEASED ='PPPoE-USER', TYPE=%s WHERE IPADDR = %s" , ("PPPoE-USER",publicIP))
	dbIPAM.commit()
	dbIPAM.close()

def readBack(publicIP,userName):
	# Verificiation
	print ""
	print "The following details have been read back from the databases, check the details are correct."
	print "--------------------------------------------------------------------------------------------"
	print

	## Readback from IPAM.
	db = MySQLdb.connect("10.1.1.51","ipam","ipam$2o18$","docsis" )
	cur = db.cursor()
	sqlRadcheck = "SELECT IPADDR, LEASED, TYPE from IPAM where IPADDR = '" + str(publicIP) + "';"
	print "READ FROM IPAM on 10.1.1.51"
	print "---------------------------"
	cur.execute(sqlRadcheck)
	for result in  cur.fetchall():
        	ipaddr=result[0]
        	type=result[1]

	print ipaddr, type

	print ""
	db.close()

	## Readback from radius.

	print "READ FROM radius on 10.1.1.24"
	print "-----------------------------"

	dbRadius = MySQLdb.connect("localhost","radius","D0xl1nk$","radius" )
	cur = dbRadius.cursor()
	sqlRadcheck = "SELECT * FROM radcheck where username = '" + str(userName) + "';"
	sqlRadreply = "SELECT * FROM radreply where username = '" + str(userName) + "';"
	cur.execute(sqlRadcheck)

	for result in cur.fetchall():
        	username=result[1]
        	password=result[4]

	cur.execute(sqlRadreply)

	for result in cur.fetchall():
        	ipAddrr=result[4]

	print ""
	print "PPPoE USERNAME: " + username
	print "PPPoE PASSWORD: " + password
	print "PUBLIC IP ADDRESS: " + ipAddrr
	print "MNGT IP ADDRESS: " + manIP
	print ""

##~~~~~ MAIN ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~##

networkSelection = findNetworkArea()
realm = networkSelection[1]
sharedNetwork = networkSelection[0]
manIP = getNextManIP(sharedNetwork)
custID = str(raw_input ("Enter Customer ID: "))
userName = custID + realm
manIP = getNextManIP(sharedNetwork)
print manIP, realm, sharedNetwork, custID  + " " +  userName
school = yes_or_no("Is this a school?")
#print manIP
if school == True:
	print "Calling generateSchoolConfig"
	generateSchoolConfig(sharedNetwork,manIP,custID)
	updateRadiusSchool(custID,manIP)
	quit ()
publicIP = getNextPubIP(sharedNetwork)
print publicIP
password=pass_generator()
siteName=generateResidentialConfig(sharedNetwork,manIP,userName,password)
updateRadiusResidential(custID,userName,password,manIP,publicIP)
updateIpam(publicIP)
#print "Config paramters are" , userName,password,manIP,publicIP,siteName
print
print
#readBack(userName,publicIP)
quit ()
