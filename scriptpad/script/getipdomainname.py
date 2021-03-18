import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from scriptpad.db import Db
class Main(basetask.BaseTask):
    name="匹配IP对应的域名"
    inputcolums={'ip':{'name':"ip","value":'ip'}}
    outputcolums = {'domainname':{'name': "domainname", 'value':'domainname','altervalue': "ADD COLUMN `{colum}` text  NULL DEFAULT NULL",'addnewcolum':'1'},
    }
    async def getdata(self):
        sql = f"""select  id from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        tmpresult=await self.db.execute(sql,1)
        if not tmpresult:
            raise ('empty table')
        self.maxid=tmpresult[0][0]
        sqlid = 1

        while sqlid<=self.maxid:
            sql=f"select id,{self.inputcolums['ip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"
            print(sql)
            sqlid=sqlid+10000
            ret=await self.db.execute(sql,1)
            if ret:
                yield ret
    async def work(self):
        sourceconfig={'sourcetable': 'ipuu_domain_ip_2020M07', 'database': 'domains', 'databaseip': '192.168.1.19', 'databaseport': 3307, 'databaseuser': 'jiaowei', 'databasepassword': 'jiaowei_123', 'condition': '', 'conditionarr': []}
        sourcedb=await Db(sourceconfig)
        targetcolum = self.outputcolums['domainname']['value']
        async for results in self.getdata():
            for row in results:
                sql = f"select domain from {sourceconfig['sourcetable']} where ip={int(ipaddress.ip_address(row[1]))}"
                print(sql)
                ret=await sourcedb.execute(sql,1)
                if ret:
                    sql = f"update {self.dbconfig['sourcetable']} set {targetcolum}='{','.join(i[0] for i in ret)}' where id={row[0]}"
                    print(sql)
                    await self.db.execute(sql)
        await sourcedb.close()

    def run(self):
        self.loop.run_until_complete(self.work())
if __name__ == '__main__':
    task=Main()
    task.run()