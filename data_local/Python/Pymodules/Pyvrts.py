
##################################
#   ModuleNmae: Pyfiledit.py     #
##################################

import traceback
from Pyfiledit import builder

def OtherHost(hostname, OtherHostname=[]):
    if OtherHostname:
        return ','.join([ i[0] for i in OtherHostname ])
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

class dinamic_vrts(builder):
    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        from Pyfunc import GetHash, DigHostsIP 
        import os, re
        import glob
        super(dinamic_vrts, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
        self.config['Hostname'] = self.config.get('_',None) and self.config['_'](self.config['Section'],
                                                  'hostname', False) or os.environ['HOSTNAME']
        if self.config.has_key('CLUSTER_VIP') : self.CLUSTER_VIP = self.eval_func(value='CLUSTER_VIP')
        else: self.CLUSTER_VIP = None
        
        #self.SNMP = self.eval_func(value='SNMP')
        if self.config['ClusterMode'] == 'redundant' :
            if (self.config['Hostname'].endswith('a') or self.config['Hostname'].endswith('A')) and\
              (type(self.config['OtherHostname']) != list and len(self.config['OtherHostname'].strip()) == 0):
                self.config['OtherHostname'] = OtherHost(self.config['Hostname'])
                self.config['ServerInfo'] = 'primary'
            elif (self.config['Hostname'].endswith('b') or self.config['Hostname'].endswith('B')) and\
              (type(self.config['OtherHostname']) != list and len(self.config['OtherHostname'].strip()) == 0):
                self.config['OtherHostname'] = OtherHost(self.config['Hostname'])
                self.config['ServerInfo'] = 'secondary'
            else:
                self.config['ServerInfo'] = 'NplusOne'
                self.config['OtherHostname'] = OtherHost(self.config['Hostname'], self.config['OtherHostname'])
        else:
            self.config['ServerInfo'] = 'primary'
            self.config['OtherHostname'] = ''
          
        if not self.config['SetClusterID'] and self.CLUSTER_VIP:
            self.SetClusterID=self.CLUSTER_VIP.split('.')[3]
        elif self.config.has_key('SetClusterID') and self.config['SetClusterID']:
            self.SetClusterID=self.config['SetClusterID']
        else:
            raise Exception, "in NplusOne mode must select ClusterID"
            
        self.NplusOneList = []
        if self.config['ClusterMode'] == 'redundant' and  self.config.has_key('NplusOne') and self.config['NplusOne']:
            for server in self.config['NplusOne']:
                self.NplusOneList.append(server.split(':')[0].strip())
        if self.config.has_key('NplusOneDelimiter'): self.NplusOneDelimiter = self.config['NplusOneDelimiter'] 
        
        if self.config.has_key('Cluster_del') :self.delete_cluster = self.config['Cluster_del']
        else: self.delete_cluster = None
        if self.config.has_key('Cluster_add') :self.add_cluster = self.config['Cluster_add']
        else: self.add_cluster = None
        if self.config.has_key('Group_Server') :self.Group_Server = self.config['Group_Server']
        else: self.Group_Server = None
    


    def __call__(self, editFiles=[]):
        methodDict = { 'llthosts' : '_llthosts',
                        'llttab' : '_llttab',
                        'gabtab' : '_gabtab',
                        '/etc/VRTSvcs/conf/sysname' : '_sysname',
                        }
        methodDict['/etc/VRTSvcs/conf/config/main.cf'] = '_cf_rulles' 
        
        super(dinamic_vrts, self).__call__(editFiles=self.config.get('VCS_FILES', editFiles), methodDict=methodDict)

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
            #print self.config[value]
            self.logger.error(traceback.format_exc())
            raise Exception, 'Failed to execute %s' % self.config[value] 
        return eval_value

    def _llthosts(self):
        lines = []
        N=0
        if self.config['ClusterMode'] == 'single':
            lines.append('0 %s\n' % self.config['Hostname'])
        elif self.config['ClusterMode'] == 'redundant':
            if self.config['ServerInfo'] == 'primary':
                lines.append('0 %s\n' % self.config['Hostname'])
                lines.append('1 %s\n' % self.config['OtherHostname'])
            elif self.config['ServerInfo'] == 'secondary':
                lines.append('0 %s\n' % self.config['OtherHostname'])
                lines.append('1 %s\n' % self.config['Hostname'])
            else:
              for S in self.config['OtherHostname'].split(','):
                   lines.append('%s %s\n' %(N,S))  
                   N=N+1
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
        
        if self.config.has_key('Udp_llt_links') and self.config['Udp_llt_links']:
            for link in self.config['Udp_llt_links']:
                lines.append(link)
        if self.config.has_key('HeartBit') and self.config['HeartBit']:
                nicA, nicB = self.config['HeartBit'].split(', ')
                lines.append('link %s %s - ether - -\n' % (nicA, nicA))
                lines.append('link %s %s - ether - -\n' % (nicB, nicB))
        if self.config.has_key('HighPriBondLink') and self.config['HighPriBondLink']:
            lines.append('link %s %s - ether - -\n' % (self.config['HighPriBondLink'], self.config['HighPriBondLink']))
            lines.append('set-dbg-minlinks 2\n')
        elif self.config.has_key('LowPri') and self.config['LowPri'] :
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
        if self.config['ServerInfo'] == 'NplusOne' : num = len(self.config['OtherHostname'].split(','))
        if not self.linesRef or not re.search('^(/sbin/gabconfig\s.*-n)\d+', self.linesRef[0]):
            self.linesRef.append('/sbin/gabconfig -c -n1\n')
        line = re.sub('^(?P<gab>/sbin/gabconfig\s.*-n)\d+', r'\g<gab>%s' % num, self.linesRef[0])
        self.file.writelines(line)


    def _sysname(self):
        lines = []
        lines.append(self.config['Hostname'])
        self.file.writelines(lines)


    def _cf_rulles(self):
        self.linesRef = []
        Res_del = None
        Res_Dep_del = None
        Res_Dep_add = None
        Res_add = None
        Group_del = None
        Group_add = None
        Agent_Ip = None
        Agent_Nic = None
        delete_include = None
        add_include = None
        self.Res_del = {}
        self.Res_Dep_del = {}
        self.Res_Dep_add = {}
        self.Res_add = {}
        self.Group_to_Delete = {}
        self.Group_to_Add = {}
        self.Agent_Ip = {}
        self.Agent_Nic = {}
        self.delete_include = {}
        self.add_include = {}

        for k,v  in self.config.iteritems():        
            if k.startswith('Res_del_') and v :
                Res_del = 'O.K'
                self.Res_del[k] = v
            if k.startswith('Res_Dep_del_') and v:
                Res_Dep_del = 'O.K'
                self.Res_Dep_del[k] = v
            if k.startswith('Res_Dep_add_') and v :
                Res_Dep_add = 'O.K'
                self.Res_Dep_add[k] = v
            if k.startswith('Res_add_') and v :
                Res_add = 'O.K'
                self.Res_add[k] = v 
            if k.startswith('Group_to_Delete_') and v :
                Group_del = 'O.K'
                self.Group_to_Delete[k] = v
            if k.startswith('Group_to_Add_') and v :
                Group_add = 'O.K'
                self.Group_to_Add[k] = v
            if k.startswith('Agent_IP_') and v :
                Agent_Ip = 'O.K'
                self.Agent_Ip[k] = v
            if k.startswith('Agent_NIC_') and v :
                Agent_Nic = 'O.K'
                self.Agent_Nic[k] = v
            if k.startswith('Include_del_') and v:
                delete_include = 'O.K'
                self.delete_include[k] = v
            if k.startswith('Include_add_') and v:
                add_include = 'O.K'
                self.add_include[k] = v

        if self.delete_include : self.linesRef = self._cf_delete_include(self.linesRef, self.delete_include)
        if self.delete_cluster : self.linesRef = self._cf_delete_cluster(self.linesRef, self.delete_cluster)
        if Res_Dep_del : self.linesRef = self._cf_delete_req(self.linesRef)
        if Res_del : self.linesRef = self._cf_delete_res(self.linesRef)
        if Group_del : self.linesRef = self._cf_delete_group(self.linesRef)
        if self.add_cluster: self.linesRef = self._cf_add_cluster(self.linesRef)
        if self.add_include : self.linesRef = self._cf_add_include(self.linesRef)
        if Group_add : self.linesRef = self._cf_add_group(self.linesRef)
        if Res_Dep_add : self.linesRef = self._cf_add_req(self.linesRef)
        if Res_add : self.linesRef = self._cf_add_res(self.linesRef)
        if Agent_Ip :
            agent_ip = self._cf_agent_ip()
            self.Res_add = {'Res_add_NplusOne' : agent_ip}
            self.linesRef = self._cf_add_res(self.linesRef)
        if Agent_Nic :
            agent_nic = self._cf_agent_nic()
            self.Res_add = {'Res_add_NplusOne' : agent_nic}
            self.linesRef = self._cf_add_res(self.linesRef)
        self._cf()


    def _cf_delete_include(self, linesRef, delete_include):
        import re
        tmp_linesRef = []
        INC_L = []
        for INC in delete_include.values():
            INC_L += INC 
        for line in linesRef:
            for include in INC_L:
                Append = True
                if re.search('include[\s\t]+"%s"' %include.strip(), line.strip()):
                    Append = False
                    continue
            if Append: tmp_linesRef.append(line)
        return tmp_linesRef 
            
    def _cf_add_include(self, linesRef):
        linesRef = self._cf_delete_include(linesRef, self.add_include)
        for INC in self.add_include.values():
           for include in INC:
               linesRef.insert(0,'include "%s"\n' % include) 
        return linesRef 

    def _cf_delete_cluster(self, linesRef, delete_cluster):
        import re
        tmp_linesRef = []
        Append = True
        for line in linesRef:
            if re.search('^[\s\t]*cluster[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Cluster = re.search('(^[\s\t]*cluster[\s\t])(.*)([\s\t].*\($)', line).group(2)
                if Cluster in delete_cluster: Append = False 
            if Append : tmp_linesRef.append(line)
            if not Append and re.search('[\s\t]*\)[\s\t]?$',line) or re.search('.*\(.*\).*\)[\s\t]?$',line):
                Append = 'True'
        return tmp_linesRef

    def _cf_add_cluster(self, linesRef):
        import re
        linesRef = self._cf_delete_cluster(linesRef, self.add_cluster.keys())
        tmp_linesRef = [] 
        self.logger.info('[I] Append Cluster')
        for k,v in self.add_cluster.iteritems():
            tmp_linesRef.append('cluster %s (\n' % k.strip())
            self.logger.info('[I] Append %s Cluster' % k)
            for i in v:
                tmp_linesRef.append('%s\n'%i)
            tmp_linesRef.append(')\n')
        for line in linesRef:
            tmp_linesRef.append(line)
        return tmp_linesRef 
         

    def _cf_delete_group(self, linesRef, dg = None):
        import re
        tmp_linesRef = []
        Append = 'True'
        i=1
        tmp = []
        Group_List = []
        NplusOneList = self.NplusOneList
        Loop = 'Yes'
        self.logger.info('[I] Delete Group')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                if NplusOneList:
                   Group, Continue, i, tmp, Group_List = self.NplusOneGroups(line, NplusOneList, i, tmp, Group_List)
                   if Continue : continue
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
                        for k in self.Group_to_Delete.keys():
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
        i=1
        tmp = []
        Group_List = []
        Append = 'True'
        NplusOneList = self.NplusOneList
        self.logger.info('[I] Delete Resource ')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                if NplusOneList:
                   Group, Continue, i, tmp, Group_List = self.NplusOneGroups(line, NplusOneList, i, tmp, Group_List)
                   if Continue : continue
                Append = 'True'
            try:
                for k in self.Res_del.keys():
                    if self.config[k].has_key(Group):
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
        i=1
        tmp = []
        Group_List = []
        NplusOneList = self.NplusOneList
        self.logger.info('[I] Delete Dependency ')
        for line in linesRef:
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
               Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
               if NplusOneList: 
                   Group, Continue, i, tmp, Group_List = self.NplusOneGroups(line, NplusOneList, i, tmp, Group_List)
                   if Continue : continue
            try:
                for k in self.Res_Dep_del.keys():
                    if self.config[k].has_key(Group):
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

    def NplusOneGroups(self,line, NplusOneList, i, tmp, Group_List):
        import re
        Continue = None
        Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
        if re.search('(.*)(%s[0-9]+)($)'% self.NplusOneDelimiter, Group):
            Group_tmp = re.search('(.*)(%s[0-9]+)($)'% self.NplusOneDelimiter, Group).group(1)
            if Group_tmp in NplusOneList:
                if  self.config['ClusterMode'] != 'redundant': 
                    Continue = True
                    return Group, Continue,i, tmp, Group_List
                if Group_tmp not in Group_List:
                    i=0
                    Group_List.append(Group_tmp)
                if Group not in tmp:
                    tmp.append(Group)
                    i += 1
                Group = Group_tmp
        return Group, Continue,i, tmp, Group_List


    def _cf_add_req(self, linesRef):
        import re
        tmp_linesRef = []
        Append = 'False'
        tmp = []
        Group_List = []
        i = 1
        NplusOneList = self.NplusOneList
        self.logger.info('[I] Append Dependency')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                if NplusOneList:
                    Group, Continue, i, tmp, Group_List = self.NplusOneGroups(line, NplusOneList, i, tmp, Group_List)
                    if Continue : continue
                Append = 'True'
            if  re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('^[\s\t]*\)[\s\t]*', line)\
            and Append == 'True':
                 for k in self.Res_Dep_add.keys():
                    if self.config[k].has_key(Group):
                        for D in self.config[k][Group]:
                            if Group in NplusOneList:
                                if re.search('(^[\s\t])?(\w+)([\s\t]+)(requires[\s\t]+)(\w+)([\s\t]?)',D):
                                    D = re.sub(re.search('(^[\s\t])?(\w+)([\s\t]+)(requires[\s\t]+)(\w+)([\s\t]?)',D).group(2),
                                        re.search('(^[\s\t])?(\w+)([\s\t]+)(requires[\s\t]+)(\w+)([\s\t]?)',D).group(2)+'%s%s'% (self.NplusOneDelimiter,i),D)
                                    D = re.sub(re.search('(^[\s\t])?(\w+[\s\t]+)(requires[\s\t]+)(\w+)([\s\t]?)',D).group(4),
                                        re.search('(^[\s\t])?(\w+[\s\t]+)(requires[\s\t]+)(\w+)([\s\t]?)',D).group(4)+'%s%s'% (self.NplusOneDelimiter,i),D)
                            tmp_linesRef.append('\t' + D +'\n')
                            self.logger.info('[I] Append Dependency %s' % D)
                 Append = 'False'
        return tmp_linesRef
    

    def _cf_add_res(self, linesRef):
        import re
        tmp_linesRef = []
        i = 1
        tmp = []
        Append = 'False'
        Flag = None
        self.logger.info('[I] Append Resource')
        Group_List = []
        NpO_append = False
        NplusOneList = self.NplusOneList
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Group = re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2)
                NpO_Group = Group
                if self.Res_add.has_key('Res_add_NplusOne') and Group in self.Res_add['Res_add_NplusOne']:
                    pass
                elif NplusOneList:
                    Group, Continue, i, tmp, Group_List = self.NplusOneGroups(line, NplusOneList, i, tmp, Group_List)
                    if Continue : continue
                Append = 'True'
            if  re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('^[\s\t]*\)[\s\t]*', line)\
            and Append == 'True':
                 for k in self.Res_add.keys():
                    if self.Res_add[k].has_key(Group):
                        for D in self.Res_add[k][Group]:
                            if  re.search('.*\(.*\).*\([\s\t]?$',line) or re.search('[\s\t]*\([\s\t]?$',line)\
                                or re.search('.*\(.*\).*\)[\s\t]?$',line) or re.search('[\s\t]*\)[\s\t]?$',line) and not Flag:
                                Flag = True 
                                if re.search('(^[\s\t])?(\w[\s\t]+)(.*)([\s\t]+?)',D) and Group in NplusOneList:
                                    if self.config.has_key('NpO_Agent') and re.search('(^[\s\t])?(%s[\s\t]+)(.*)([\s\t]+?)' % self.config['NpO_Agent'] ,D):
                                        NpO_append = True
                                    D = re.sub(re.search('(^[\s\t])?(\w[\s\t]+)(.*)([\s\t]+?)',D).group(3),
                                        re.search('(^[\s\t])?(\w[\s\t]+)(.*)([\s\t]+?)',D).group(3)+'%s%s'% (self.NplusOneDelimiter,i),D)
                                      
                                tmp_linesRef.append('\t' + D +'\n')
                                if NpO_append:
                                    tmp_linesRef.append('\t' +'GroupName = %s' %NpO_Group  +'\n')  
                                    NpO_append = False
                                self.logger.info('[I] Append %s' %D)
                            elif Flag:
                                if re.search('.*\(.*\).*\)[\s\t]?$',D) or re.search('[\s\t]*\)[\s\t]?$',D):
                                    Flag = None 
                                tmp_linesRef.append('\t\t' + D +'\n')
                                self.logger.info('[I] Append %s' %D)
                 Append = 'False'
        return tmp_linesRef




    def _cf_agent_ip(self):
        Agent_Ip = {}
        for k1 in self.Agent_Ip.keys():
            for k,v in self.Agent_Ip[k1].iteritems():
                N = 1
                for Ip,Attr in v.iteritems():
                    Network = Ip 
                    Netmask = Attr['Netmask'] 
                    Bond = Attr['Bond'] 
                    if  self.config['ClusterMode'] != 'redundant': 
                        Agent_Ip['%s'%(k)] = ['IP EdnVip%s (' %(k),
                        'Device = %s' % Bond, 'Address = "%s"' % Network, 'NetMask = "%s"' %Netmask, ')']
                    else:
                        Agent_Ip['%s%s%s'%(k,self.NplusOneDelimiter,N)] = ['IP EdnVip%s%s%s (' %(k,self.NplusOneDelimiter,N),
                                 'Device = %s' % Bond, 'Address = "%s"' % Network, 'NetMask = "%s"' %Netmask,
                                 'OnlineRetryLimit = 5', ')'] 
                    
                    N+=1
        return Agent_Ip 


    def _cf_agent_nic(self):
        Agent_Nic = {}
        for k1 in self.Agent_Nic.keys():
            for k,v in self.Agent_Nic[k1].iteritems():
                N = 1
                for Ip,Attr in v.iteritems():
                    GW = Attr['GW'] 
                    Bond = Attr['Bond'] 
                    if  self.config['ClusterMode'] != 'redundant': 
                        Agent_Nic['%s'%(k)] = ['NIC EdnNic%s (' %(k),
                        'Device = %s' % Bond, 'Mii = 0', 'NetworkHosts = { "%s" }' %GW, ')']
                    else:
                         Agent_Nic['%s%s%s'%(k,self.NplusOneDelimiter,N)] = ['NIC EdnNic%s%s%s (' %(k,self.NplusOneDelimiter,N),
                         'Device = %s' % Bond, 'Mii = 0', 'NetworkHosts = { "%s" }' %GW, ')']                       
                    
                    N+=1
        return Agent_Nic 



    def _cf_add_group(self, linesRef):
        import re, os
        tmp_linesRef = []
        Groups = []
        OtherHostname = self.config['OtherHostname']
        self.logger.info('[I] Add Group')
        def add_group():
            tmp_linesRef.append('\tSystemList = { %s = 0 }\n'% os.environ['HOSTNAME'])
            tmp_linesRef.append('\tAutoStartList = { %s }\n'% os.environ['HOSTNAME'])
            tmp_linesRef.append('\t)\n')
        for line in linesRef:
            tmp_linesRef.append(line)
            if re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                Groups.append(re.search('(^[\s\t]*group[\s\t])(.*)([\s\t].*\($)', line).group(2))
        #for k in self.config.keys():
        for k in self.Group_to_Add.keys():
            for G in self.config[k].keys():
                if self.config[k][G].upper() == 'NPLUSONE' :
                    if self.Group_Server and  self.Group_Server.has_key(G):
                        self.config['OtherHostname'] =  ','.join(self.Group_Server[G.strip()])
                    else: self.config['OtherHostname'] = OtherHostname
                    if self.config['ClusterMode'] != 'redundant':
                        tmp_linesRef = self._cf_delete_group(tmp_linesRef, dg = {'Group_to_Delete_' : G })
                        tmp_linesRef.append('group %s (\n' % G )
                        add_group()
                        self.logger.info('[I] Add Group %s' %G)
                        continue
                    if len(self.config['OtherHostname'].split(',')) == 1:
                        LenOtherHostname= len(self.config['OtherHostname'].split(','))+1
                    else: LenOtherHostname= len(self.config['OtherHostname'].split(',')) 
                    StartPoint = 1
                    for i in range(StartPoint,LenOtherHostname):
                        if '%s%s%s' %(G,self.NplusOneDelimiter,i) in Groups:
                             tmp_linesRef = self._cf_delete_group(tmp_linesRef, dg = {'Group_to_Delete_' : '%s%s%s' %(G,self.NplusOneDelimiter,i) })    
                        tmp_linesRef.append('group %s%s%s (\n' % (G,self.NplusOneDelimiter,i) )
                        add_group()
                        self.logger.info('[I] Add Group %s%s%s' %(G,self.NplusOneDelimiter,i))
                elif G in Groups:
                    if self.config[k][G].upper() == 'EXIT':
                        raise Exception, 'The Group %s is existing' % G
                    elif self.config[k][G].upper() == 'NEW':
                        tmp_linesRef = self._cf_delete_group(tmp_linesRef, dg = {'Group_to_Delete_' : G }) 
                        tmp_linesRef.append('group %s (\n' % G )
                        add_group()
                        self.logger.info('[I] Add Group %s' %G)
                    elif self.config[k][G].upper() == 'IGNORE':
                        pass 
                else:
                    tmp_linesRef.append('group %s (\n' % G )
                    add_group()
                    self.logger.info('[I] Add Group %s' %G)
                   
        self.config['OtherHostname'] = OtherHostname
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


    def NplusOne(self):
        NplusOne = {}
        OtherHostname = self.config['OtherHostname']
        def _NplusOne(hostname, ServerList):
            AutoStartList = []
            N = 1
            g=1
            for i in hostname:
                if N >= n:
                    AutoStartList.append(i)
                    ServerList.append('%s = %s' %(i,g))
                    g+=1
                N += 1
            return AutoStartList,ServerList,g,n

        def _RemainServer(hostname,g):
            for i in hostname:
                ServerList.append('%s = %s' %(i,g))
                g+=1
            return ServerList

        def _AddNplusOneDict(NplusOne,n,ServerList,AutoStartList):
            NplusOne['%s%s%s' %(server.split(':')[0].strip(),self.NplusOneDelimiter,n)]={'ServerList' : ', '.join(ServerList)}
            NplusOne['%s%s%s' %(server.split(':')[0].strip(),self.NplusOneDelimiter,n)]['AutoStartList'] =', '.join(AutoStartList)
            return NplusOne

        if self.config['ClusterMode'] =='redundant' and self.config['ServerInfo'] == 'NplusOne' and self.config.has_key('NplusOne'):
            #for server in self.config['NplusOne'].split(','):
            for server in self.config['NplusOne']:
                if self.Group_Server and  self.Group_Server.has_key(server.split(':')[0].strip()):
                    self.config['OtherHostname'] =  ','.join(self.Group_Server[server.split(':')[0].strip()].values())
                else: self.config['OtherHostname'] = OtherHostname
                if len(self.config['OtherHostname'].split(',')) == 1 : 
                    LenOtherHostname = len(self.config['OtherHostname'].split(','))+1
                else: LenOtherHostname = len(self.config['OtherHostname'].split(',')) 
                StartPoint = 1
                if server.split(':')[1].upper().strip() == 'FIRST' :
                    for n in range(StartPoint,LenOtherHostname):
                        ServerList=['%s = 0' %(self.config['OtherHostname'].split(',')[0])]
                        AutoStartList,ServerList,g,n = _NplusOne(self.config['OtherHostname'].split(',')[1:], ServerList)
                        AutoStartList += self.config['OtherHostname'].split(',')[1:n]
                        AutoStartList += [self.config['OtherHostname'].split(',')[0]]
                        ServerList = _RemainServer(self.config['OtherHostname'].split(',')[1:n],g)
                        NplusOne = _AddNplusOneDict(NplusOne,n,ServerList,AutoStartList)
                elif server.split(':')[1].upper().strip() == 'LAST':
                    for n in range(StartPoint,LenOtherHostname):
                        ServerList = []
                        ServerList=['%s = 0' %(self.config['OtherHostname'].split(',')[-1])]
                        AutoStartList,ServerList,g,n = _NplusOne(self.config['OtherHostname'].split(',')[:-1],ServerList)
                        AutoStartList += self.config['OtherHostname'].split(',')[0:n]
                        AutoStartList = AutoStartList[1:]
                        AutoStartList += [self.config['OtherHostname'].split(',')[-1]]
                        AutoStartList.sort()
                        ServerList = _RemainServer(self.config['OtherHostname'].split(',')[0:n-1],g)
                        NplusOne = _AddNplusOneDict(NplusOne,n,ServerList,AutoStartList)
                else:
                    for n in range(StartPoint,LenOtherHostname):
                        AutoStartList = []
                        ServerList = []
                        N = 1
                        tmp = []
                        g=1
                        ServerList.append('%s = 0' % server.split(':')[1])
                        for i in self.config['OtherHostname'].split(','):
                           if i != server.split(':')[1].strip():
                               if N >= n:
                                   AutoStartList.append(i)
                                   ServerList.append('%s = %s' %(i,g))
                                   g+=1 
                               else:
                                   tmp.append(i)
                               N += 1
                        for i in self.config['OtherHostname'].split(','):
                             if i != server.split(':')[1].strip() and i not in AutoStartList: AutoStartList.append(i)
                        AutoStartList += [server.split(':')[1]]
                        ServerList = _RemainServer(tmp,g)
                        NplusOne = _AddNplusOneDict(NplusOne,n,ServerList,AutoStartList)
        self.config['OtherHostname'] = OtherHostname
        return NplusOne


    def _cf_server_by_group(self,Group):
        if self.Group_Server and self.Group_Server.has_key(Group):
            order_server = self.Group_Server[Group].values()
            order_server.sort()
            primaryHost = order_server[0]
            secondaryHost = ','.join(order_server[1:])
        else:
            primaryHost, secondaryHost = self._cf_server_by_default()
        return primaryHost, secondaryHost 
        
    def _cf_server_by_default(self):
        if self.config['ClusterMode'] == 'redundant':
            if self.config['ServerInfo'] == 'primary': 
                primaryHost = self.config['Hostname']
                secondaryHost = self.config['OtherHostname']
            elif self.config['ServerInfo'] == 'secondary':
                primaryHost = self.config['OtherHostname']
                secondaryHost = self.config['Hostname']
            else:   
                primaryHost = self.config['OtherHostname'].split(',')[0]
                secondaryHost = ','.join(self.config['OtherHostname'].split(',')[1:])
        else:           
            primaryHost = self.config['Hostname'] 
            secondaryHost = None
        return primaryHost, secondaryHost

    def _cf(self):
        import os, re
        # Setup VARs
        primaryHost, secondaryHost = self._cf_server_by_default()
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
        Append_Single = None
        SystemNameFlag = False
        NplusOne = self.NplusOne()
        for line in self.linesRef:
            # Searching: captured block 'end/close'
            if parenthesis == 'open':
                if re.search('^[\s\t]*\)[\s\t]*', line):
                    parenthesis = 'close'
                continue
            # Searching: system blocks, raise stsyemDone = 1 so it will enter only once.
            SystemName = re.search('^[\s\t]*system[\t\s]+(:?\w+[-_]?\w+){1,5}[\t\s]+\([\t\s]?$', line)
            if SystemName: SystemNameFlag = True
            if SystemName and self.config.has_key('NplusOne') and self.config['NplusOne'] and \
                       self.config['ClusterMode'] == 'redundant':
                parenthesis = 'open'
                if systemDone == 1:
                    continue
                systemDone = 1
                lines.append('system %s (\n' %primaryHost)
                lines.append(')\n') 
                for i in secondaryHost.split(','):
                    lines.append('system %s (\n' %i)
                    lines.append(')\n') 
                    systemDone = 1
            elif SystemName and self.config['ClusterMode'] == 'redundant':
                if Append_Single:
                    parenthesis = 'open'
                    continue
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
                if len(secondaryHost.split(',')) == 1:
                    lines.append('%ssystem %s (\n' % (space, secondaryHost))
                    self.logger.debug('Addnig: %ssystem %s (' % (space, secondaryHost))
                    lines.append('%s\t)\n' % space)
                    self.logger.debug('Addnig:%s\t)' % space)
                else:
                    for i in secondaryHost.split(','):
                        lines.append('%ssystem %s (\n' % (space, i))
                        self.logger.debug('Addnig: %ssystem %s (' % (space, i))
                        lines.append('%s\t)\n' % space)
                        self.logger.debug('Addnig:%s\t)' % space)
                  
                Append_Single = True
            elif SystemName and self.config['ClusterMode'] == 'single':
                if Append_Single: 
                    parenthesis = 'open'
                    continue
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
                Append_Single = True 
            # Searching: group blocks
            elif re.search('^[\s\t]*group[\t\s]+\w+[\t\s]+\([\t\s]?$', line):
                space = re.search('^([\s\t]*)group[\t\s]+\w+[\t\s]+\(', line).group(1) + '\t'
                self.logger.info('Starting editing the \'%s\' block.' % \
                                (re.search('^[\s\t]*group[\t\s]+(\w+)[\t\s]+\(', line).group(1)))
                lines.append(line)
                parenthesis = 'open'
                if self.config['ClusterMode'] == 'redundant':
                    Group = re.search('^[\s\t]*group[\t\s]+(\w+)[\t\s]+\(', line).group(1)
                    primaryHost, secondaryHost = self._cf_server_by_group(Group.strip())
                    if NplusOne and  Group in NplusOne.keys():
                        lines.append('%sSystemList = { %s }\n' % (space ,NplusOne[Group]['ServerList']))
                        self.logger.debug('Addnig: SystemList = { %s }' % NplusOne[Group]['ServerList'])
                        lines.append('%sAutoStartList = { %s }\n' % (space ,NplusOne[Group]['AutoStartList']))
                        self.logger.debug('Addnig: AutoStartList = { %s }' % NplusOne[Group]['AutoStartList'])
                        lines.append('%sFailOverPolicy = RoundRobin\n' % space)
                        self.logger.debug('Addnig: FailOverPolicy = RoundRobin')
                    else:             
                        Vrts_Group='Daemons'
                        if self.config.get('_',None) and self.config['_']('MWAS', 'identifier_ha', False)\
                        and (self.config['_']('MWAS', 'identifier_ha') == 'AA'):
                            Vrts_Group='ID'
                        Parallel = set(['Daemons',Vrts_Group])
                        if self.Group_Server and Group.strip() in self.Group_Server.keys():
                            SystemList = []
                            AutoStartList = []
                            n=0
                            order_server = self.Group_Server[Group.strip()].values()
                            order_server.sort()
                            for i in order_server: 
                                SystemList.append('%s = %s' %(i,n))
                                AutoStartList.append(i)
                                n+=1
                            lines.append('%sSystemList = { %s }' %(space, ', '.join(SystemList)))
                            self.logger.debug('Addnig: SystemList = { %s }' %', '.join(SystemList))
                            lines.append('%sAutoStartList = { %s }'  %(space, ', '.join(AutoStartList)))
                            self.logger.debug('Addnig: AutoStartList = { %s }' %', '.join(AutoStartList))
                        elif len(self.config['OtherHostname'].split(',')) > 2:
                            SystemList = ['%s = 0' % primaryHost]
                            AutoStartList = [primaryHost]
                            n=1
                            for i in secondaryHost.split(','):
                                SystemList.append('%s = %s' %(i,n))
                                AutoStartList.append(i)
                                n+=1
                            lines.append('%sSystemList = { %s }' %(space, ', '.join(SystemList)))
                            self.logger.debug('Addnig: SystemList = { %s }' %', '.join(SystemList))
                            lines.append('%sAutoStartList = { %s }'  %(space, ', '.join(AutoStartList)))
                            self.logger.debug('Addnig: AutoStartList = { %s }' %', '.join(AutoStartList))
                        else:
                            lines.append('%sSystemList = { %s = 0, %s = 1 }\n' % \
                                (space, primaryHost, secondaryHost))
                            self.logger.debug('Addnig: SystemList = { %s = 0, %s = 1 }' % \
                                      (primaryHost, secondaryHost))
                            lines.append('%sAutoStartList = { %s, %s }\n' % (space, primaryHost, secondaryHost))
                            self.logger.debug('Addnig: AutoStartList = { %s, %s }' % (primaryHost, secondaryHost))
                        for P in self.config['Parallel_Group']:
                            Parallel.add(P.strip()) 
                        if Parallel.intersection([re.search('(^[\s\t]*group[\t\s])(.*)([\t\s]+\()', line).group(2)]):
                            lines.append('%sParallel = 1\n' % space) 
                            self.logger.debug('Addnig: Parallel = 1')
                else:
                    lines.append('%sSystemList = { %s = 0 }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: SystemList = { %s = 0 }' % primaryHost)
                    lines.append('%sAutoStartList = { %s }\n' % (space, primaryHost))
                    self.logger.debug('Addnig: AutoStartList = { %s }' % primaryHost)

                lines.append('%s)\n' % space)
            else:
                if Append == 'True': lines.append(line)

        if not SystemNameFlag:
            primaryHost, secondaryHost = self._cf_server_by_group(None)
            lines.append('system %s (\n' % (primaryHost))
            lines.append('\t)\n')
            if secondaryHost:
                if len(secondaryHost.split(',')) == 1:
                    lines.append('system %s (\n' % (secondaryHost))
                    lines.append('\t)\n')
                else:
                    for i in secondaryHost.split(','):
                        lines.append('system %s (\n' % (i))
                        lines.append('\t)\n')

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
            elif re.search('^[\s\t]*IP EdnVIP[\t\s]+\([\t\s]?$', line) and self.CLUSTER_VIP:
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
            #print self.config[value]
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
            elif re.search('^[\s\t]*IP EdnVIP[\t\s]+\([\t\s]?$', line) and self.CLUSTER_VIP:
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
