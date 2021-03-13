from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os,json,psutil
import task.script as script
import re
import asyncio
import sys
from task.serializers import historyserializer,TaskSerializer,Vpserializer
from task.models import TaskHistory
from task.models import Vp as Vpmodel
if os.name!='nt':
    from crontab import CronTab
from django.db import connections
from rest_framework import viewsets,pagination
class Taskatmobilesoption(APIView):
    def get(self,request):
        from task.basetask import BaseTask
        arr=BaseTask.atmobilesoption.keys()
        return Response(arr)
class Task(APIView):
    def get(self, request):
        scriptdir=os.path.join(settings.BASE_DIR,'task','script')
        files=os.listdir(scriptdir)
        tmp=[getattr(script,f[0:-3]).Main.setfilename(f) for f in files if f not in ['__init__.py','__pycache__']]
        scriptarr=sorted(tmp,key=lambda item: item.atmobiles[0] if item.atmobiles else '',reverse=True)
        serializer=TaskSerializer(scriptarr, many=True)
        return Response(serializer.data)
    def post(self,request):
        arr=["ok"]

        cmd=sys.executable

        tmp = {f.name: request.data.get(f.name) for f in TaskHistory._meta.fields if f.name in request.data}

        history=TaskHistory(**tmp)
        history.save()
        request.data['taskid']=history.id
        cmd += [os.path.join(settings.BASE_DIR, 'task','script', request.data['filename']), json.dumps(request.data)]

        psutil.Popen(cmd)
        cmd[-1]=f"'{cmd[-1]}'"
        if (request.data['cron']['enabled']):
            cron = CronTab(user= getpass.getuser())
            job = cron.new(command=' '.join(cmd),comment='sp'+str(history.id))
            job.setall(request.data['cron']['expression'])
            cron.write()
        return Response(arr)

class TableSearch(APIView):
    def get(self,request):
        tablename=request.query_params.get('sourcetable','')
        sql=f"select table_name,table_schema from tables where table_name like '%{tablename}%'"
        arr=[]
        for database in connections:
            if database=='default':
                continue
            try:
                cur=connections[database].cursor()
                cur.execute(sql)
            except Exception as e:
                continue

            tmp=cur.fetchall()
            for t in tmp:
                arr.append({'sourcetable':t[0],'value':f"{database}-{t[0]}",'database':t[1],'databaseip':settings.DATABASES[database]['HOST'],'databaseport':settings.DATABASES[database]['PORT'],'databaseuser':settings.DATABASES[database]['USER'],'databasepassword':settings.DATABASES[database]['PASSWORD'],
                            'condition':'','conditionarr':[]
                            })
        return Response(arr)


class TablePreview(APIView):
    def post(self,request):
        dbconfig=request.data
        obj={'colums':[],'datas':[]}
        if 1:
            db=f"{dbconfig['databaseip'][dbconfig['databaseip'].rfind('.')+1:]}-{dbconfig['databaseport']}"
            cur=connections[db].cursor()
            sql=f"show full columns from  {dbconfig['database']}.{dbconfig['sourcetable']}"
            cur.execute(sql)
            ret=cur.fetchall()
            obj['errortip']='该数据表没有自增id主键请调整'
            obj['colums']=[{"name":row[0]} for row in ret]
            for row in ret:
                if row[0]=='id':
                    if not row[1].startswith('int'):
                        obj['errortip'] = '该数据表id不是int类型请调整'
                        break
                    if row[4]!='PRI':
                        obj['errortip'] = '该数据表id不是主键'
                        break
                    obj['errortip']=''
                    break

            try:
                sql=f"select * from {dbconfig['database']}.{dbconfig['sourcetable']} {dbconfig['condition']} order by id desc limit 5"
                cur.execute(sql)
            except Exception as e:
                sql = f"select * from {dbconfig['database']}.{dbconfig['sourcetable']} {dbconfig['condition']} limit 3"
            print(sql)
            cur.execute(sql)
            ret=cur.fetchall()
            obj['datas']=[{ obj['colums'][i]['name'] :value  for i,value in enumerate(row)} for row in ret]

        return Response(obj)


