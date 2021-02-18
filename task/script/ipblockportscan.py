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
    name="ip块端口探测"
    mark = "大部分服务器有被封禁现象，只选择540可以获得更多结果。"
    atmobiles = ['刘亚伟']
    sourcetable='tw_all_ipblk_for_port20200925'
    args={'ports':{'name':'ports','alisaname':'要探测的端口','value':'80,443,21,8080,8081,25,465,143,993,110,995,22,23,53,0','type':'input'},
         'outputable': {'name':'outputable','alisaname':'输出表名称','value':'','type':'input','formator':'{sourcetable}_result_{now}'},
            'waittime': {'name': 'waittime', 'alisaname': '等待回应时间', 'value': '2', 'type': 'input'},
          }
    inputcolums = {'minip':{'name': "minip", "value": 'minip','type':'radio'}, 'maxip':{'name': "maxip", "value": 'maxip','type':'radio'}}
    async def startremote(self):
        dic = {"port": f"{self.args['ports']['value']}", "listname": f"{self.tasklist}",'waittime':self.args['waittime']['value']}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/portscan.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)
    async def init(self):
        sql = f'''CREATE TABLE if not exists  `{self.args['outputable']['value']}`  (
              `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
              `ip` int(11) UNSIGNED NULL DEFAULT NULL,
              `ports` varchar(1024) NULL DEFAULT NULL,
              `host_id` int(11) NULL DEFAULT 0,
              PRIMARY KEY (`id`) USING BTREE,
              UNIQUE INDEX `nip`(`ip`) USING BTREE
            ) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;'''
        await self.db.execute(sql)
    async def sendtask(self):
        sql = f"""select  id from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        tmpresult=await self.db.execute(sql,1)
        if not tmpresult:
            raise ('empty table')
        self.maxid=tmpresult[0][0]
        self.totalnum=self.maxid


        sqlid=1
        while sqlid<=self.maxid:
            if int(await self.redis.llen(self.tasklist))>10000:
                self.progress=(sqlid-10000)*100//self.maxid
                if self.progress<=0:
                    self.progress=6
                await asyncio.sleep(2)
                continue
            sql = f"""select {self.inputcolums['minip']['value']}, {self.inputcolums['maxip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+1000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            result=await self.db.execute(sql,1)
            sqlid=sqlid+1000



            arr=[]
            for ip1,ip2 in result:
                try:
                    tmp = netaddr.iprange_to_cidrs(str(ipaddress.ip_address(ip1)), str(ipaddress.ip_address(ip2)))
                    arr += [f"0_{i}" for i in tmp]
                except Exception as e:
                    print(e)
            if arr:

                await self.redis.rpush(self.tasklist,*arr)

        await self.settaskendflag()
    async def calcprogress(self):
        leftnum = await self.redis.llen(self.tasklist)
        self.progress =  math.floor((self.totalnum - leftnum) * 100 / self.totalnum)
    async def getresult(self):

        sql = f"insert into {self.args['outputable']['value']} (id,ports,ip,host_id) values (%s,%s,%s,%s) ON DUPLICATE KEY UPDATE ports=VALUES(ports)"
        print(sql)
        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 10000, encoding="utf-8")
            if result:
                await self.redis.ltrim(self.resultlist, len(result), -1)
                self.sleeptime=0
                rows = [i.split('_', 3) for i in result]
                #print('getreuslt',rows)
                await self.db.executemany(sql, rows)
            else:
                print('no result?????')
                await self.calcprogress()
                self.sleeptime+=3
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break
                await asyncio.sleep(3)
if __name__ == '__main__':
    task=Main()
    task.run()