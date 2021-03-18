import collections
import re
import json
from pathlib import Path


class ParserBanner:
    '''use nmap's re pattern to find the service name,version'''
    patterndic = collections.defaultdict(list)
    port2proto = {80: 'http', 21: 'ftp', 22: 'ssh', 23: 'telnet', 25: 'smtp', 110: 'pop3', 143: 'imap', 465: 'smtp',
                  995: 'pop3', 993: 'imap'}
    usednmapproto = port2proto.values()
    povpattern = re.compile(r' ([pov])/(.*?)/')

    def __init__(self, ip, port, banner):
        self.ip = ip
        self.port = port
        self.banner = banner
        if len(self.__class__.patterndic) == 0:
            self.get_patterndic()

    def get_patterndic(self):
        # there are lot of re expressions,and they have diffrent styles, so just use that is simple to parse
        file = str(Path(__file__).resolve(strict=True).parent.joinpath('nmap-service-probes'))
        # print(file)
        with open(file, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                try:
                    if line[0:6] != 'match ':
                        continue
                    p = 6
                    while line[p] != ' ':
                        p += 1
                    protoname = line[6:p]
                    if protoname not in self.__class__.usednmapproto:
                        continue
                    if line[p + 1] != 'm':
                        continue
                    sep = line[p + 2]
                    endseppos = line.find(sep, p + 4)
                    patternflagpos = endseppos + 1
                    pattern = line[p + 3:endseppos]
                    patternflag = 0
                    debugn = 0
                    while line[patternflagpos] != ' ':
                        if line[patternflagpos] == 'i':
                            patternflag |= re.IGNORECASE
                        elif line[patternflagpos] == 's':
                            patternflag |= re.DOTALL
                        patternflagpos += 1
                        debugn += 1
                        if debugn > 2:
                            print('parseerror')
                            raise ('parseerror')
                    tmpstr = line[patternflagpos:]
                    tmpstr = re.sub(r'\$(?=\d+)', r'\\', tmpstr);
                    self.__class__.patterndic[protoname].append([re.compile(pattern, patternflag), tmpstr])
                except Exception as e:
                    print(55, e)

                if line[line.find(' ') + 2] != '|':
                    continue
                header, content = line.split('|', 1)
                if 'http' in header:
                    self.__class__.protodic['http'].append(re.compile(content))

    def parse(self):
        try:
            self.tag = f'{self.__class__.port2proto[int(self.port)]}{self.port}'
            print('tag', self.tag)
            if self.__class__.port2proto[int(self.port)] in ['http', 'ssh']:
                return self.__getattribute__('parse' + self.__class__.port2proto[int(self.port)])()
            else:
                return self.parsetmp(self.__class__.port2proto[int(self.port)])
        except Exception as e:
            print(e)
            return '', '', ''

    def parsehttp(self):
        try:
            js = json.loads(self.banner)
            tmpserver = js[self.tag]['result']['response']['headers']['server'][0]
            version = re.findall(r'[\d+\.]+', tmpserver)
            return tmpserver, version[0] if version else '', ''
        except Exception as e:
            print(e)
            return '', '', ''

    def parsetmp(self, name):
        service = version = os = ''
        try:
            banner = json.loads(self.banner)[self.tag]['result']['banner']
            print('name')
            for repattern, opvstr in self.__class__.patterndic[name]:
                if repattern.search(banner):
                    try:
                        for name, value in self.__class__.povpattern.findall(repattern.sub(opvstr, banner)):
                            if name == 'p':
                                service = value
                            elif name == 'o':
                                os = value
                            elif name == 'v':
                                version = value
                        return service, version, os
                    except Exception as e:
                        print(95, e)
                        continue
        except Exception as e:
            print(98, e)
        return '', '', ''

    def parsessh(self):
        service = version = os = ''
        try:
            tmp = json.loads(self.banner)
            service = tmp[self.tag]['result']['server_id']['software']
            version = tmp[self.tag]['result']['server_id']['version']

        except Exception as e:
            print(e)
        return service, version, os


if __name__ == '__main__':
    ip = '23'
    port = 21
    banner = r'''{"ftp21": {"status": "success", "protocol": "ftp", "result": {"banner": "220 MikroTik FTP server (MikroTik 6.46.4) ready\r\n"}, "timestamp": "2020-10-22T15:07:19+08:00"}}'''

    pb = ParserBanner(ip, port, banner)
    print(pb.parse())