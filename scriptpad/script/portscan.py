import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import ipaddress
import asyncio
import math,json
class Main(basetask.BaseTask):
    name="单个ip端口探测"
    atmobiles = ['刘亚伟']
    mark = "大部分服务器有被封禁现象，只选择540可以获得更多结果。"
    args={'ports':{'name':'ports','alisaname':'要探测的端口','value':'80,443,21,8080,8081,25,465,143,993,110,995,22,23,53,0','type':'input'},
          'waittime': {'name': 'waittime', 'alisaname': '等待回应时间', 'value': '2', 'type': 'input'},
          }
    inputcolums = {'ip':{'name': "ip", "value": 'ip','type':'radio'}}
    outputcolums = {'ports':{'name': "ports", 'value':'ports','altervalue': "ADD COLUMN `{colum}` varchar(1024) NULL DEFAULT NULL",'addnewcolum':'1'},
                    }
    async def startremote(self):
        dic = {"port": f"{self.args['ports']['value']}", "listname": f"{self.tasklist}",'waittime':self.args['waittime']['value']}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/portscan.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        sql = f"""select  id from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        tmpresult=await self.db.execute(sql,1)
        if not tmpresult:
            raise ('empty table')
        self.maxid=tmpresult[0][0]
        self.totalnum=self.maxid
        sqlid=1
        while sqlid<=self.maxid :
            if int(await self.redis.llen(self.tasklist))>10000:
                self.progress=(sqlid-10000)*100//self.maxid
                if self.progress<=0:
                    self.progress=6
                await asyncio.sleep(2)
                continue
            sql = f"""select id,{self.inputcolums['ip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+1000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            #print(sql)
            result=await self.db.execute(sql,1)
            sqlid=sqlid+1000



            arr=[]
            for id,ip in result:

                try:
                    strip=str(ipaddress.ip_address(ip))
                    arr.append(f"{id}_{strip}")
                except Exception as e:
                    print(e)
            if arr:
                await self.redis.rpush(self.tasklist, *arr)


        await self.settaskendflag()


    async def getresult(self):

        #sql = f"insert into {self.args['outputable']['value']} (id,ports,ip,host_id) values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE ports=VALUES(ports)"
        sql = f"insert into {self.dbconfig['sourcetable']} (id,{self.outputcolums['ports']['value']}) values (%s,%s) ON DUPLICATE KEY UPDATE {self.outputcolums['ports']['value']}=VALUES({self.outputcolums['ports']['value']})"
        #print(sql)
        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 10000, encoding="utf-8")
            if result:
                await self.redis.ltrim(self.resultlist, len(result), -1)
                self.sleeptime=0
                rows = [i.split('_', 2)[0:2] for i in result]

                await self.db.executemany(sql, rows)
            else:
                self.sleeptime+=3
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break
                await asyncio.sleep(3)
if __name__ == '__main__':
    task=Main()
    task.run()