import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
from bs4 import BeautifulSoup
import re
import aiohttp
import asyncio
class Main(basetask.BaseTask):
    name = "datacentermap"
    dbconfig = {'sourcetable':'datacentermap'}
    async def myrequest(self,url):
        async with self.semaphore:
            en=0
            while 1:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url) as response:
                            return await response.text()
                except Exception as e:
                    print(44, e)
                    en+=1
                    if en>50:
                        return ''

    async def worker(self,a):
        text=await self.myrequest(f'https://www.datacentermap.com{a}')
        print(f'https://www.datacentermap.com{a}')
        if 'View as simple list' not in text:
            soup2 = BeautifulSoup(text, 'lxml')
            tmps = soup2.find_all('a', text=re.compile(r'[\w -]+ \(\d+\)'))
            print({a},tmps,text)
            if tmps:
                await asyncio.wait([self.worker(tmp.attrs['href']) for tmp in tmps])
        else:
            text = await self.myrequest(f'https://www.datacentermap.com{a}datacenters.html')
            country, city1, city2, *_ = a.replace('-',' ').split('/')[1:]
            soup3 = BeautifulSoup(text, 'lxml')
            trs = soup3.select('div.lefttext>table>tr')
            for tr in trs:
                arr = [country, city1, city2] + [td.text for td in tr.select('td')]
                if len(arr) == 7:
                    self.result.append(arr)
    async def init(self):
        self.result=[]
        url = '/datacenters.html'
        self.semaphore = asyncio.Semaphore(50) # when threads too big,the website will return too many connections.
        await self.worker(url)
        sql = "insert into datacentermap (country,city1,city2,data_center,company,address,city3) values (%s,%s,%s,%s,%s,%s,%s)"
        print(self.result)
        print(len(self.result))
        await self.db.executemany(sql, self.result)

if __name__ == '__main__':
    task=Main()
    task.run()