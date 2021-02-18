import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from task.db import  Db
import random
import datetime
from pathlib import Path
class Main(basetask.BaseTask):
    name = "获取域名whois信息"
    atmobiles = ['刘金周']
    inputcolums = {'domain':{'name': "domain", "value": 'domain'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisaname': "结果输出表",'formator':'domainwhois_{now}'}
    }
    dbconfig = {'sourcetable': '', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}
    async def init(self):
        tablesql=f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `domain` varchar(100) CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL DEFAULT NULL,
  `update_time` datetime(0) NULL DEFAULT NULL,
  `domain_alive` tinyint(4) NULL DEFAULT NULL,
  `domain_status` varchar(1024) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `domain_nserver` varchar(1500) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `domain_updated_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `domain_creation_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `domain_expiration_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_domain_id` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_name` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_url` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_iana_id` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_updated_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_creation_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_expiration_date` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_abuse_email` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrar_abuse_phone` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_name` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_org` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_street` varchar(512) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_city` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_prov` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_postal_code` varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_country` varchar(50) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_phone` varchar(30) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_phone_ext` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_fax` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_fax_ext` varchar(20) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `registrant_email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_org` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_street` varchar(120) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_city` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_prov` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_postal_code` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_country` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_phone` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_phone_ext` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_fax` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_fax_ext` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `admin_email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_id` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_name` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_org` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_street` varchar(100) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_city` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_prov` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_postal_code` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_country` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_phone` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_phone_ext` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_fax` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_fax_ext` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `tech_email` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `whois_server` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  `refer_url` varchar(80) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `domain`(`domain`) USING BTREE
) ENGINE = MyISAM AUTO_INCREMENT =1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;'''
        print(tablesql)
        await self.db.execute(tablesql)
        self.colums = {"domain": [], "update_time": [], "domain_alive": ["0"]}
        file = str(Path(__file__).resolve(strict=True).parent.parent.joinpath('Field.txt'))
        with open(file, 'r') as f:
            for l in f.readlines():
                k, c = l.split(":")
                self.colums.update({k.lower(): []})

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"CNAME"}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/whois.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        sql = f"""select  id,{self.inputcolums['domain']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
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
            sql = f"""select id,{self.inputcolums['domain']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)} group by {self.inputcolums['domain']['value']}"""
            
            result=await self.db.execute(sql,1)
            sqlid=sqlid+10000



            arr=[]
            for id,domain in result:

                if 1:
                    try:
                        s=f'{domain}'
                        arr.append(s)
                        if len(arr) >= 3000:
                            #print('inserto redis',len(arr),self.tasklist)
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)

        await self.settaskendflag()

    async def getresult(self):

        updatesql=f"insert ignore into {self.args['outtable']['value']} ({','.join(self.colums.keys())}) values ({','.join(['%s']*len(self.colums))})"

        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime=0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows=[]
                for i in result:
                    rows.append(i.split('$_'))
                if rows:
                    await self.db.executemany(updatesql, rows,ignoreerror=True)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()