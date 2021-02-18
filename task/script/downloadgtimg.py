import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import asyncio
import math,json
import requests,time
class Main(basetask.BaseTask):
    name = "下载极验点选图片"
    atmobiles = ['刘金周']


    dbconfig = {'sourcetable': 'aiwen_geoip_ask_street_multi_sorted', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"NS"}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/downloadgtimg.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        pass
    async def getresult(self):
        while 1:
            result = await self.redis.lrange('gtimg_result', 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime=0
                await self.redis.ltrim('gtimg_result', len(result), -1)

                for url in result:
                    en = 0
                    fname = f'{str((time.time() * 10000))}.jpg'
                    while 1:


                        try:
                            session=requests.session()
                            ret = session.get(url)
                            with open(f'/home/ant/fengcuan/gtimg/{fname}', 'wb') as f:
                                f.write(ret.content)
                            break
                        except Exception as e:
                            print(e)
                            en+=1
                            if en>10:
                                break

            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>3*600  and int(await self.redis.llen('gtimg_result'))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()