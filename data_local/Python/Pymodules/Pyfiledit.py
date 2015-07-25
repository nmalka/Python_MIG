
##################################
#   ModuleNmae: Pyfiledit.py     #
##################################

import traceback
import pdb

def filesToBakup(config):
    import re
    try:
        fileList = re.split('[\t\s]?,[\t\s]?', config['Files'])
        if len(fileList) == 0 or fileList[0] == '':
            raise
    except:
        return False
    else:
        return True

def OtherHost(hostname):
    if hostname.endswith('a'):
        return hostname[:-1] + 'b'
    elif hostname.endswith('A'):
        return hostname[:-1] + + 'B'
    if hostname.endswith('b'):
        return hostname[:-1] + 'a'
    elif hostname.endswith('B'):
        return hostname[:-1] + + 'A'
    else:
        raise Exception, 'OTHERHOST can NOT be generate by from the given hostname \'%s\'' % hostname

class builder(object):
    def __init__(self,config, componentID, loggerName='', *args, **kwargs):
        self.log = '>> %s 2>&1' % config['LogFile']
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.id = componentID
    def __call__(self, editFiles, methodDict):
        import os, sys
        for fileToEdit in editFiles:
            self.fileToEdit = fileToEdit
            if os.path.basename(self.fileToEdit) in methodDict.keys() \
                    or self.fileToEdit in methodDict.keys():
                try:
                    if type(methodDict[os.path.basename(self.fileToEdit)]) == str:
                        method = 'self.' + methodDict[os.path.basename(self.fileToEdit)]
                    else:
                        method = methodDict[os.path.basename(self.fileToEdit)]
                except KeyError:
                    if type(methodDict[self.fileToEdit]) == str:
                        method = 'self.' + methodDict[self.fileToEdit]
                    else:
                        method = methodDict[self.fileToEdit]
                if os.path.isfile(self.fileToEdit):
                    lines = open(self.fileToEdit)
                    self.linesRef = lines.readlines()
                    lines.close()
                else:
                    self.linesRef = []
                self.file = open(self.fileToEdit, 'w')
                try:
                    self.logger.error('Starting the parser for: \'%s\'' % \
                                        self.fileToEdit)
                    if type(method) == str:
                        eval(method)()
                    else:
                        method()
                except:
                    self.logger.error('Failed to exec method, \'%s\'' % (method))
                    raise 
                try:
                    self.file.close()
                    self.logger.error('\'%s\' was successfully parsed' % \
                                        self.fileToEdit)
                except:
                    self.logger.error('Couldn\'t close the edited file: \'%s\'' % \
                                    self.fileToEdit)
                    raise Exception, '%109%'
            else:
                self.logger.error('Skipping \'%s\', no method for file' % \
                                    self.fileToEdit)


class CopyUtils(object):
    def __init__(self, Files, Path, cp='/bin/cp', 
            dateFormat='%Y%m%d%H%M%S', loggerName='', log='', *args, **kwargs):
        import os, stat, datetime, sys, re
        from Pymodule import dirFix
        import logging
        self.logger = logging.getLogger(loggerName)
        self.log = log
        # Date VAR
        self.runDate = datetime.datetime.now()
        self.dateVal = self.runDate.strftime(dateFormat)
        global dateVal
        dateVal = self.dateVal
        # building VARs from config
        try:
            self.fileDict = {}
            fileList = re.split('[\t\s]?,[\t\s]?', Files)
            for file in fileList:
                if file.endswith('/'): file = file[:-1]
                newFile = file.replace('/', '_')
                if newFile.startswith('_'): newFile = newFile[1:]
                self.fileDict[newFile] = file
            self.backupPath = dirFix(Path)
            self.cp = cp
            self.BackupDict = {}
        except:
            self.logger.error('Can NOT parse files param list')
            raise
        # create backupPath if not exist.
        try:
            os.makedirs(self.backupPath)
        except:
            pass
    def Backup(self):
        # backup method
        import os, sys
        # building BackupDict for the methods!
        for file in self.fileDict.keys():
            if os.path.isfile(self.fileDict[file]) or os.path.isdir(self.fileDict[file]):
                backfile = os.path.join(self.backupPath, self.dateVal + '_' + file)
                self.BackupDict[self.fileDict[file]] = backfile
            else:
                raise Exception, '\'%s\' no such file or directory' % self.fileDict[file]
        self.logger.debug(self.BackupDict)
        r = ''
        type = ''
        ret = []
        for src, dst in self.BackupDict.iteritems():
            if os.path.isfile(src): 
                r =''
                type = 'File'
            elif os.path.isdir(src):
                r = '-r'
                type = 'Directory'
            else: 
                raise Exception, '\'%s\' no such file or directory' % self.fileDict[file]
            if not os.system("%s --preserve=mode,ownership %s %s %s %s" % (self.cp, r, src, dst, self.log)):
                self.logger.error('%s %s was backed up to %s' % \
                                 (type, os.path.basename(src), os.path.basename(dst)))
                if os.path.isfile(src): ret.append(src)
            else:
                self.logger.info("%s --preserve=mode,ownership %s %s %s" % (self.cp, r, src, dst))
                self.logger.error('Can not backup \'%s\' %s' % (src, type))
                raise Exception, "%101%"
        return ret
    def RollBack(self, extention='*_'):
        # rollback method
        import os, sys
        from Pymodule import listFilesByDate
        rollfile = {}
        self.logger.debug('fileDict=%s' % self.fileDict)
        for file in self.fileDict.keys():
            NotinUse, files = listFilesByDate(dir=self.backupPath,extention=extention + file)
            if len(files)>0:
                rollfile[self.fileDict[file]] = files.pop(0)
            else:
                self.logger.error('File \'%s\' could not be rollback, no backfile!!' % file)
                if not extention == '*':
                    raise Exception, "%102%"
        for dst, src in rollfile.iteritems():
            wildcard = ''
            if os.path.isfile(src):
                r =''
                type = 'File'
            elif os.path.isdir(src):
                r = '-r'
                if os.path.isdir(dst):
                    wildcard = '/*'
                type = 'Directory'
            else:
                raise Exception, '\'%s\' no such file or directory' % src
            if not os.system("%s --preserve=mode,ownership %s %s%s %s %s" % \
                            (self.cp, r, src, wildcard, dst, self.log)):
                self.logger.error('%s \'%s\' was rolled back to %s' % \
                                 (type, os.path.basename(src), os.path.basename(dst)))
            else:
                self.logger.info("%s --preserve=mode,ownership %s %s%s %s" % (self.cp, r, src, wildcard, dst))
                self.logger.error('Can not rollback \'%s\' %s' % (os.path.basename(dst), type))
                if not extention == '*_':
                    raise Exception, "%100%"
    def Delete(self):
        import os
        for file in self.fileDict.values():
            if os.path.isfile(file):
                os.unlink(file)
                self.logger.info('Delete \'%s\'' % os.path.basename(file))
            else:
                self.logger.info('\'%s\' no such file.')
                raise Exception, '%133%'

