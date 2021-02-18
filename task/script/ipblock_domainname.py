import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from task.db import Db
import datetime
class Main(basetask.BaseTask):
    name="曹松匹配IP块对应的域名"
    mark="源数据表在19服务器3307端口domain库中时会调用sql存储过程（快），在其他库中时使用程序存取数据(慢).不要同时执行2个此进程"
    inputcolums = {'minip':{'name': "minip", "value": 'minip','type':'radio'}, 'maxip':{'name': "maxip", "value": 'maxip','type':'radio'}}
    args={
         'outputable': {'name':'outputable','alisaname':'输出表名称','value':'','type':'input','formator':'{sourcetable}_domainresult_{now}'},
       #  'outputtype': {'name': 'outputtype', 'alisaname': '输出方式', 'value': '1', 'style': 'radio',
       #                'options': [{'name':'ip-domain多行输出','value':'1'},{'name':'ip-domain,domain单行输出(,连接domain)','value':'0'}]},
        }
    async def init(self):
        sql = f'''CREATE TABLE if not exists  `{self.args['outputable']['value']}`  (
          `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
          `minip` int(11) UNSIGNED NULL DEFAULT NULL,
          `r_id` int(11)  UNSIGNED NULL DEFAULT NULL,
          `domain` varchar(600) CHARACTER SET utf8 COLLATE utf8_general_ci NULL DEFAULT NULL,
          `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`) USING BTREE,
          INDEX `r_id`(`r_id`) USING BTREE,
          INDEX `minip`(`minip`) USING BTREE
        ) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci COMMENT = '版本日期：20201015' ROW_FORMAT = Dynamic;'''
        await self.db.execute(sql)
        sourceconfig={'sourcetable': 'ipuu_domain_ip_2020M07', 'database': 'domains', 'databaseip': '192.168.1.19', 'databaseport': 3307, 'databaseuser': 'jiaowei', 'databasepassword': 'jiaowei_123', 'condition': '', 'conditionarr': []}
        if self.dbconfig['databaseip']==sourceconfig['databaseip'] and self.dbconfig['databaseport']==sourceconfig['databaseport']:
            await  self.rapidmatch() #相同数据库可以使用sql 语句直接操作
        else:
            await self.work()#不同数据库 必须程序取数据匹配了
    async def rapidmatch(self):
        sql=f'''DROP PROCEDURE IF EXISTS matchipdomain;
CREATE PROCEDURE matchipdomain(IN sourcetable VARCHAR(255),IN iminip varchar(30),IN imaxip varchar(30))
BEGIN
	DECLARE flag INT DEFAULT 0;
	DECLARE vid int unsigned ;
	DECLARE vminip int unsigned ;
	DECLARE vmaxip int unsigned ;
	
	declare SQL_FOR_SELECT varchar(300);
	DECLARE ipcursor CURSOR FOR (SELECT id,minip,maxip FROM fengchuantmpview);
	DECLARE CONTINUE HANDLER FOR NOT FOUND SET flag = 1;
	set SQL_FOR_SELECT= CONCAT("CREATE OR REPLACE VIEW fengchuantmpview (id,minip,maxip) as SELECT id,",iminip,",",imaxip," from ",sourcetable);
	set @fengsql=SQL_FOR_SELECT;
	PREPARE stm FROM @fengsql;
	EXECUTE stm;
	DEALLOCATE PREPARE stm;
	OPEN ipcursor;
		FETCH ipcursor INTO vid,vminip,vmaxip;
		
		WHILE flag != 1 DO
				WHILE vminip <=vmaxip DO
					insert into `{self.args['outputable']['value']}` (r_id,minip,domain,update_time) select vid,vminip,domain,update_time from `ipuu_domain_ip_2020M07` where ip=vminip;
					set vminip=vminip+1;
				END WHILE;
				FETCH ipcursor INTO vid,vminip,vmaxip;
		END WHILE;
	CLOSE ipcursor;
END;
call  matchipdomain('{self.dbconfig['sourcetable']}','{self.inputcolums['minip']['value']}','{self.inputcolums['maxip']['value']}');'''
        print(sql)
        await self.db.execute(sql)
    async def getdata(self):
        sql = f"""select  id from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        tmpresult=await self.db.execute(sql,1)
        if not tmpresult:
            raise ('empty table')
        self.maxid=tmpresult[0][0]
        sqlid = 1

        while sqlid<=self.maxid:
            sql=f"select id,{self.inputcolums['minip']['value']},{self.inputcolums['maxip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"
            print(sql)
            sqlid=sqlid+10000
            self.progress = (sqlid) * 100 // self.maxid
            ret=await self.db.execute(sql,1)
            if ret:
                yield ret
    async def work(self):
        sourceconfig={'sourcetable': 'ipuu_domain_ip_2020M07', 'database': 'domains', 'databaseip': '192.168.1.19', 'databaseport': 3307, 'databaseuser': 'jiaowei', 'databasepassword': 'jiaowei_123', 'condition': '', 'conditionarr': []}

        sourcedb=await Db(sourceconfig)

        arr=[]
        insertsql = f"insert into {self.args['outputable']['value']} (minip,r_id,domain,update_time) values (%s,%s,%s)"
        async for results in self.getdata():
            for row in results:
                rid,minip,maxip=row
                for ip in range(minip,maxip+1):
                    sql = f"select domain,update_time from {sourceconfig['sourcetable']} where `ip`={ip}"
                    print(sql)
                    ret=await sourcedb.execute(sql,1)
                    if ret:
                       # if self.args['outputtype']['value']=='0':

                        #    arr.append([ip,rid,','.join(i[0] for i in ret),str(datetime.datetime.now())])
                        #else:
                        arr+=[[ip,rid,i[0],i[1]] for i in ret]
                        if len(arr)>5000:
                            await self.db.executemany(insertsql,arr)
                            arr=[]
        if arr:
            await self.db.executemany(insertsql, arr)
        await sourcedb.close()
if __name__ == '__main__':
    task=Main()
    task.run()