def killtask(request,taskid,listname):
    from django.http import JsonResponse
    print(taskid,listname)
    try:

        os.system(f"""pkill -f ''taskid": {taskid}'""")
        print(f"""pkill -f '"taskid": {taskid}'""")
        model=Vpmodel.objects.get(id=taskid)
        model.deleteflag=1
        model.save()
    except Exception as e:
        print(e)

    try:
        cmd=sys.executable
        cmd += [os.path.join(settings.BASE_DIR, 'task', 'basetask.py'), 'killtask',listname]
        psutil.Popen(cmd)
    except Exception as e:
        print(e)
    return JsonResponse({'status':'ok'})


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 30
class TaskHistoryviewset(viewsets.ModelViewSet):

    queryset = TaskHistory.objects.all()
    serializer_class = historyserializer
    #pagination.PageNumberPagination.page_size = 30
    pagination_class = ExamplePagination
class Vp(viewsets.ModelViewSet):
    pagination.PageNumberPagination.page_size = 1000
    serializer_class = Vpserializer
    queryset = Vpmodel.objects.all()
from datetime import datetime
import getpass
class crontab(APIView):
    http_method_names = ['get', 'put', 'delete']
    def put(self,request,pk):
        cron = CronTab(user= getpass.getuser())
        print(pk)
        it = cron.find_comment('sp'+pk)
        item=it.__next__()
        print(request.data)
        r=item.enable(request.data['status'])
        print(request)
        cron.write()
        msg='禁用' if not r else '启用'
        msg=f'{msg}任务成功'
        return Response({'title':msg,'msg':msg})
    def delete(self,request,pk):
        cron = CronTab(user= getpass.getuser())
        it = cron.find_comment('sp'+pk)
        item=it.__next__()
        item.delete()
        cron.write()
        msg=f'删除任务成功'
        return Response({'title':msg,'msg':msg})
    def get(self, request):
        cron = CronTab(user= getpass.getuser())
        it = cron.find_comment(re.compile(r'sp(\d+)'))
        arr=[]
        for item in it:
            try:
                js=json.loads(item.command.split(' ',2)[2].strip("'"))
                try:
                    sourcetable=js['dbconfig']['sourcetable']
                except Exception as e:
                    sourcetable =''
                try:

                    schedule = item.schedule(date_from=datetime.now())
                    lasttime=schedule.get_prev()
                    nexttime= schedule.get_next()
                    outtable = js['args']['outtable']['value']
                except Exception as e:
                    outtable =''
                arr.append({'name':js['name'],'description':item.description(locale_code='zh_CN'),'enabled':item.is_enabled(),'detail':item.command,'sourcetable':sourcetable,'outtable':outtable,'pk':item.comment[2:],
                            'lasttime':lasttime,
                            'nexttime':nexttime,
                            })
            except Exception as e:
                print(e )
        return Response(arr)
def executecommand(request,command):

    import asyncssh
    from django.http.response import StreamingHttpResponse


    def getresult(command):
        print(command)
        models = Vpmodel.objects.all()
        async def run(host):
            try:

                async with asyncssh.connect(host.ip, port=host.port, username=host.username, password=host.password,
                                            known_hosts=None) as conn:

                    tmp = await conn.run(command)
                    data={'data':tmp.stdout,'status':tmp.returncode,'name':host.host_id}
            except Exception as e:
                data= {'data':'连接失败','status':-1,'name':host.host_id}
            result=f'data: {json.dumps(data)}\n\n'
            return result
        tasks=[run(model) for model in models]
        loop=asyncio.new_event_loop()

        done,pending=loop.run_until_complete(asyncio.wait(tasks,return_when=asyncio.FIRST_COMPLETED))
        for d in done:
            yield d.result()
        while pending:
            done, pending = loop.run_until_complete(asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED))
            for d in done:
                yield d.result()
        data={'closed':1}
        yield f'data: {json.dumps(data)}\n\n'
    response = StreamingHttpResponse(getresult(command))
    response['Content-Type'] = 'text/event-stream'
    response['Cache-Control'] = 'no-cache'
    response['Connection'] = 'keep-alive'
    return response