class backup(builder):
    def __call__(self, *args, **kwargs):
        import os, re
        if self.config['BackupFiles']:
            File = CopyUtils(Files=self.config['BackupFiles'], Path=self.config['BackupPath'], log=self.log)
            self.logger.error('Starting the backup:')
            ret = File.Backup()
            self.logger.error("backuping was successfully finished")
        else:
            self.logger.error("BackupFiles parametter is empty. There is nothing to backup.")
            raise Exception, '%132%'

        if self.config.has_key('RollFile') and self.config['RollFile'] and \
           self.config.has_key('Label') and self.config['Label']:
            editFiles = []
            cp = '/bin/cp'
            self.RollDst = self.config['BackupPath'] + '/' + dateVal + '_' + self.config['Label'] + '.conf'
            self.logger.debug('dst rollback file: %s' % self.RollDst)
            if not os.system("%s --preserve=mode,ownership %s %s %s" % \
                    (cp, self.config['RollFile'], self.RollDst, self.log)) == 0:
                raise Exception, "Failed to copy %s to %s" % \
                    (self.config['BackupPath'], self.RollDst)
            editFiles.append(self.RollDst)
            methodDict = { self.RollDst : '_rollback' }
            super(backup, self).__call__(editFiles=editFiles, methodDict=methodDict)
        else:
            raise Exception, 'Failed to get RollDate and Label parametters from backup config file'
    def _rollback(self):
        import re, os, sys
        lines = []
        for line in self.linesRef:
            try:
                if re.match('BackupPath\s?=\s?.*$', line):
                    line = re.sub('(?P<BackupPath>BackupPath\s?=\s?).*', r'\g<BackupPath>%s' % self.config['BackupPath'], line)
                    self.logger.error('Replacing \'BackupPath\' parametter in \'%s\' file to: %s' % \
                            (self.RollDst, self.config['BackupPath']))
                if re.match('RollDate\s?=\s?\d{14}', line):
                    line = re.sub('(?P<roll>RollDate\s?=\s?).*', r'\g<roll>%s' % dateVal, line)
                    self.logger.error('Replacing \'RollDate\' parametter in \'%s\' file to: %s' % \
                                     (self.RollDst, dateVal))
                if re.match('RollFiles\s?=\s?.*', line):
                    line = re.sub('(?P<files>RollFiles\s?=\s?).*', r'\g<files>%s' % self.config['BackupFiles'], \
                                  line)
                    self.logger.error('Replacing \'RollFiles\' parametter in \'%s\' file to: %s' % \
                                     (self.RollDst, self.config['BackupFiles']))
            except:
                self.logger.error('Unable to modify \'%s\' file' % self.RollDst)
                self.logger.error(traceback.format_exc())
            lines.append(line)
        self.file.writelines(lines)
        

class rollback(builder):
    def __call__(self, *args, **kwargs):
        import sys
        try:
            rollDate = self.config['RollDate']
            self.logger.error("Starting the rollback to: %s" % rollDate)
        except:
            self.logger.error("RollDate parametter is not define in the config file! skiping the rollback")
            raise Exception, "%104%"
        if self.config['RollFiles']:
            self.logger.info("Starting to Rollback")
            CopyUtils(Files=self.config['RollFiles'], Path=self.config['BackupPath'], log=self.log).RollBack(extention=rollDate + '_')
            self.logger.error("Successfully finished the Rollback to %s." % rollDate)
        else:
            self.logger.error("Files and Directoris parametter are empty. there was nothing to rollbak.")

class os_ip_change(builder):
    def __call__(self, editFiles):
        import os
        methodDict = { 'hosts' : '_hosts',
                       'network' : '_network',
                     }
        for file in editFiles:
            file = os.path.basename(file)
            if file.startswith('ifcfg-bond'):
                methodDict[file] = '_bond'
        super(os_ip_change, self).__call__(editFiles=editFiles, methodDict=methodDict)
    def _hosts(self):
        import re, string, sys
        serverlist = []
        lines = []
        for line in self.linesRef:
            if re.search('^(:?#\s+(:?Do|that)|.*localhost)', line):
                lines.append(line)
        #serverlist = re.split(',[\t\s]?', self.config['ServerIPInfo'][0])
        '''
        serverlist = re.sub('\$HOSTNAME', self.config['Hostname'], serverlist)
        if re.search('\$OTHERHOST', serverlist):
            serverlist = re.sub('\$OTHERHOST', OtherHost(self.config['Hostname']), serverlist)
        while re.search('(\$BOND\d+([\:|\.]\d+)?_RIP)', serverlist):
            rip = re.search('(\$BOND\d+([\:|\.]\d+)?_RIP)', serverlist).group(1)
            serverlist = re.sub('(\$BOND\d+([\:|\.]\d+)?_RIP)', self.config[rip[1:]], serverlist, 1)
        serverlist = re.split(',[\t\s]?', serverlist)
        '''
        lines += self.iplistNG(serverlist)
        try:
            if self.config['OtherHostsIPs'] == '': raise Exception, 'OtherHostsIPs is empty...'
            hostsIPs = re.split(',[\t\s]?', self.config['OtherHostsIPs'])
        except:
            self.logger.error(traceback.format_exc())
            self.logger.error('No extra ips where added: OtherHostsIPs was not configured')
        else:
            lines += self.iplistNG(hostsIPs)
        self.file.writelines(lines)
    def _network(self):
        import re
        lines = []
        v6flag = 'no'
        v6gw = 'GATEWAY'
        vskip = 'GATEWAY|IPV6_DEFAULTGW'    
        if self.config['_'](self.config['Section'],'v6_%s' % self.config['Hostname'], False):
            v6flag = 'yes'
            if self.config['DG'].find(':') > -1:
                v6gw = 'IPV6_DEFAULTGW'
        for line in self.linesRef:
            arg = line.split('=')
            if re.search('%s' % vskip, arg[0]):
                continue 
            else:
                line = re.sub('(?P<hostname>HOSTNAME=).*', r'\g<hostname>%s' % self.config['Hostname'], line) 
                line = re.sub('(?P<v6net>NETWORKING_IPV6=).*', r'\g<v6net>%s' % v6flag , line) 
                lines.append(line)
        lines.append('%s=%s\n' %(v6gw,self.config['DG']))
        self.file.writelines(lines)
        
    def _bond(self):
        import re
        lines = []
        skip = 'IPADDR|NETMASK|NETWORK|BROADCAST|IPV6ADDR|IPV6INIT|BONDING_OPTS'
        index = re.search('(\ifcfg-bond(\d+([\:|\.]\d+)?))', self.file.name).group(2)
        bonds = [bond for bond in self.config.keys() if bond.startswith('BOND%s_' % index)]
        v6s = [v6 for v6 in self.config.keys() if v6.startswith('V6_BOND%s_' % index)]
        if bonds and (not v6s):
            netel = self.networkelements(bonds,index)
        elif v6s and (not bonds):
            netel = self.networkelements(v6s,index)
        elif v6s and bonds:
            netel = self.networkelements(bonds + v6s,index)
        else:
            self.logger.error('Please configure IPs : No IPs were found...')  
        for line in self.linesRef:
            arg = line.split('=')
            if re.search('%s' % skip, arg[0]):
                continue
            else:
                lines.append(line)
        lines += netel.values()    
        self.file.writelines(lines)    
    def networkelements(self, vlist,index): 
        from Pynet import IPCalc
        import Pyconstruct.ipcalc as ipcalc
        ip = ''
        mask = ''
        prefix = ''
        netdict = {}
        ipv6 = ''
        for el in vlist:
           if el == 'BOND%s_RIP' %index : 
               ip = self.config[el]
           if el == 'BOND%s_MASK' % index:
               mask = self.config[el] 
           if el == 'BOND%s_NEXT_HOP' % index: 
               hop = self.config[el]  
           if el == 'V6_BOND%s_RIP' %index : 
               ipv6 = self.config[el]
           if el == 'V6_BOND%s_PREFIX' %index :
               prefix = self.config[el] 
        if ip and mask:     
            calc = IPCalc(ip=ip, subnet=mask)
            netdict['IPADDR'] = 'IPADDR=%s\n' % ip
            netdict['NETMASK'] = 'NETMASK=%s\n' % mask
            netdict['BROADCAST'] = 'BROADCAST=%s\n' % calc.calcBroadcast()
            netdict['NETWORK'] = 'NETWORK=%s\n' % calc.calcNet()
            if (self.config.get('_',None)):
                Continue_Flag = None
            if self.config['_'](self.config['Section'], 'bonding_opts', False):
                bonding_opts = self.config['_'](self.config['Section'], 'bonding_opts')
                Continue_Flag = '1'
            else: 
                for SEC in self.config['sysConfig'].sections():
                    if self.config['_'](SEC, 'type', False) and self.config['_'](SEC, 'type', False).upper() == 'NETWORK' \
                       and  self.config['_'](SEC, 'nexthop', False) == hop and self.config['_'](SEC, 'bonding_opts', False):
                            bonding_opts = self.config['_'](SEC,'bonding_opts')
                            Continue_Flag = '1'
                            break
            if not Continue_Flag and self.config.has_key('bonding_opts'):
                bonding_opts = self.config['bonding_opts']
            elif not Continue_Flag:
                bonding_opts = '"mode=active-backup miimon=100"' 
        elif self.config.has_key('bonding_opts'):
            bonding_opts = self.config['bonding_opts']
        else:
            bonding_opts = '"mode=active-backup miimon=100"'  
        if ipv6 and prefix:
            network = ipcalc.Network(ipv6+'/'+prefix)
            if ipv6 in network:
                netdict['IPV6ADDR'] = 'IPV6ADDR=%s/%s\n' % (ipv6,prefix)
                netdict['IPV6INIT'] = 'IPV6INIT=yes\n'
            else:
                raise Exception,"%s is not part of V6 network" % ip 
        netdict['BONDING_OPTS'] = 'BONDING_OPTS=%s\n' % bonding_opts
        return netdict    
    def iplist(self, _list):
        import re, sys
        ips = {}
        if len(_list)>0:
            for x in _list:
                ip, names = x.rsplit(':', 1)
                names = re.sub('%', '  ', names)
                ips[ip.strip()] = names.strip()
        return ips
    def iplistNG(self, _list):
        import re, sys
        ips = []
        if len(_list)>0:
            for x in _list:
                if x.startswith('#'):
                    x = re.sub('%|:', '  ', x)
                    ips.append('%s\n' % x)
                elif x:
                    try:
                        ip, names = x.rsplit(':', 1)
                    except:
                        self.logger.error('SplitError', 'Ban line format, Got \"%s\" Expect: <IP>:<alias...>' % x)
                        raise
                    names = re.sub('%', '  ', names)
                    ips.append('%s\t%s\n' % (ip.strip(), names.strip()))
        return ips
    def addlines(self, dict):
        lines = []
        if len(dict.keys())>0:
            for ip, names in sorted(dict.iteritems()):
                lines.append('%s\t%s\n' % (ip, names))
        return lines


