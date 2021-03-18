import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
from scriptpad.db import Db
import re
import asyncio
class Main(basetask.BaseTask):
    name = "海南省三亚市入口"
    dbconfig = {'sourcetable':'cn_proj_db_tr_vp_526_hainan'}
    def parsetracerouteresult(self,tmpresult):
        ll=len(tmpresult)
        p=0
        arr=[]
        is_zl = 1
        while p<ll:

            step,routerid, num_ip,isalive = tmpresult[p]
            if step==1:
                if len(arr)>=2:
                    print(p,ll,[arr[-2][1], arr[-2][2]])
                    self.allpoints.append([arr[-2][1], arr[-2][2],is_zl,arr[-2][3],arr[-2][2]>>16<<16,arr[-2][2]>>8<<8])
                arr=[]
                is_zl=1
            if tmpresult[p][1]!=0:
                arr.append(tmpresult[p])
            else:
                is_zl=0
            p+=1
        if len(arr) >= 2:
            self.allpoints.append([arr[-2][1], arr[-2][2],is_zl,arr[-2][3],arr[-2][2]>>16<<16,arr[-2][2]>>8<<8])
    async def init(self):

        self.allpoints=[]
        targetdb = {'sourcetable': 'router_numip', 'database': 'CN_Proj_DB_temp', 'databaseip': '192.168.1.25',
                        'databaseport':3306, 'databaseuser': 'fengchuan', 'databasepassword': 'bOelm#Fb2aX', 'condition': '',
                        'conditionarr': []}
        self.tdb = await Db(targetdb)

        for n in [526,533,541]:#
            traceroutetable=f'cn_proj_db_tr_vp_{n}_hainan'
            sql=f"select step,routerid,num_ip,isalive from {traceroutetable} order by id asc"
            tmpresult=await self.db.execute(sql,1)
            self.parsetracerouteresult(tmpresult)
        sql="insert into router_numip (router_ip,num_ip,is_zl,is_alive,num_ip2,num_ip3) values (%s,%s,%s,%s,%s,%s)"
        await self.tdb.executemany(sql,self.allpoints)
        sql='''update router_numip a,cn_proj_landmark_hainan_all b,cn_proj_dic_cn_landmark_districts_infos c set a.province = c.official_province,a.city = c.official_city,a.district = c.official_district where a.num_ip2 = b.num_ip2 and a.num_ip3 = b.num_ip3 and a.num_ip = b.num_ip and b.district_id = c.id'''
        await self.tdb.execute(sql)
        sql="update router_numip a,CN_Proj_DB.cn_proj_db_main_ip_blk24_base b,CN_Proj_DB.cn_proj_dic_cn_lib_city c set a.ip_city = c.id where a.num_ip2 = b.num_ip2 and a.num_ip3 = b.num_ip3 and a.num_ip between b.num_minip and b.num_maxip and b.city_id = c.id and c.city = '三亚市'"
        await self.tdb.execute(sql)
        #sql="select "
    #进一步的数据处理
    async def init222(self):
        targetdb = {'sourcetable': 'router_numip', 'database': 'CN_Proj_DB_temp', 'databaseip': '192.168.1.25',
                        'databaseport':3306, 'databaseuser': 'fengchuan', 'databasepassword': 'bOelm#Fb2aX', 'condition': '',
                        'conditionarr': []}
        self.tdb = await Db(targetdb)
        sql="select router_ip,district from router_numip where ip_city=251 and district!=''"
        result=await self.tdb.execute(sql,1)
        r=defaultdict(lambda : defaultdict(int))
        for ip,area in result:
            r[ip][area]+=1
        arr=[]
        for ip in r:
            for area in r[ip]:
                arr.append([ip,area,r[ip][area]])
                print(ip,area,r[ip][area])
        sql="insert into router_district (router_ip,district,num) values (%s,%s,%s)"
        await self.tdb.executemany(sql,arr)
from collections import defaultdict
if __name__ == '__main__':
    task=Main()
    task.run()