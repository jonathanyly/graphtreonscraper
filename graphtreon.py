import requests
from bs4 import BeautifulSoup
import time
import re
import json
from datetime import datetime, timezone
import pandas as pd
import threading

class graphtreon:

    def __init__(self, csvdict):

        self.csvdict = csvdict
        self.session = requests.Session()
        self.headers = {
            'authority': 'graphtreon.com',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7,fr;q=0.6',
            'cache-control': 'max-age=0',
            # 'cookie': '_ga=GA1.2.1131125318.1683127865; _gid=GA1.2.599574092.1684670646; laravel_session=eyJpdiI6IldTMWEybkJVN3pkQmYzN09CV1wvUlVBPT0iLCJ2YWx1ZSI6IlpvM3ZLQ2FFckRzSmpJSWg3RlpDcUZIUFZwa0ZwRTlZWExUYzhCRHZpZFBDWEs2N1lxbENsRDRDRmJmRCtWdmIiLCJtYWMiOiJiYWJhYTMxOTA5MTk2MjMyYmQ5YWEwYTZlZTAyZTM1ODlmNWZmZDUyNTNkODZiNDM3NzM0MDU0MTQ3NTY4NzE2In0%3D',
            'referer': 'https://graphtreon.com/patreon-creators',
            'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        }
        self.cookies = {
            '_ga': 'GA1.2.1131125318.1683127865',
            '_gid': 'GA1.2.599574092.1684670646',
            'laravel_session': 'eyJpdiI6IldTMWEybkJVN3pkQmYzN09CV1wvUlVBPT0iLCJ2YWx1ZSI6IlpvM3ZLQ2FFckRzSmpJSWg3RlpDcUZIUFZwa0ZwRTlZWExUYzhCRHZpZFBDWEs2N1lxbENsRDRDRmJmRCtWdmIiLCJtYWMiOiJiYWJhYTMxOTA5MTk2MjMyYmQ5YWEwYTZlZTAyZTM1ODlmNWZmZDUyNTNkODZiNDM3NzM0MDU0MTQ3NTY4NzE2In0%3D',
        }
    

    def gettoppatreons(self, category):

        '''
        Returns Top Patreons
        '''

        params = {
            '_': f'{round(time.time())}',
        }

        while True:
            try:
                response = self.session.get(f'https://graphtreon.com/api/creators/{category}', params=params, cookies=self.cookies, headers=self.headers)
                if response.status_code == 200:
                    patreons = response.json()["data"]
                    break
                else:
                    print(f'Something went wrong, got different status code', response.status_code)
            except Exception as e:
                print("Got Exception", e)
        counter = 0
        for patreon in patreons:
            try:
                name = re.findall(r'\(.*\)', patreon["link"])[0].replace("(", "").replace(")", "")
                self.csvdict[name] = {"Name": name, "Patreons":patreon["patrons"], "Earnings":patreon["earnings"], "createdAt": patreon["patreonPublishedAt"], "Link": f'https://graphtreon.com/creator/{name}', "daysRunning": patreon["daysRunning"]}
                print(f"[{datetime.now()} | {name}] Saved Patreon...")
            except IndexError:
                continue
            counter += 1
            if counter == 3:
                return
            
    def getsinglepatreon(self, patreon):

        '''
        Returns data from a single patreon creator
        '''
        
        while True:
            try:
                keyValue = patreon["Name"]
                response = self.session.get(f'https://graphtreon.com/{patreon["Name"]}', cookies=self.cookies, headers=self.headers)
                if response.status_code == 200:
                    tempSoup = BeautifulSoup(response.text, "html.parser")
                    break
                elif response.status_code == 404:
                    print("Got wrong name, returning")
                    return
                else:
                    print("something went wrong during request", response.status_code)
            except Exception as e:
                print("got exception", e)
        
        scriptContent = tempSoup.find_all("script")[11].text

        patronSeriesData = json.loads("["+re.search(r'var dailyGraph_patronSeriesData = \[(.*)\];',scriptContent)[1]+"]")
        earningsSeriesData = json.loads("["+re.search(r'var dailyGraph_earningsSeriesData = \[(.*)\];',scriptContent)[1]+"]")
        self.csvdict[keyValue]["Earnings Data"] = earningsSeriesData
        self.csvdict[keyValue]["Patron Data"] = patronSeriesData
        print(f'[{datetime.now()}] Got data for {keyValue}')

    def convertSingleDates(self, patreon):

        tempPatronList = []
        tempEarningsList = []
        '''
        Converting UNIX Timestamps to UTC
        '''

        '''
        Converting Patron Dates
        '''
        for index, date in enumerate(patreon["Patron Data"]):
            tempUnix = int(date[0]/1000)
            utcTimeDatetime = datetime.fromtimestamp(tempUnix, timezone.utc)
            utcTime = datetime.strftime(utcTimeDatetime, "%d.%m.%Y")
            if datetime.strptime(utcTime, "%d.%m.%Y") >= datetime.strptime("11.03.2019", "%d.%m.%Y") and datetime.strptime(utcTime, "%d.%m.%Y") <= datetime.strptime("11.03.2021", "%d.%m.%Y"):
                self.csvdict[patreon["Name"]]["Patron Data"][index][0] = utcTime
                tempPatronList.append(date)
            
        
        self.csvdict[patreon["Name"]]["Patron Data"] = tempPatronList

        '''
        Converting Earnings Dates
        '''

        for index, date in enumerate(patreon["Earnings Data"]):
            tempUnix = int(date[0]/1000)
            utcTimeDatetime = datetime.fromtimestamp(tempUnix, timezone.utc)
            utcTime = datetime.strftime(utcTimeDatetime, "%d.%m.%Y")
            if datetime.strptime(utcTime, "%d.%m.%Y") >= datetime.strptime("11.03.2019", "%d.%m.%Y") and datetime.strptime(utcTime, "%d.%m.%Y") <= datetime.strptime("11.03.2021", "%d.%m.%Y"):
                self.csvdict[patreon["Name"]]["Earnings Data"][index][0] = utcTime
                tempEarningsList.append(date)
            
        
        self.csvdict[patreon["Name"]]["Earnings Data"] = tempEarningsList
        
        print("Converted all timestamp", patreon["Name"])
            
    def convertToCSV(self):

        '''
        Converting self.csv to normal CSV output, removing all dates before 31.12.2018 and after 31.12.2020
        Corona official start
        '''
        for key, val in self.csvdict.items():
            if len(val["Earnings Data"]) != 0:
                tempDict = {"Patreon Count": [val for key,val in val["Patron Data"]],"Earnings Count": [round(val) for key,val in val["Earnings Data"]], "Date": [key for key,val in val["Patron Data"]]}
                df = pd.DataFrame.from_dict(tempDict, orient='index')
                df = df.transpose()
                df.to_csv(f"{key}.csv", index = False)
            else:
                tempDict = {"Patreon Count": [val for key,val in val["Patron Data"]], "Date": [key for key,val in val["Patron Data"]]}
                df = pd.DataFrame.from_dict(tempDict, orient='index')
                df = df.transpose()
                df.to_csv(f"{key}.csv", index = False)

    def getTotalPatreons(self):

        '''
        Uses threading module to check all patreons at the same time
        '''
        threads = []
        for key, val in self.csvdict.items():
            tempThread = threading.Thread(target=self.getsinglepatreon, args = (self.csvdict[key],))
            tempThread.start()
            threads.append(tempThread)
        
        for thread in threads:
            thread.join()

    def convertAllDates(self):

        '''
        uses threading module to convert faster
        '''

        threads = []
        for key, val in self.csvdict.items():
            tempThread = threading.Thread(target=self.convertSingleDates, args=(val,))
            tempThread.start()
            threads.append(tempThread)
        
        for thread in threads:
            thread.join()


    