class vrts(builder):
    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        from Pyfunc import GetHash, DigHostsIP 
        import os
        import glob
        super(vrts, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
        self.config['Hostname'] = self.config.get('_',None) and self.config['_'](self.config['Section'], 'hostname', False) or os.environ['HOSTNAME']
        self.CLUSTER_VIP = self.eval_func(value='CLUSTER_VIP')
        self.SNMP = self.eval_func(value='SNMP')
        if self.config['ClusterMode'] == 'redundant' and self.config['OtherHostname'] == '':
            self.config['OtherHostname'] = OtherHost(self.config['Hostname'])
            if self.config['Hostname'].endswith('a') or self.config['Hostname'].endswith('A'):
                self.config['ServerInfo'] = 'primary'
            else:
                self.config['ServerInfo'] = 'secondary'
          
        if not self.config['SetClusterID']:
            self.SetClusterID=self.CLUSTER_VIP.split('.')[3]
        else:
            self.SetClusterID=self.config['SetClusterID']

        if not self.config['CLUSTER_MASK'] :
           if  self.config.has_key('Interface') and self.config['Interface']:
               get_netmask = '/etc/sysconfig/network-scripts/ifcfg-%s' % self.config['Interface']
           else:
               get_netmask = '/etc/sysconfig/network-scripts/ifcfg-bond0'
           self.CLUSTER_MASK = GetHash(ret='NETMASK',file = get_netmask)
        else:
           self.CLUSTER_MASK = self.config['CLUSTER_MASK']
        
        if not self.config['NETWORKHOSTS']:
           self.NETWORKHOSTS = GetHash(ret='GATEWAY',file='/etc/sysconfig/network')
        else:
           self.NETWORKHOSTS = self.config['NETWORKHOSTS']
         
    


    def __call__(self, editFiles):
        methodDict = { 'llthosts' : '_llthosts',
                        'llttab' : '_llttab',
                        'gabtab' : '_gabtab',
                        '/etc/VRTSvcs/conf/sysname' : '_sysname',
                        }

        if self.config.has_key('N_G') and self.config['N_G'].upper() == 'YES' :
            self.logger.info('[I] Runnig as a new generation')
            methodDict['/etc/VRTSvcs/conf/config/main.cf'] = '_cf_rulles' 
        else:
            self.logger.info('[I] Runnig as a old version')
            methodDict['/etc/VRTSvcs/conf/config/main.cf'] = '_cf_old' 

        super(vrts, self).__call__(editFiles=editFiles, methodDict=methodDict)

    def eval_func(self,value):
        from Pyfunc import GetHash, DigHostsIP 
        import re
        import sys
        try:
            re.search('^[a-zA-Z0-9_]+\(.*\)$',self.config[value]).group()
            eval_value = eval(self.config[value])
        except AttributeError:
            self.logger.debug('[W] %s' % traceback.format_exc())
            eval_value = self.config[value]
        except :
            print self.config[value]
            self.logger.error(traceback.format_exc())
            raise Exception, 'Failed to execute %s' % self.config[value] 
        return eval_value

    def _llthosts(self):
        lines = []
        if self.config['ClusterMode'] == 'single':
            lines.append('0 %s\n' % self.config['Hostname'])
        elif self.config['ClusterMode'] == 'redundant':
            if self.config['ServerInfo'] == 'primary':
                lines.append('0 %s\n' % self.config['Hostname'])
                lines.append('1 %s\n' % self.config['OtherHostname'])
            else:
                lines.append('0 %s\n' % self.config['OtherHostname'])
                lines.append('1 %s\n' % self.config['Hostname'])
        else:
            raise Exception, "ClusterMode must be single/redundant given: %s" % \
                            self.config['ClusterMode']
        self.file.writelines(lines)

    def _llttab(self):
        import os, re
        if not (self.config['ClusterMode'] == 'single' or self.config['ClusterMode'] == 'redundant'):
            raise Exception, "ClusterMode must be single/redundant given: %s" % \
                    self.config['ClusterMode']
        lines = []
        lines.append('set-node %s\n' % self.config['Hostname'])
        lines.append('set-cluster %s\n' % self.SetClusterID)
        if self.config.has_key('HeartBit') and self.config['HeartBit']:
            nicA, nicB = self.config['HeartBit'].split(', ')
            lines.append('link %s %s - ether - -\n' % (nicA, nicA))
            lines.append('link %s %s - ether - -\n' % (nicB, nicB))
        if self.config.has_key('LowPri') and self.config['LowPri'] :
            lowpri=os.popen("ifconfig %s" % self.config['LowPri'])  
            for line in lowpri.readlines():
                try :
                    HWaddr=re.search('(\s*)(.*)(HWaddr)(.*)',line).group(4)            
                except:
                    continue
            if HWaddr:
                lines.append('link-lowpri %s eth-%s - ether - - '% (self.config['LowPri'],HWaddr[1:]))
            else:
                raise Exception, '[E] Missing MAC Information for %s' %self.config['LowPri']
        if not self.config['HeartBit'] and not  self.config['LowPri'] :
            raise Exception, '[E] Missing HeartBit Information' 

        self.file.writelines(lines)

    def _gabtab(self):
        import re
        if self.config['ClusterMode'] == 'single': num = 1
        if self.config['ClusterMode'] == 'redundant': num = 2
        line = re.sub('^(?P<gab>/sbin/gabconfig\s.*-n)\d', r'\g<gab>%s' % num, self.linesRef[0])
        self.file.writelines(line)


    def _sysname(self):
        lines = []
        lines.append(self.config['Hostname'])
        self.file.writelines(lines)


    def _cf_rulles(self):
        Res_del = None
        Res_Dep_del = None
        Res_Dep_add = None
        Res_add = None
        Group_del = None
        Group_add = None

        for k,v  in self.config.iteritems():        
            if k.startswith('Res_del_') and v : Res_del = 'O.K'
            if k.startswith('Res_Dep_del_') and v: Res_Dep_del = 'O.K'
            if k.startswith('Res_Dep_add_') and v : Res_Dep_add = 'O.K'
            if k.startswith('Res_add_') and v : Res_add = 'O.K'
            if k.startswith('Group_to_Delete_') and v : Group_del = 'O.K'
            if k.startswith('Group_to_Add_') and v : Group_add = 'O.K'


        if Res_Dep_del : self.linesRef = self._cf_delete_req(self.linesRef)
        if Res_del : self.linesRef = self._cf_delete_res(self.linesRef)
        if Group_del : self.linesRef = self._cf_delete_group(self.linesRef)
        if Group_add : self.linesRef = self._cf_add_group(self.linesRef)
        if Res_Dep_add : self.linesRef = self._cf_add_req(self.linesRef)
        if Res_add : self.linesRef = self._cf_add_res(self.linesRef)

        if ((self.config.get('_',None)) and self.config['_'](self.config['Section'], 'local_disk', False) \
        and (self.config.get('_',None)) and  self.config['_'](self.config['Section'], 'local_disk', False).upper() != 'YES')\
        or ((self.config.get('_',None)) and not self.config['_'](self.config['Section'], 'local_disk', False)\
        and (self.config['mounts'])): 
            self.linesRef = self._cf_mounts(self.linesRef)
        self._cf()

    def _cf_delete_group(self, linesRef, dg = None):
        import re
        tmp_linesRef = []
        Append = 'True'
        Loop = 'Yes'
        self.logger.info('[I] Delete Group')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                Append = 'True'
                Loop = 'Yes'
            try:
                if Loop == 'Yes':
                    Loop = 'No'
                    if dg:
                        for k in dg.keys():
                            if k.startswith('Group_to_Delete_'):
                                T_List = []
                                for T in dg[k].split(','):
                                    T_List.append(T.strip())
                                if Group in T_List:
                                    self.logger.info('[I] Delete Group %s' % Group)
                                    Append = 'False'
                                    break
                    else:
                        for k in self.config.keys():
                            if k.startswith('Group_to_Delete_'):
                                T_List = []
                                for T in self.config[k].split(','):
                                    T_List.append(T.strip())
                                if Group in T_List:
                                    self.logger.info('[I] Delete Group %s' % Group)
                                    Append = 'False'
                                    break
            except:
                pass
            if Append == 'True': tmp_linesRef.append(line)
        return tmp_linesRef


    def _cf_delete_res(self, linesRef):
        import re
        tmp_linesRef = []
        Append = 'True'
        self.logger.info('[I] Delete Resource ')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                Append = 'True'
            try:
                for k in self.config.keys():
                    if k.startswith('Res_del_') and self.config[k].has_key(Group):
                        for D in self.config[k][Group]:
                            if re.search('%s' %D, line):
                                Append = 'False'
                                self.logger.info('[I] Delete line %s' % line)
                                break
            except:
                pass 
            if Append == 'True': tmp_linesRef.append(line)
            if Append == 'False' and re.search('[\s\t]*\)[\s\t]?$',line) or re.search('.*\(.*\).*\)[\s\t]?$',line):
                Append = 'True'
        return tmp_linesRef

    def _cf_delete_req(self, linesRef):
        import re
        tmp_linesRef = []
        Append = 'True'
        self.logger.info('[I] Delete Dependency ')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
            try:
                for k in self.config.keys():
                    if k.startswith('Res_Dep_del_') and self.config[k].has_key(Group):
                        for D in self.config[k][Group]:
                            if re.search('%s' %D, line):
                                Append = 'False'
                                self.logger.info('[I] Delete Dependency %s' %line)
                                break
            except:
                pass 
            if Append == 'True': tmp_linesRef.append(line)
            Append = 'True'
        return tmp_linesRef

    def _cf_add_req(self, linesRef):
        import re
        tmp_linesRef = []
        Append = 'False'
        self.logger.info('[I] Append Dependency')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                Append = 'True'
            if  re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('^[\s\t]*\)[\s\t]*', line)\
            and Append == 'True':
                 for k in self.config.keys():
                    if k.startswith('Res_Dep_add_') and self.config[k].has_key(Group):
                        for D in self.config[k][Group]:
                            tmp_linesRef.append('\t' + D +'\n')
                            self.logger.info('[I] Append Dependency %s' % D)
                 Append = 'False'
        return tmp_linesRef
    

    def _cf_add_res(self, linesRef):
        import re
        tmp_linesRef = []
        Append = 'False'
        self.logger.info('[I] Append Resource')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                Append = 'True'
            if  re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('^[\s\t]*\)[\s\t]*', line)\
            and Append == 'True':
                 for k in self.config.keys():
                    if k.startswith('Res_add_') and self.config[k].has_key(Group):
                        for D in self.config[k][Group]:
                            if  re.search('.*\(.*\).*\([\s\t]?$',line) or re.search('[\s\t]*\([\s\t]?$',line)\
                                or re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('[\s\t]*\)[\s\t]?$',line):
                                tmp_linesRef.append('\t' + D +'\n')
                                self.logger.info('[I] Append %s' %D)
                            else:
                                tmp_linesRef.append('\t\t' + D +'\n')
                                self.logger.info('[I] Append %s' %D)
                 Append = 'False'
        return tmp_linesRef



    def _cf_add_group(self, linesRef):
        import re, os
        tmp_linesRef = []
        Groups = []
        self.logger.info('[I] Add Group')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Groups.append(re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2))
        for k in self.config.keys():
            if k.startswith('Group_to_Add_'):
                for G in self.config[k].keys():
                    if G in Groups:
                        if self.config[k][G].upper() == 'EXIT':
                            raise Exception, 'The Group %s is existing' % G
                        elif self.config[k][G].upper() == 'NEW':
                            tmp_linesRef = self._cf_delete_group(tmp_linesRef, dg = {'Group_to_Delete_' : G }) 
                            tmp_linesRef.append('group %s (\n' % G )
                            tmp_linesRef.append('\tSystemList = { %s = 0 }\n'% os.environ['HOSTNAME'])
                            tmp_linesRef.append('\tAutoStartList = { %s }\n'% os.environ['HOSTNAME'])
                            tmp_linesRef.append('\t)\n')
                            self.logger.info('[I] Add Group %s' %G)
                        elif self.config[k][G].upper() == 'IGNORE':
                            pass 
                    else:
                        tmp_linesRef.append('group %s (\n' % G )
                        tmp_linesRef.append('\tSystemList = { %s = 0 }\n'% os.environ['HOSTNAME'])
                        tmp_linesRef.append('\tAutoStartList = { %s }\n'% os.environ['HOSTNAME'])
                        tmp_linesRef.append('\t)\n')
                        self.logger.info('[I] Add Group %s' %G)
                   
        return tmp_linesRef



    def _cf_mounts(self, linesRef):
        import re
        tmp_linesRef = []
        Group = None
        self.logger.info('[I] Add Mounts,LV and DEP')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                if self.config['GroupName'] == re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2):
                    Group = 'O.K'
            
            if Group and re.search('[\s\t]*\)[\s\t]?$', line) or re.search('.*\(.*\).*\)[\s\t]?$',line):
                lv = []
                for mount in self.config['mounts'].split(',') :
                    tmp_linesRef.append('\tLVMLogicalVolume %s ( \n' % mount.split(':')[1])
                    tmp_linesRef.append('\t\tLogicalVolume = %s \n' % mount.split(':')[1])
                    tmp_linesRef.append('\t\tVolumeGroup = %s \n' % self.config['VG']) 
                    tmp_linesRef.append('\t)\n')
                    lv.append(mount.split(':')[1])
                    tmp_linesRef.append('\tMount Mount_%s (\n' % mount.split(':')[0].strip())
                    tmp_linesRef.append('\t\tMountPoint = "%s"\n' %mount.split(':')[2])
                    tmp_linesRef.append('\t\tBlockDevice = "/dev/mapper/%s-%s" \n' %(self.config['VG'],mount.split(':')[1]))
                    tmp_linesRef.append('\t\tFSType = %s \n' % self.config['FSType'])
                    tmp_linesRef.append('\t\tFsckOpt = "-n" \n')
                    tmp_linesRef.append('\t)\n')

                    tmp_linesRef.append ('\tMount_%s requires %s\n' % (mount.split(':')[0].strip(), mount.split(':')[1])) 

                if self.config['ClusterMode'] == 'single':
                    self.logger.info('Adding \'LVMVolumeGroup\' for single node')
                    tmp_linesRef.append('\tLVMVolumeGroup %s (\n' % (self.config['VG']))
                    tmp_linesRef.append('\t\tVolumeGroup = %s\n' % (self.config['VG']))
                    tmp_linesRef.append('\t)\n')
                    tmp_linesRef.append('\n')
                    for L in lv:
                        tmp_linesRef.append ('\t%s requires %s\n ' %(L, self.config['VG']))
                Group = None
        return tmp_linesRef

    def _cf(self):
        import os, re
        # Setup VARs
        if self.config['ClusterMode'] == 'redundant':
            if self.config['ServerInfo'] == 'primary':
                primaryHost = self.config['Hostname']
                secondaryHost = self.config['OtherHostname']
            else:
                primaryHost = self.config['OtherHostname']
                secondaryHost = self.config['Hostname']
        else:
            primaryHost = self.config['Hostname']
        parenthesis = 'close'
        systemDone = 0
        vg = ''
        added = 0
        lv = []
        LVMVG = 1
        LVMVGp = 'close'
        requires = 0
        lines = []
        Append = 'True'
        for line in self.linesRef:
            # Searching: captured block 'end/close'
            if parenthesis == 'open':
                if re.search('^[\s\t]*\)[\s\t]*', line):
                    parenthesis = 'close'
                continue
            # Searching: system blocks, raise stsyemDone = 1 so it will enter only once.
            if re.search('^[\s\t]*system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\([\t\s]?$', line):
                # Check that if system line will appear again it will be ignored
                if systemDone == 1:
                    parenthesis = 'open'
                    systemDone = 0
                    continue
                systemDone = 1
                self.logger.info('Starting editing the \'system\' block.')
                space = re.search('^([\s\t]*)system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\(', line).group(1)
                parenthesis = 'open'
                lines.append('%ssystem %s (\n' % (space, primaryHost))
                self.logger.debug('Addnig: system %s (' % primaryHost)
                lines.append('%s\t)\n' % space)
                self.logger.debug('Addnig: %s\t)' % space)
                if self.config['ClusterMode'] == 'redundant':
                    lines.append('%ssystem %s (\n' % (space, secondaryHost))
                    self.logger.debug('Addnig: %ssystem %s (' % (space, secondaryHost))
                    lines.append('%s\t)\n' % space)
                    self.logger.debug('Addnig:%s\t)' % space)
            # Searching: group blocks
            elif re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                space = re.search('^([\s\t]*)group[\t\s]+\w+[\t\s]+\(', line).group(1) + '\t'
                self.logger.info('Starting editing the \'%s\' block.' % \
                                (re.search('^[\s\t]*group[\t\s]+(\w+)[\t\s]+\(', line).group(1)))
                lines.append(line)
                parenthesis = 'open'
                if self.config['ClusterMode'] == 'redundant':
                    lines.append('%sSystemList = { %s = 0, %s = 1 }\n' % \
                            (space, primaryHost, secondaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0, %s = 1 }' % \
                                      (primaryHost, secondaryHost))
                    Vrts_Group='Daemons'
                    if self.config.get('_',None) and self.config['_']('MWAS', 'identifier_ha', False)\
                    and (self.config['_']('MWAS', 'identifier_ha') == 'AA'):
                        Vrts_Group='ID'
                    
                    Parallel = set(['Daemons',Vrts_Group])
                    for P in self.config['Parallel_Group'].split(','):
                        Parallel.add(P.strip()) 
                    if Parallel.intersection([re.search('(^[\s\t]*group[\t\s])(.*)([\t\s]+\()', line).group(2)]):
                       lines.append('%sParallel = 1\n' % space) 
                       self.logger.debug('Addnig: Parallel = 1')
                    lines.append('%sAutoStartList = { %s, %s }\n' % (space, primaryHost, secondaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s, %s }' % (primaryHost, secondaryHost))
                else:
                    lines.append('%sSystemList = { %s = 0 }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0 }' % primaryHost)
                    lines.append('%sAutoStartList = { %s }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s }' % primaryHost)

                lines.append('%s)\n' % space)
            # Searching: SNMP block
            elif re.search('^[\s\t]*NotifierMngr Notifier[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'snmp\' block.')
                space = re.search('^([\s\t]*)NotifierMngr Notifier[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sCritical = 0\n' % space)
                self.logger.debug('Adding: Critical = 0')
                lines.append('%sSnmpConsoles = { %s }\n' % (space, self.listsnmp(self.SNMP)))
                self.logger.debug('Adding: SnmpConsoles = { %s }' % (self.listsnmp(self.SNMP)))
                lines.append('%s)\n' % space)
                self.logger.debug('Adding: )')
            # Searching: NIC EdnNIC block
            elif re.search('^[\s\t]*NIC EdnNIC[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'NIC EdnNIC\' block.')
                space = re.search('^([\s\t]*)NIC EdnNIC[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sMii = 0\n' % space)
                self.logger.debug('Adding: Mii = 0')
                lines.append('%sNetworkHosts = { %s }\n' %(space, self.listip(self.NETWORKHOSTS)))
                self.logger.debug('NetworkHosts = { %s }' % self.NETWORKHOSTS)
                lines.append('%s)\n' % space)
            # Searching: IP EdnVIP
            elif re.search('^[\s\t]*IP EdnVIP[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'IP EdnVIP\' block.')
                space = re.search('^([\s\t]*)IP EdnVIP[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sAddress = "%s"\n' % (space, self.CLUSTER_VIP))
                self.logger.debug('Adding: Address = "%s"' % self.CLUSTER_VIP)
                lines.append('%sNetMask = "%s"\n' % (space, self.CLUSTER_MASK))
                self.logger.debug('Adding: NetMask = "%s"' % self.CLUSTER_MASK)
                lines.append('%s)\n' % space)
                self.logger.debug('Addnig: )')
            elif (re.match('^[\s\t]+EdnVIP requires \w+[\t\s]?$', line) or requires) and added:
                if not requires:
                    space = re.search('^([\s\t]+)EdnVIP requires', line).group(1)
                    requires = 1
                if re.match('^[\s\t]*\n$', line) and self.config['ClusterMode'] == 'single':
                    requires = 0
                    for L in lv:
                        lines.append('%s%s requires %s\n' % (space, L, vg))
                        self.logger.debug('Adding: %s requires %s\n' % (L, vg))
                lines.append(line)
            else:
                if Append == 'True': lines.append(line)

        cmd = '/opt/VRTSvcs/bin/hacf'
        cftocmd = '-cftocmd'
        verify = '-verify'
        generate = '-generate'
        path = os.path.dirname(self.fileToEdit)
        self.file.writelines(lines)
        self.file.close()
        self.logger.error('Finished editing main.cf file. Going to validate the changes:')
        self.logger.error('Running: \'hacf -verify <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, verify, path, self.log)):
            self.logger.error('%s was verified.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -verify <VRTS config path>\''
        self.logger.error('Running: \'hacf -generate <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, generate, path, self.log)):
            self.logger.error('%s was ganerated.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -generate <VRTS config path>\''
        self.logger.error('Running: \'hacf -cftocmd <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, cftocmd, path, self.log)):
            self.logger.error('%s was modified acording to the new main.cf file.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -cftocmd <VRTS config path>\''
    def listip(self, l):
        tmp = l.split(', ')
        list = []
        for i in tmp:
            i = '"' + i + '"'
            list.append(i)
        return (', ').join(list)
    def listsnmp(self, l):
        tmp = l.split(', ')
        list = []
        for i in tmp:
            i = '"' + i + '"' + ' = Information'
            list.append(i)
        return (', ').join(list)

    def _cf_old(self):
        import os, re
        # Setup VARs
        if self.config['ClusterMode'] == 'redundant':
            if self.config['ServerInfo'] == 'primary':
                primaryHost = self.config['Hostname']
                secondaryHost = self.config['OtherHostname']
            else:
                primaryHost = self.config['OtherHostname']
                secondaryHost = self.config['Hostname']
        else:
            primaryHost = self.config['Hostname']
        parenthesis = 'close'
        systemDone = 0
        vg = ''
        added = 0
        lv = []
        LVMVG = 1
        LVMVGp = 'close'
        requires = 0
        lines = []
        for line in self.linesRef:
            # Searching: captured block 'end/close'
            if parenthesis == 'open':
                if re.search('^[\s\t]*\)[\s\t]*', line):
                    parenthesis = 'close'
                continue
            # Searching: system blocks, raise stsyemDone = 1 so it will enter only once.
            if re.search('^[\s\t]*system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\([\t\s]?$', line):
                # Check that if system line will appear again it will be ignored
                if systemDone == 1:
                    parenthesis = 'open'
                    systemDone = 0
                    continue
                systemDone = 1
                self.logger.info('Starting editing the \'system\' block.')
                space = re.search('^([\s\t]*)system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\(', line).group(1)
                parenthesis = 'open'
                lines.append('%ssystem %s (\n' % (space, primaryHost))
                self.logger.debug('Addnig: system %s (' % primaryHost)
                lines.append('%s\t)\n' % space)
                self.logger.debug('Addnig: %s\t)' % space)
                if self.config['ClusterMode'] == 'redundant':
                    lines.append('%ssystem %s (\n' % (space, secondaryHost))
                    self.logger.debug('Addnig: %ssystem %s (' % (space, secondaryHost))
                    lines.append('%s\t)\n' % space)
                    self.logger.debug('Addnig:%s\t)' % space)
            # Searching: group blocks
            elif re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                space = re.search('^([\s\t]*)group[\t\s]+\w+[\t\s]+\(', line).group(1) + '\t'
                self.logger.info('Starting editing the \'%s\' block.' % \
                                (re.search('^[\s\t]*group[\t\s]+(\w+)[\t\s]+\(', line).group(1)))
                lines.append(line)
                parenthesis = 'open'
                if self.config['ClusterMode'] == 'redundant':
                    lines.append('%sSystemList = { %s = 0, %s = 1 }\n' % \
                            (space, primaryHost, secondaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0, %s = 1 }' % \
                                      (primaryHost, secondaryHost))
                    Vrts_Group='Daemons'
                    if self.config.get('_',None) and self.config['_']('MWAS', 'identifier_ha', False) and (self.config['_']('MWAS', 
'identifier_ha') == 'AA'):
                        Vrts_Group='ID'
                    if set(['Daemons',Vrts_Group]).intersection([re.search('^[\s\t]*group[\t\s]+(\w+)[\t\s]+\(', line).group(1)]):
                       lines.append('%sParallel = 1\n' % space) 
                       self.logger.debug('Addnig: Parallel = 1')
                    lines.append('%sAutoStartList = { %s, %s }\n' % (space, primaryHost, secondaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s, %s }' % (primaryHost, secondaryHost))
                else:
                    lines.append('%sSystemList = { %s = 0 }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0 }' % primaryHost)
                    lines.append('%sAutoStartList = { %s }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s }' % primaryHost)
                lines.append('%s)\n' % space)
            # Searching: SNMP block
            elif re.search('^[\s\t]*NotifierMngr Notifier[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'snmp\' block.')
                space = re.search('^([\s\t]*)NotifierMngr Notifier[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sCritical = 0\n' % space)
                self.logger.debug('Adding: Critical = 0')
                lines.append('%sSnmpConsoles = { %s }\n' % (space, self.listsnmp(self.SNMP)))
                self.logger.debug('Adding: SnmpConsoles = { %s }' % (self.listsnmp(self.SNMP)))
                lines.append('%s)\n' % space)
                self.logger.debug('Adding: )')
            # Searching: NIC EdnNIC block
            elif re.search('^[\s\t]*NIC EdnNIC[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'NIC EdnNIC\' block.')
                space = re.search('^([\s\t]*)NIC EdnNIC[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sMii = 0\n' % space)
                self.logger.debug('Adding: Mii = 0')
                lines.append('%sNetworkHosts = { %s }\n' %(space, self.listip(self.NETWORKHOSTS)))
                self.logger.debug('NetworkHosts = { %s }' % self.NETWORKHOSTS)
                lines.append('%s)\n' % space)
            # Searching: IP EdnVIP
            elif re.search('^[\s\t]*IP EdnVIP[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'IP EdnVIP\' block.')
                space = re.search('^([\s\t]*)IP EdnVIP[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sAddress = "%s"\n' % (space, self.CLUSTER_VIP))
                self.logger.debug('Adding: Address = "%s"' % self.CLUSTER_VIP)
                lines.append('%sNetMask = "%s"\n' % (space, self.CLUSTER_MASK))
                self.logger.debug('Adding: NetMask = "%s"' % self.CLUSTER_MASK)
                lines.append('%s)\n' % space)
                self.logger.debug('Addnig: )')
            # disable/enable LVMVolumeGroup and requires
            elif re.match('^[\s\t]+LogicalVolume = \w[\w_-]+[\t\s]?$', line):
                l = re.match('^[\s\t]+LogicalVolume = (\w[\w_-]+)', line).group(1)
                lv.append(l)
                lines.append(line)
            elif re.match('^[\s\t]+VolumeGroup = \w[\w_-]+[\t\s]?$', line) and vg == '':
                vg = re.match('^[\s\t]+VolumeGroup = (\w[\w_-]+)', line).group(1)
                self.logger.info('Getting VG from main.cf: %s' % vg)
                lines.append(line)
            elif re.match('^[\s\t]+LVMVolumeGroup .*\([\t\s]?$', line) or LVMVGp == 'open':
                if LVMVGp == 'close':
                    LVMVGp = 'open'
                    LVMVG = 0
                if re.search('^[\s\t]*\)[\s\t]*', line):
                    LVMVGp = 'close'
                if self.config['ClusterMode'] == 'redundant':
                    self.logger.info('Removing: %s' % line[:-1])
                    continue
                lines.append(line)
            elif re.match('^[\s\t]+Mount Mount_\w+', line) and LVMVG:
                LVMVG = 0
                added = 1
                if self.config['ClusterMode'] == 'single':
                    self.logger.info('Adding \'LVMVolumeGroup\' for single node')
                    space = re.search('^([\s\t]+)Mount Mount_', line).group(1)
                    lines.append('%sLVMVolumeGroup %s (\n' % (space, vg))
                    lines.append('%s\tVolumeGroup = %s\n' % (space, vg))
                    lines.append('%s\t)\n' % space)
                    lines.append('\n')
                lines.append(line)
            elif re.match('^[\s\t]+\w+_lv requires \w+_vg[\t\s]?$', line) and \
                          self.config['ClusterMode'] == 'redundant':
                   self.logger.debug('Removing: %s' % line[:-1])
                   continue
            elif (re.match('^[\s\t]+EdnVIP requires \w+[\t\s]?$', line) or requires) and added:
                if not requires:
                    space = re.search('^([\s\t]+)EdnVIP requires', line).group(1)
                    requires = 1
                if re.match('^[\s\t]*\n$', line) and self.config['ClusterMode'] == 'single':
                    requires = 0
                    for L in lv:
                        lines.append('%s%s requires %s\n' % (space, L, vg))
                        self.logger.debug('Adding: %s requires %s\n' % (L, vg))
                lines.append(line)
            else:
                lines.append(line)

        cmd = '/opt/VRTSvcs/bin/hacf'
        cftocmd = '-cftocmd'
        verify = '-verify'
        generate = '-generate'
        path = os.path.dirname(self.fileToEdit)
        self.file.writelines(lines)
        self.file.close()
        self.logger.error('Finished editing main.cf file. Going to validate the changes:')
        self.logger.error('Running: \'hacf -verify <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, verify, path, self.log)):
            self.logger.error('%s was verified.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -verify <VRTS config path>\''
        self.logger.error('Running: \'hacf -generate <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, generate, path, self.log)):
            self.logger.error('%s was ganerated.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -generate <VRTS config path>\''
        self.logger.error('Running: \'hacf -cftocmd <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, cftocmd, path, self.log)):
            self.logger.error('%s was modified acording to the new main.cf file.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -cftocmd <VRTS config path>\''


class racvrts(builder):
    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        from Pyfunc import GetHash, DigHostsIP 
        import os
        import glob
        super(racvrts, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
        self.config['Hostname'] = os.environ['HOSTNAME']
        self.SNMP = self.eval_func(value='SNMP')
        if self.config['ClusterMode'] == 'redundant':
            if self.config['OtherHostname'] == '' and self.config['Primary'] == '':
                if self.config['Hostname'].endswith('a') or self.config['Hostname'].endswith('A'):
                    self.config['Primary'] = self.config['Hostname']
                    self.config['OtherHostname'] = OtherHost(self.config['Hostname'])
                elif self.config['Hostname'].endswith('b') or self.config['Hostname'].endswith('B'):
                    self.config['Primary'] = OtherHost(self.config['Hostname']) 
                    self.config['OtherHostname'] = self.config['Hostname']
            elif self.config['OtherHostname'] and not  self.config['Primary']:
                self.logger.error(traceback.format_exc())
                raise Exception, 'Missing Primary information' 
            elif not self.config['OtherHostname'] and   self.config['Primary']:
                self.logger.error(traceback.format_exc())
                raise Exception, 'Missing OtherHostname information' 

        else:
            self.config['Primary'] = self.config['Hostname'] 
        if not self.config['SetClusterID']:
            self.SetClusterID=self.config['Scan1'].split('.')[3]
        else:
            self.SetClusterID=self.config['SetClusterID']

        if not self.config['CLUSTER_MASK'] :
           if  self.config.has_key('Interface') and self.config['Interface']:
               get_netmask = '/etc/sysconfig/network-scripts/ifcfg-%s' % self.config['Interface']
           else:
               get_netmask = '/etc/sysconfig/network-scripts/ifcfg-bond0'
           self.CLUSTER_MASK = GetHash(ret='NETMASK',file = get_netmask)
        else:
           self.CLUSTER_MASK = self.config['CLUSTER_MASK']
        
        if not self.config['NETWORKHOSTS']:
           self.NETWORKHOSTS = GetHash(ret='GATEWAY',file='/etc/sysconfig/network')
        else:
           self.NETWORKHOSTS = self.config['NETWORKHOSTS']

    def __call__(self, editFiles):
        methodDict = { 'llthosts' : '_llthosts',
                        'llttab' : '_llttab',
                        'gabtab' : '_gabtab',
                        '/etc/VRTSvcs/conf/sysname' : '_sysname',
                        '/etc/VRTSvcs/conf/config/main.cf' : '_cf',
                        }
        super(racvrts, self).__call__(editFiles=editFiles, methodDict=methodDict)

    def eval_func(self,value):
        from Pyfunc import GetHash , DigHostsIP 
        import re
        import sys
        try:
            re.search('^[a-zA-Z0-9_]+\(.*\)$',self.config[value]).group()
            eval_value = eval(self.config[value])
        except AttributeError:
            self.logger.debug('[W] %s' % traceback.format_exc())
            eval_value = self.config[value]
        except :
            print self.config[value]
            self.logger.error(traceback.format_exc())
            raise Exception, 'Failed to execute %s' % self.config[value] 
        return eval_value

    def _llthosts(self):
        lines = []
        i=1
        if self.config['ClusterMode'] == 'single':
            lines.append('0 %s\n' % self.config['Hostname'])
        elif self.config['ClusterMode'] == 'redundant':
                lines.append('0 %s\n' % self.config['Primary'].split(':')[0])
                for Other in self.config['OtherHostname'].split(','):
                    lines.append('%s %s\n' % (i, Other.split(':')[0].strip()))
                    i=i+1
        else:
            raise Exception, "ClusterMode must be single/redundant given: %s" % \
                            self.config['ClusterMode']
        self.file.writelines(lines)

    def _llttab(self):
        import os, re
        if not (self.config['ClusterMode'] == 'single' or self.config['ClusterMode'] == 'redundant'):
            raise Exception, "ClusterMode must be single/redundant given: %s" % \
                    self.config['ClusterMode']
        lines = []
        lines.append('set-node %s\n' % self.config['Hostname'])
        lines.append('set-cluster %s\n' % self.SetClusterID)
        if self.config.has_key('HeartBit') and self.config['HeartBit']:
            for nic in self.config['HeartBit'].split(':')[0].split(','):
                lines.append('link %s %s - ether - -\n' % (nic, nic))
        if self.config.has_key('LowPri') and self.config['LowPri'] :
            lowpri=os.popen("ifconfig %s" % self.config['LowPri'])  
            for line in lowpri.readlines():
                try :
                    HWaddr=re.search('(\s*)(.*)(HWaddr)(.*)',line).group(4)            
                except:
                    continue
            if HWaddr:
                lines.append('link-lowpri %s eth-%s - ether - - '% (self.config['LowPri'],HWaddr[1:]))
            else:
                raise Exception, '[E] Missing MAC Information for %s' %self.config['LowPri']
        if not self.config['HeartBit'] and not  self.config['LowPri'] :
            raise Exception, '[E] Missing HeartBit Information' 

        self.file.writelines(lines)

    def _gabtab(self):
        import re
        num = 1
        if self.config['ClusterMode'] == 'redundant': 
            for Other in self.config['OtherHostname'].split(','):
                num = num + 1
        line = re.sub('^(?P<gab>/sbin/gabconfig\s.*-n)\d', r'\g<gab>%s' % num, self.linesRef[0])
        self.file.writelines(line)

    def _sysname(self):
        lines = []
        lines.append(self.config['Hostname'])
        self.file.writelines(lines)

    def _cf(self):
        import os, re
        # Setup VARs
        if self.config['ClusterMode'] == 'redundant':
            primaryHost = self.config['Primary'].split(':')[0]
            secondaryHost = self.config['OtherHostname']
            Str = ''
            i = 1
            StartList = ''
            for second in secondaryHost.split(','):
                Str=Str+','+second.split(':')[0] +' = '+ str(i)
                StartList = StartList + ',' + second.split(':')[0]
                i=i+1
        else:
            primaryHost = self.config['Hostname']
            Str =''
            StartList = ''
        parenthesis = 'close'
        systemDone = 0
        vg = ''
        added = 0
        requires = 0
        lines = []
        Sid = 0
        Device = 0
        Address = 0
        System = 0
        Group = 1
        PrivMask = 0

        for line in self.linesRef:
            # Searching: captured block 'end/close'
            if parenthesis == 'open':
                if re.search('^[\s\t]*\)[\s\t]*', line):
                    parenthesis = 'close'
                continue
            # Searching: system blocks, raise stsyemDone = 1 so it will enter only once.
            if re.search('^[\s\t]*system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\([\t\s]?$', line) and System ==0:
                # Check that if system line will appear again it will be ignored
                if systemDone == 1:
                    parenthesis = 'open'
                    systemDone = 0
                    continue
                systemDone = 1
                self.logger.info('Starting editing the \'system\' block.')
                space = re.search('^([\s\t]*)system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\(', line).group(1)
                parenthesis = 'open'
                lines.append('%ssystem %s (\n' % (space, primaryHost))
                self.logger.debug('Addnig: system %s (' % primaryHost)
                lines.append('%s\t)\n' % space)
                self.logger.debug('Addnig: %s\t)' % space)
                if self.config['ClusterMode'] == 'redundant':
                    for second in secondaryHost.split(','):
                        lines.append('%ssystem %s (\n' % (space, second.split(':')[0]))
                        self.logger.debug('Addnig: %ssystem %s (' % (space, second))
                        lines.append('%s\t)\n' % space)
                        self.logger.debug('Addnig:%s\t)' % space)
                System = 1
                Group = 0

            elif  re.search('^[\s\t]*SystemList[\t\s]+\=', line):
                if self.config['ClusterMode'] == 'redundant':
                    lines.append('%sSystemList = { %s = 0 %s  }\n' % \
                        (space, primaryHost, Str))
                    self.logger.debug('Addnig: SystemList = { %s = 0 %s  }' % \
                                  (primaryHost, Str))

                else:
                    lines.append('%sSystemList = { %s = 0 }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0 }' % primaryHost)

            elif re.search('^[\s\t]*AutoStartList[\t\s]+\=', line):
                if self.config['ClusterMode'] == 'redundant': 
                    lines.append('%sAutoStartList = { %s %s }\n' % (space, primaryHost, StartList))
                    self.logger.debug('Addnig: AutoStartList = { %s, %s }' % (primaryHost, StartList))
                else:
                    lines.append('%sAutoStartList = { %s }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s }' % primaryHost)
                #lines.append('%s)\n' % space)
 
            elif re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = 1
                lines.append(line)

            # Searching: CVMCluster Agent 
            elif re.search('^[\s\t]*CVMNodeId[\t\s]+\=', line):
                self.logger.info('Starting editing the CVMNodeId.')
                space = re.search('^([\s\t]*)CVMNodeId[\t\s]+\=', line).group(1) 
                line = '%sCVMNodeId = {%s %s }' %(space, primaryHost , Str) 
                lines.append(line+'\n')

            # Searching: Oracle Agent 
            elif re.search('^[\s\t]*Sid[\t\s]+\@', line) and Sid == 0:
                i=1
                self.logger.info('Starting editing Oracle ora1.')
                space = re.search('^([\s\t]*)Sid[\t\s]+\@', line).group(1)
                line = '%sSid @%s = %s1' %(space, primaryHost, self.config['SchemaName'])
                lines.append(line+'\n')
                if self.config['ClusterMode'] == 'redundant':
                    for second in secondaryHost.split(','):
                        i = i + 1
                        line = '%sSid @%s = %s%s' %(space, second.split(':')[0].strip(), self.config['SchemaName'],i) 
                        lines.append(line+'\n')
                Sid = 1



            # Searching: PrivNIC Agent 
            elif re.search('^[\s\t]*Device[\t\s]+\@', line) and Device == 0:
                self.logger.info('Starting editing PrivNIC ora_priv.')
                i = 0
                Eth = ''
                for eth in self.config['HeartBit'].split(':')[0].split(','):
                    Eth = Eth + eth.strip() + ' = ' + str(i) + ', '
                    i=i+1
                Eth = Eth[:-2]
                space = re.search('^([\s\t]*)Device[\t\s]+\@', line).group(1)
                line = '%sDevice @%s = { %s }' %(space, primaryHost, Eth)
                lines.append(line+'\n')
                if self.config['ClusterMode'] == 'redundant':
                    for second in secondaryHost.split(','):
                        line = '%sDevice @%s = { %s }' %(space, second.split(':')[0].strip(), Eth)
                        lines.append(line+'\n')
                Device = 1
            

            # Searching: PrivNIC Agent
            elif re.search('^[\s\t]*Address[\t\s]+\@', line) and Address == 0:
                self.logger.info('Starting editing PrivNIC ora_priv.')
                try:
                    if self.config['Primary'].split(':')[1]:
                        if self.config['ClusterMode'] == 'redundant':
                            for seconf in self.config['OtherHostname'].split(','):
                                if seconf.split(':')[1]:
                                    pass
                                else:
                                    raise Exception, 'Missing InterConnect Addres'
                        line = '%sAddress @%s =  "%s" ' %(space, self.config['Primary'].split(':')[0].strip(), self.config['Primary'].split(':')[1].strip())
                        lines.append(line+'\n')
                        if self.config['ClusterMode'] == 'redundant':
                            for second in self.config['OtherHostname'].split(','):
                                line = '%sAddress @%s =  "%s" ' %(space, second.split(':')[0].strip(), second.split(':')[1].strip())    
                                lines.append(line+'\n')
                except:
                    i=2
                    line = '%sAddress @%s =  "1.1.1.%s" ' %(space, primaryHost, i ) 
                    lines.append(line+'\n')
                    if self.config['ClusterMode'] == 'redundant':
                        for second in secondaryHost.split(','):
                            i=i+1
                            line = '%sAddress @%s =  "1.1.1.%s" ' %(space, second.split(':')[0], i)
                            lines.append(line+'\n')
                Address = 1
                PrivMask = 1

            elif re.search('^[\s\t]*NetMask[\t\s]', line) and PrivMask == 1:
                if self.config.has_key('InterConnectNetMask') and self.config['InterConnectNetMask']: 
                    line = '%sNetMask = "%s" ' %(space, self.config['InterConnectNetMask'].strip())
                else:
                    line = '%sNetMask = "255.255.255.0"'  %(space)
                lines.append(line+'\n')
                PrivMask=0

            # Searching: SNMP block
            elif re.search('^[\s\t]*NotifierMngr Notifier[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'snmp\' block.')
                space = re.search('^([\s\t]*)NotifierMngr Notifier[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sCritical = 0\n' % space)
                self.logger.debug('Adding: Critical = 0')
                lines.append('%sSnmpConsoles = { %s }\n' % (space, self.listsnmp(self.SNMP)))
                self.logger.debug('Adding: SnmpConsoles = { %s }' % (self.listsnmp(self.SNMP)))
                lines.append('%s)\n' % space)
                self.logger.debug('Adding: )')
            # Searching: NIC EdnNIC block
            elif re.search('^[\s\t]*NIC EdnNIC[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'NIC EdnNIC\' block.')
                space = re.search('^([\s\t]*)NIC EdnNIC[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sMii = 0\n' % space)
                self.logger.debug('Adding: Mii = 0')
                lines.append('%sNetworkHosts = { %s }\n' %(space, self.listip(self.NETWORKHOSTS)))
                self.logger.debug('NetworkHosts = { %s }' % self.NETWORKHOSTS)
                lines.append('%s)\n' % space)
            # Searching: IP EdnVIP
            elif re.search('^[\s\t]*IP EdnVIP[\t\s]+\([\t\s]?$', line):
                self.logger.info('Starting editing the \'IP EdnVIP\' block.')
                space = re.search('^([\s\t]*)IP EdnVIP[\t\s]+\(', line).group(1) + '\t'
                lines.append(line)
                parenthesis = 'open'
                lines.append('%sDevice = bond0\n' % space)
                self.logger.debug('Adding: Device = bond0')
                lines.append('%sAddress = "%s"\n' % (space, self.CLUSTER_VIP))
                self.logger.debug('Adding: Address = "%s"' % self.CLUSTER_VIP)
                lines.append('%sNetMask = "%s"\n' % (space, self.CLUSTER_MASK))
                self.logger.debug('Adding: NetMask = "%s"' % self.CLUSTER_MASK)
                lines.append('%s)\n' % space)
                self.logger.debug('Addnig: )')

            else:
                if not re.search('^[\s\t]*Sid[\t\s]+\@', line):
                    if not re.search('^[\s\t]*Device[\t\s]+\@', line):
                        if not re.search('^[\s\t]*Address[\t\s]+\@', line):
                            if not re.search('^[\s\t]*system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\([\t\s]?$', line):
                                if not Group == 0:
                                    lines.append(line)

        cmd = '/opt/VRTSvcs/bin/hacf'
        cftocmd = '-cftocmd'
        verify = '-verify'
        generate = '-generate'
        path = os.path.dirname(self.fileToEdit)
        self.file.writelines(lines)
        self.file.close()
        self.logger.error('Finished editing main.cf file. Going to validate the changes:')
        self.logger.error('Running: \'hacf -verify <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, verify, path, self.log)):
            self.logger.error('%s was verified.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -verify <VRTS config path>\''
        self.logger.error('Running: \'hacf -generate <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, generate, path, self.log)):
            self.logger.error('%s was ganerated.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -generate <VRTS config path>\''
        self.logger.error('Running: \'hacf -cftocmd <VRTS config path>\'')
        if not os.system('%s %s %s %s' % (cmd, cftocmd, path, self.log)):
            self.logger.error('%s was modified acording to the new main.cf file.' % \
                            os.path.basename(self.fileToEdit))
        else:
            raise Exception, 'Failed to exec \'hacf -cftocmd <VRTS config path>\''
    def listip(self, l):
        tmp = l.split(', ')
        list = []
        for i in tmp:
            i = '"' + i + '"'
            list.append(i)
        return (', ').join(list)
    def listsnmp(self, l):
        tmp = l.split(', ')
        list = []
        for i in tmp:
            i = '"' + i + '"' + ' = Information'
            list.append(i)
        return (', ').join(list)
