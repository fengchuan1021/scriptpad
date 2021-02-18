from rest_framework.views import APIView
import asyncio
import asyncssh
from rest_framework.response import Response
class serverScript(APIView):
    async def readfiles(self,path='.'):
        n=1
        while n<5:
            try:
                async with asyncssh.connect('49.64.220.49', port=22, username='ant', password='ant@aiwen123',
                                            known_hosts=None, keepalive_interval=3) as conn:
                    async with conn.start_sftp_client() as sftp:
                        dirs=await sftp.readdir(path)
                        files=[{'name':f.filename,'isdir':f.longname[0]=='d'} for f in dirs if f.filename!='.']
                        files=sorted(files,key=lambda item:(-item['isdir'],item['name']))
                        return files
            except Exception as e:
                print(e)
                n+=1

    def get(self, request):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result=loop.run_until_complete(self.readfiles())
        return Response(result)
