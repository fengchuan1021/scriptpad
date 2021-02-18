import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import netaddr
import ipaddress
import asyncio
import math,json
class Main(basetask.BaseTask):
    name = "获取IP块的主机名hostname"
    inputcolums = {'minip':{'name': "minip", "value": 'minip'},'maxip':{'name': "maxip", "value": 'maxip'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisa': "结果输出表",'formator':'ipuu_ip_hostname_{conditionarr}'}
    }

    dbconfig = {'sourcetable': 'aiwen_geoip_ask_street_multi_sorted', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}
    async def init(self):


        tablesql = f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`(
          `id` int(11) NOT NULL AUTO_INCREMENT,
          `ip` int(11) UNSIGNED NULL DEFAULT NULL,
          `hostname` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL,
          `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`) USING BTREE,
          UNIQUE INDEX `ip`(`ip`) USING BTREE
        ) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;'''
        await self.db.execute(tablesql)
    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"PTR"}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/aioquery.py '{json.dumps(dic)}'"
        #print(cmd)
        await self.remoterun(cmd)
    async def sendtask(self):
        sql = f"""select  id,{self.inputcolums['minip']['value']},{self.inputcolums['maxip']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        print(sql)
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
            sql = f"""select id,{self.inputcolums['minip']['value']},{self.inputcolums['maxip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+1000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            print(sql)
            result=await self.db.execute(sql,1)
            sqlid=sqlid+1000



            arr=[]
            for id,minip,maxip in result:
                for i in range(minip,maxip+1):

                    try:
                        strip=str(ipaddress.ip_address(i))
                        arr.append(f"0_{strip}")
                        if len(arr) >= 3000:
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)


        await self.settaskendflag()

    async def getresult(self):
        updatesql=f"insert into {self.args['outtable']['value']} (id,ip,hostname) values (%s,%s,%s) ON DUPLICATE KEY UPDATE hostname=VALUES(hostname)"


        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime=0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = [i.split('_', 2) for i in result]

                await self.db.executemany(updatesql, rows)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()