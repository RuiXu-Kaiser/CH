import subprocess
import requests
import os
import re

def getSessionID ():
    os.remove (headerFilePath)
    command = [
        "curl",
        "-H", "X-Requested-With: Curl Sample",
        "-D", headerFilePath,
        "-d", "action=login&username=kaser2rx1&password=$Rxu7200720529",
        "https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/session/"  # Replace with your target URL
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)


def extract_qualys_session():
    try:
        with open(headerFilePath, "r", encoding="utf-8") as f:
            for line in f:
                # Target Set-Cookie headers in a case-insensitive manner
                if line.lower().startswith("set-cookie:"):
                    # Search for the QualysSession key and capture its value
                    match = re.search(r"QualysSession=([^;\s]+)", line)
                    if match:
                        return match.group(1)

        print("QualysSession key not found in the file.")
        return None

    except FileNotFoundError:
        print(f"Error: The file '{filename}' does not exist.")
        return None

def getScanHistoryData (SessionID):
    os.remove (scanHistoryFilePath)
    command = [
        "curl",
        "-H", "X-Requested-With: Curl Sample",
        "-b", "QualysSession="+SessionID+"; path=/api;secure",
        "-o", scanHistoryFilePath,
        "https://qualysapi.qg2.apps.qualys.com/api/2.0/fo/scan/?action=list&type=Scheduled&launched_after_datetime=2026-08-10&state=Finished&show_status=0&ignore_target=1"
    ]
    result = subprocess.run(command, check=True, capture_output=True, text=True)

dirpath = r"\\csc2cwn21113408.cloud.kp.org\\Client$"
headerFilePath = os.path.join(dirpath,"header.txt")
scanHistoryFilePath = os.path.join(dirpath,"scanhistory.xml")
getSessionID()
session_key = extract_qualys_session()
getScanHistoryData (session_key)

SAServer = "csc2cwn21113408.cloud.kp.org,2251"
SADB = "Qualys"
UpdateScript = r"C:\Users\Y912052\ScanHistoryUpdateScript.sql"
Logfile = r"C:\Users\Y912052\UpdateDBLog.log"

subprocess.call(["sqlcmd", "-S", SAServer, "-d", SADB, "-i", UpdateScript, "-o", Logfile, "-E"], shell=True)