
###############################
#   By: Itzik Ben Itzhak      #
#   Mail: itzik.b.i@gmail.com #
#   Date: 30/08/2010          #
#   Module: Pymatrix          #
###############################

import os, glob, sys, re, copy
from ConfigParser import *
from operator import attrgetter, itemgetter
import Pyconstruct.ipcalc as ipcalc

def getID(self,server_key):
    if server_key[-1].isdigit():
        return re.search('(\d+)', server_key).group(1)
    return re.search('(\d+[a-z])', server_key).group(1)
        
        
def getInterfaceByIP(self,ip,section,server_key=False,cluster_id=False):
    if cluster_id : network = self.getNetworkByIP(ip,section,cluster_id=cluster_id)
    elif server_key : network = self.getNetworkByIP(ip,section,server_key=server_key)
    if not network:return False
    interface = self.getKey(section, '%s_interface' %network.lower(),False) or self.getKey(network,'interface',False)
    if interface:return interface
    return False
    
def getNetworkByIP(self,ip,section,server_key=False,cluster_id=False):
    networks = []
    version = ipcalc.IP(ip).version()
    if server_key:
        networks = [ key for key in self.getKey(section,server_key,False).keys() if not key=='hostname']
    elif cluster_id:
        for server in self.getListOfKeys(section,self.getKey(section,self.host_key_detect)+cluster_id,False):
            for key in server[0].keys():
                if not key=='hostname' and key not in networks:
                    networks.append(key)
    for network_id in networks:
        if version == 4 and self.has_option(network_id, 'netmask'):
            if ip in ipcalc.Network('%s/%s' % (self.get(network_id, 'network') ,ipcalc.netmask2int(self.get(network_id, 'netmask')))):
                return network_id
        elif version == 6 and self.has_option(network_id, 'prefix'):
            if ip in ipcalc.Network('%s/%s' % (self.get(network_id, 'network') ,self.get(network_id, 'prefix'))):
                return network_id
    return False

def DynamicOption(self,section,server_key,option,default=''):
    if self.getID(server_key)[-1].isdigit():
        cluster_key_detect = self.get(section,self.host_key_detect)
    else:
        id = re.search('(\d+)', server_key).group(1)
        cluster_key_detect = self.get(section,self.host_key_detect) + id
    if self.has_option(section,'%s_%s' % (option,server_key)):
        return self.get(section,'%s_%s' % (option,server_key))
    elif self.has_option(section,'%s_%s' % (option ,cluster_key_detect)):
        return self.get(section,'%s_%s' % (option,cluster_key_detect))
    elif self.has_option(section,'%s' % option):
        return self.get(section,'%s' % option)
    else:
        return default

    
def getUniqeApps(self,applist):
    serverlist = []
    for value in getAppsServers(self,applist[0]).values():
        serverlist.extend(value) 
    for app in applist:
        checklist = []
        for value in getAppsServers(self,app).values():
            checklist.extend(value)
        serverlist = list(set(serverlist) & set(checklist))
    return serverlist

def appNotInServers(self,app):
    server_keys = []
    application_servers = []
    for value in getAppsServers(self,app).values():
        application_servers.extend(value)
    servers = getSectionApps(self).values()
    for server in servers:
        server_keys.extend(server.keys())
    for app_server in application_servers:
        server_keys.remove(app_server)
    return server_keys
            
def getUnionApps(self,applist):
    serverlist = []
    for app in applist:
        for value in getAppsServers(self,app).values():
            if value[0] not in serverlist:
                serverlist.extend(value)
    return serverlist

def Dict2Sort(dict):
    sorted_dict = {}  
    for section,servers_list in dict.iteritems():
        sorted_dict[section] = sorted(servers_list , optionSorting)
    return sorted_dict

def AppVip(self,app):
    appdict = self.getAppsServers(app,check_by='full',group_by_cluster=True,filter=True)
    if not appdict: return ''
    if self.getKey(appdict.keys()[0] ,'cluster_vip%s' % appdict.values()[0].keys()[0],False):
        return self.getKey(appdict.keys()[0] ,'cluster_vip%s' % appdict.values()[0].keys()[0],False)
    else:
        return ''

def AppVips(self,app,newKey='cluster_vip{{ ID }}',section=False):
    tup = []
    newKey = re.sub('{{[\t\s]*ID[\t\s]*}}', '{{ID}}', newKey)
    apps = self.getAppsServers(app,check_by='full',group_by_cluster=True,section=section)
    if apps.keys().__len__() == 0:return []
    elif not section and apps.keys().__len__() > 1:
        add_section = True
    else:
        add_section = False
    for _section,index_servers in apps.iteritems():
        
        for index in index_servers.keys():
            tup += [('%s%s' % (add_section and '%s_' % _section.lower() or '',self.getKey(_section, 'cluster_vip%s' % index)), '%s' % newKey.replace('{{ID}}',index))]
    return tup 

    
def getAppsServers(self,app,section=False,server_key=False,check_by=False,group_by_cluster=False,filter=False):
    new_appsdict = {}
    if not server_key and not section:
        appsdict = getSectionApps(self,check_by=check_by)
        if not appsdict:
            return appsdict
        for item in appsdict:
            for value in appsdict[item]:
                if app in appsdict[item][value]:
                    if new_appsdict.has_key(item):
                        new_appsdict[item] = new_appsdict[item] + [value]
                    else:
                        new_appsdict[item] = [value]
        if group_by_cluster:
            Group_By_Index(self,Dict2Sort(new_appsdict))
            if not filter:
                return Group_By_Index(self,Dict2Sort(new_appsdict))
            else :
                return filter_by_index(self,Group_By_Index(self,Dict2Sort(new_appsdict)))
        else:
            return Dict2Sort(new_appsdict)
    elif section and not server_key:
        appsdict = getSectionApps(self,section=section,check_by=check_by)
        if not appsdict:
            return appsdict
        for value in appsdict[section]:
            if app in appsdict[section][value]:
                if new_appsdict.has_key(section):
                    new_appsdict[section] = new_appsdict[section] + [value] 
                else:
                    new_appsdict[section] = [value]                 
        if group_by_cluster:
            if not filter:
                return  Group_By_Index(self,Dict2Sort(new_appsdict))
            else:
                return filter_by_index(self,Group_By_Index(self,Dict2Sort(new_appsdict)))
        else:
            return Dict2Sort(new_appsdict)
    elif server_key and not section:
        appsdict = getSectionApps(self,server_key=server_key,check_by=check_by)
        if not appsdict:
            return appsdict
        if app in appsdict.values()[0][server_key]:
            new_appsdict[appsdict.keys()[0]] = [server_key]
        if group_by_cluster:
            if not filter:
                return  Group_By_Index(self,new_appsdict)
            else:
                return filter_by_index(self,Group_By_Index(self,new_appsdict))
        else:
            return new_appsdict     
    elif server_key and section:
        appsdict = getSectionApps(self,section=section,server_key=server_key,check_by=check_by)
        if not appsdict:
            return appsdict
        if app in appsdict[section][server_key]:
            new_appsdict[appsdict.keys()[0]] = [server_key]
        if group_by_cluster:
            if not filter:
                return  Group_By_Index(self,new_appsdict)
            else:
                return filter_by_index(self,Group_By_Index(self,new_appsdict))
        else:
            return new_appsdict

def filter_by_index(self,appsdict):
    if not appsdict :return {}
    filterdict = {}
    if self.getKey(self.Section,'cluster_id') in appsdict[appsdict.keys()[0]].keys():
        filterdict = {appsdict.keys()[0] : {self.getKey(self.Section,'cluster_id') : appsdict[appsdict.keys()[0]][self.getKey(self.Section,'cluster_id')]}}
    else:
        filterdict = { appsdict.keys()[0]: appsdict[appsdict.keys()[0]]}
    return filterdict

def checkByList(self,section,server_key=False,check_by=False):     
    applist = []
    host_key_detect = self.getKey(section, self.host_key_detect)
    if check_by == 'apps':
        applist = self.getListOfKeys(section,'applist_%s' % host_key_detect, required=False)
    elif check_by == 'required':
        applist = self.getListOfKeys(section,'reqlist_%s' % host_key_detect, required=False)
    elif check_by == 'runner':
        applist = self.getListOfKeys(section,'runnerapps_%s' % host_key_detect, required=False)
    else:
        for apps,host in self.getListOfKeys(section,'applist_%s' % host_key_detect, required=False):
            for reqs,server in self.getListOfKeys(section,'reqlist_%s' % host_key_detect, required=False):
                if host.split('_')[1] == server.split('_')[1]:
                    if apps and reqs:
                        applist += ([(apps+reqs,host)])  
                    elif apps and not reqs:
                        applist += ([(apps,host)])
                    elif reqs and not apps:
                        applist += ([(reqs,host)])
        if applist:
            runnerlist = self.getListOfKeys(section,'runnerapps_%s' % host_key_detect, required=False)
            applist = insertRunnerApps(self,applist,runnerlist)
        else:
            applist = self.getListOfKeys(section,'runnerapps_%s' % host_key_detect, required=False)         
    return applist

def insertRunnerApps(self,applist,runnerlist):
    newlist = []
    if not applist and not runnerlist:return {}
    for apps,host in applist:
        for runners,server in runnerlist:
            if not host.split('_')[1] == server.split('_')[1]:continue
            else:
                if apps and runners:
                    newlist += ([(apps+runners,host)])  
                elif apps and not runners:
                    newlist += ([(apps,host)])
                elif runners and not apps:
                    newlist += ([(runners,host)])
    return newlist   
        
def getAppsByClusterUpper(self,section,cluster_key_detect,app=False,check_by=False):
    upperdict = {}
    appsdict = self.getAppsBy(section,cluster_key_detect,app=app,check_by=check_by) 
    for k,v in appsdict.items():
        upperdict[k.upper()] = v
    return upperdict

def getAppsByCluster(self,section,cluster_key_detect,app=False,check_by=False):
    appsdict = self.getAppsBy(section,cluster_key_detect,app=app,check_by=check_by)     
    return appsdict
    
def getAppsBy(self,section,cluster_key_detect=False,app=False,check_by=False):
    appsdict = {}
    if section and app and not cluster_key_detect:
        appsdict[app] = []
        for apps,host in checkByList(self,section=section,check_by=check_by):
            if app in apps:
                appsdict[app] += [host.split('_')[1]]
        return appsdict
    elif section and app and cluster_key_detect:
        appsdict[app] = []
        for apps,host in checkByList(self,section=section,check_by=check_by):
            if app in apps:
                if cluster_key_detect[-1].isdigit():
                    id_key = re.search('^%s(\d+)' % self.get(section,self.host_key_detect), cluster_key_detect).group(1)
                    if host[:-id_key.__len__()].endswith(cluster_key_detect):
                        appsdict[app] += [host.split('_')[1]]
                else:
                    appsdict = getAppsByCluster(section,app=app,check_by=check_by)
        return appsdict
    elif section and cluster_key_detect and not app:
        for apps,host in checkByList(self,section=section,check_by=check_by):
            if cluster_key_detect[-1].isdigit():
                id_key = re.search('^%s(\d+)' % self.get(section,self.host_key_detect), cluster_key_detect).group(1)
                if host[:-id_key.__len__()].endswith(cluster_key_detect):
                    for app in apps :
                        if not appsdict.keys():
                            appsdict = {app : [host.split('_')[1]]}
                        elif not appsdict.has_key(app):
                            appsdict[app] = [host.split('_')[1]]
                        elif appsdict.has_key(app):
                            appsdict[app] += [host.split('_')[1]]
            else:
                for app in apps:
                    if not appsdict.keys():
                        appsdict = {app : [host.split('_')[1]]}
                    elif not appsdict.has_key(app):
                        appsdict[app] = [host.split('_')[1]]
                    elif appsdict.has_key(app):
                        appsdict[app] += [host.split('_')[1]]
        return appsdict
    else:
        for apps,host in checkByList(self,section=section,check_by=check_by):
            for app in apps:
                if not appsdict.keys():
                    appsdict = {app : [host.split('_')[1]]}
                elif not appsdict.has_key(app):
                    appsdict[app] = [host.split('_')[1]]
                elif appsdict.has_key(app):
                    appsdict[app] += [host.split('_')[1]]
        return appsdict

def Group_By_Index(self,appsdict):
    index_dict = {}
    sectionflag = False
    for key in appsdict.keys():
        flag = False
        if not sectionflag:
            index_dict = {key : {'' : ['']}}
            sectionflag = True
        else:
            index_dict[key] = {'' : [''] }
        for server in appsdict[key]:
            id_key = re.search('^%s(\d+)' % self.get(key,self.host_key_detect), server).group(1)
            if index_dict[key].has_key(id_key):
                if not server in index_dict[key][id_key]:
                    index_dict[key][id_key].append(server)
                else:
                    index_dict[key][id_key].append(server)
            else:
                if not flag:
                    index_dict[key] = {id_key : ['']}
                    flag = True
                    if not server in index_dict[key][id_key]:
                        index_dict[key][id_key] = [server]
                    else:
                        index_dict[key][id_key].append(server)
                else:
                    index_dict[key][id_key] = ['']
                    if not server in index_dict[key][id_key]:
                        index_dict[key][id_key] = [server]
                    else:
                        index_dict[key][id_key].append(server)
    return index_dict 

def getGroupByCluster(self,appsdict):
    index_dict = {}
    sectionflag = False
    for key in appsdict.keys():
        flag = False
        if not sectionflag:
            index_dict = {key : {'' : ['']}}
            sectionflag = True
        else:
            index_dict[key] = {'' : [''] }
        for server in appsdict[key].keys():
            id_key = re.search('^%s(\d+)' % self.get(key,self.host_key_detect), server).group(1)
            if index_dict[key].has_key(id_key):
                if not server in index_dict[key][id_key]:
                    index_dict[key][id_key].append(server)
                else:
                    index_dict[key][id_key].append(server)
            else:
                if not flag:
                    index_dict[key] = {id_key : ['']}
                    flag = True
                    if not server in index_dict[key][id_key]:
                        index_dict[key][id_key] = [server]
                    else:
                        index_dict[key][id_key].append(server)
                else:
                    index_dict[key][id_key] = ['']
                    if not server in index_dict[key][id_key]:
                        index_dict[key][id_key] = [server]
                    else:
                        index_dict[key][id_key].append(server)
    return index_dict              

def getSectionApps(self,section=False,server_key=False,cluster_key_detect=False,check_by=False,group_by_cluster=False):
    appsdict = {}
    if section and cluster_key_detect and not server_key:
        appsdict[section] = ''
        flag = False
        for apps,host in checkByList(self,section=section,check_by=check_by) :
            if not cluster_key_detect[-1].isdigit():
                IDlength = re.search('%s(\d+)' % cluster_key_detect, host).group(1).__len__()
                if host[:-IDlength].endswith(cluster_key_detect):
                    if not flag:
                        appsdict[section] = {host.split('_')[1] : apps}
                        flag = True    
                    else:
                        appsdict[section][host.split('_')[1]] = apps
            else:
                id_key = re.search('^%s(\d+)' % self.get(section,self.host_key_detect), cluster_key_detect).group(1)   
                if host[:-id_key.__len__()].endswith(cluster_key_detect):
                    if not flag:
                        appsdict[section] = {host.split('_')[1] : apps}
                        flag = True    
                    else:
                        appsdict[section][host.split('_')[1]] = apps
        if group_by_cluster:
            return getGroupByCluster(self,appsdict)
        else:
            return appsdict
    elif section and server_key and not cluster_key_detect:
        for apps,host in checkByList(self,section=section,check_by=check_by):
            if host.split('_')[1] == server_key:
                appsdict = {section : {server_key : apps}}
        if group_by_cluster:
            return getGroupByCluster(self,appsdict)
        else:
            return appsdict
    elif section and not server_key and not cluster_key_detect:
        appsdict = {section : '' }
        flag = False
        for apps,host in checkByList(self,section=section,check_by=check_by):
            if not flag:
                appsdict = {section : {host.split('_')[1] : apps}}
                flag = True
            else:
                appsdict[section][host.split('_')[1]] = apps
        if group_by_cluster:
            return getGroupByCluster(self,appsdict)
        else:
            return appsdict
    else:
        for section in self.server_sections:
            flag = False
            appsdict[section] = ''
            for apps,host in checkByList(self,section=section,check_by=check_by):
                if not flag:
                    appsdict[section] = {host.split('_')[1] : apps}
                    flag = True
                else:
                    appsdict[section][host.split('_')[1]] = apps
        if group_by_cluster:
            return getGroupByCluster(self,appsdict)
        else:
            return appsdict



def buildSysConfig(serverSection=False, 
                   host_key_detect='host_key_detect', 
                   file='/data_local/Python/system.ini', 
                   identifierPath='/data_local/Python/', 
                   wildcard='server__*__*.info',
                   DEFAULT_APPS = {},
                   CORE_APPS = {},
                   UI_APPS = {},
                   INCLUDED_APPS = {},
                   GLOBAL_CORE_APPS = {},
                   host_delimiter = ':',
                   net_support_sections = ''
                   ):
    # Initial Vars/Methods All set attribute
    # FIXME - Ugly but works... 
    foundsection = False
    popup = False
    ConfigParser.getKey = getKey
    ConfigParser.getListOfKeys = getListOfKeys
    ConfigParser.host_key_detect = host_key_detect
    ConfigParser.getSectionApps = getSectionApps
    ConfigParser.getAppsServers = getAppsServers
    ConfigParser.getUniqeApps = getUniqeApps
    ConfigParser.appNotInServers = appNotInServers
    ConfigParser.DynamicOption = DynamicOption
    ConfigParser.getAppsByClusterUpper = getAppsByClusterUpper
    ConfigParser.getAppsByCluster = getAppsByCluster
    ConfigParser.getAppsBy = getAppsBy
    ConfigParser.getUnionApps = getUnionApps
    ConfigParser.filter_by_index = filter_by_index
    ConfigParser.CORE_APPS = copy.deepcopy(CORE_APPS)
    ConfigParser.INCLUDED_APPS = INCLUDED_APPS
    ConfigParser.DEFAULT_APPS = DEFAULT_APPS
    ConfigParser.UI_APPS = UI_APPS
    ConfigParser.GLOBAL_CORE_APPS = GLOBAL_CORE_APPS
    ConfigParser.getInterfaceByIP = getInterfaceByIP
    ConfigParser.getNetworkByIP = getNetworkByIP
    ConfigParser.AppVip = AppVip
    ConfigParser.AppVips = AppVips
    ConfigParser.getID = getID
    ConfigParser.host_delimiter = host_delimiter
    sysConfig = ConfigParser()
    # Get ini parser objext
    returnFiles = sysConfig.read(file)
    if returnFiles.__len__() == 0:
        raise Exception, 'ConfigParser could not open: \"%s\"' % file
    # Select server from section by file or force_server_id option under RUNNER section else popup to the user
    elif not os.path.isfile(file):
        raise Exception, 'No ini file where found: \"%s\"' % file
    serverID = glob.glob(os.path.join(identifierPath,wildcard))
    old_serverID = serverID
    sysConfig.server_sections = [s for s in sysConfig.sections() if sysConfig.has_option(s, 'type') and \
                                 sysConfig.get(s, 'type') == 'server' and sysConfig.has_option(s, host_key_detect) ]
    # 1st condition check if force_server_id is enabled
    if sysConfig.has_option('RUNNER', 'force_server_id') and sysConfig.get('RUNNER', 'force_server_id'):
        serverID = sysConfig.get('RUNNER', 'force_server_id')
        #FIXME - Amir,set the checking if file exist to function
        if serverID.find(sysConfig.host_delimiter) > -1:
            #serverID = [x.strip(' ') for x in serverID.split(host_delimiter)]
            serverSection,serverID = serverID.split(sysConfig.host_delimiter)
            if not serverID.startswith( sysConfig.get(serverSection, host_key_detect)):
                serverID = sysConfig.get(serverSection, host_key_detect) +  serverID
        elif serverID.find(sysConfig.host_delimiter) == -1:
            for section in sysConfig.sections():
                if serverID == section:
                    serverSection = serverID
                    foundsection = True
            if not serverID.startswith( sysConfig.get(serverSection, host_key_detect)) and not foundsection:
                serverID = sysConfig.get(serverSection, host_key_detect) +  serverID  
    # 2nd condition check if file server__*__.info exsit
    elif serverID.__len__() > 1:
       raise Exception, 'Found more then one serverID file: %s' % ', '.join(serverID) 
    elif serverID.__len__() == 0: 
        if not serverSection:
            sys.stdout.write("\n\n[Runner] What is the section name from system.ini file?: ")
            sys.stdout.flush()
            serverSection = raw_input()
        sys.stdout.write("\n\n[Runner] What is \"%s\" server index from system.ini file?: %s" % (serverSection, sysConfig.get(serverSection, host_key_detect)))
        sys.stdout.flush()
        serverID = raw_input()
        if not serverID.startswith( sysConfig.get(serverSection, host_key_detect)):
            serverID = sysConfig.get(serverSection, host_key_detect) +  serverID
        popup = True
    elif serverID.__len__() == 1:
        serverID = os.path.basename(serverID[0])
        if serverID[6:].startswith('__'):
            serverSection = serverID.split('__')[1]
            serverID = serverID.split('__')[2].split('.')[0]
        elif serverID[6:].startswith('_'):
            serverID = serverID.split('_')[1].split('.')[0]
        else:
            e = '%s: %s\n'  % (sys.exc_info()[0], sys.exc_info()[1])
            raise Exception, '%s BadFileName Failed to get server Type or serverID file' % e
    # 3rd condition check what is the section if didn't get one yet
    if not serverSection: 
        sys.stdout.write("\n\nWhat is the section name from system.ini file? ")
        sys.stdout.flush()
        serverSection = raw_input()
        if sysConfig.has_option(serverSection, 'type') and sysConfig.get(serverSection, 'type') == 'server':
            popup = True
        else:
            raise Exception, 'Section name must be one of the following\n%s' % sysConfig.server_sections
    # If popup exist, save the file to HD under /data_local/Python
    if popup:
        if old_serverID:
            os.remove(old_serverID[0])
        f = open(os.path.join(identifierPath, 'server__'+ serverSection + '__'+ serverID + '.info'), 'w')
        f.close()
    sysConfig.set('RUNNER','Section',serverSection)
    sysConfig.Section = serverSection
    # Setting network dict to all network sections: key=net section name, value=ipcalc obj of the nework
    sysConfig.network_sections = networkSectionList(sysConfig)
    sysConfig.set('RUNNER', 'network_sections', sysConfig.network_sections)
    # Build servers Dictionary including replacing ips to full name and implement range options.
    for section in sysConfig.server_sections:
        host_key = sysConfig.get(section, host_key_detect)
        id_list = []
        host_id = ''
        counter = True
        if sysConfig.has_option(section, 'range') and sysConfig.getint(section, 'range') > 1:
            for item in sysConfig.items(section):
                if item[0].startswith(host_key) and item[0][-1].isdigit():
                    host_id = re.findall('\d+',item[0])
                    if host_key in id_list:
                        counter = False 
                    else:
                        id_list.append(host_key)
                elif item[0].startswith(host_key) and item[0].endswith('a')and item[0][-2].isdigit():
                    host_id = re.findall('\d+a',item[0])
                    id_key = re.search('(\d+)',host_id[0]).group(0)
                    if id_key in id_list:
                        counter = False
                    else:
                        id_list.append(id_key)
                # Building range server list for this section
                if host_id:
                    if not counter:
                       raise Exception, 'Range is already builded for server(%s) from Section %s cant build again for %s' % (servername,section,host_key+host_id[0]) 
                    else:
                        rebuildRange(sysConfig, section, host_key,host_id)
                        servername = host_key+host_id[0]
        # update servers ips tp full name and converst servers option to dict
        serversDictBuild(sysConfig, section, host_key)
        for section in net_support_sections:
            if section in sysConfig.sections():
               setSectionSupportNetwork(sysConfig,section)
    # build auto requirement for applications according to GLOBAL_CORE_APPS 
    global_required_apps_builder(sysConfig)
    # build new options for serverID IPs/hostname/otherhostname/vips/{{ID}}
    buildSectionInfo(sysConfig, serverSection, serverID)
    include_apps_builder(sysConfig)
    # Debug print:
    if sysConfig.has_option('RUNNER', 'debug'):
        sections = sysConfig.get('RUNNER', 'debug')
        if not sections:
            sections = (serverSection,)
        else:
            sections = [s.strip().upper() for s in sections.split(',')]
        print 'buildSectionInfo DEBUG:'
        
        for section in sections:
            debug = 'DEBUG: Section - \"%s\"' % section
            print debug
            print '-' * len(debug)
            try:
                for item in sysConfig.items(section):
                   print '%s = %s' % (item[0], item[1])
            except:
                print 'DEBUG Error: Cant find \"%s\" section in ini file.' % section
                continue
            print '#' * 10 + ' END Section - %s ' %section + '#' * 10 + '\n'
        
    return sysConfig, sysConfig.getKey, sysConfig.getListOfKeys

def rebuildRange(sysConfig, section, host_key,host_id):
    """
    Building server list acording to range parameter in sysConfig.
    rebuildRange update sysConfig section it self, so no return value is needed.
    rebuildRange dose not parse the IPs of each server it only increment the index of each server elements 
    """
    # Getting network dict including ipcalc obkject
    network_sections = sysConfig.get('RUNNER', 'network_sections')
    # Fetch first server, range and parse server elements for ranging.
    serverInfo = sysConfig.get(section, host_key + host_id[0]).split(sysConfig.host_delimiter)
    _range = sysConfig.getint(section, 'range')
    hostname, ips = getNetworksDict(serverInfo, network_sections,sysConfig)
    if not host_id[0].endswith('a'):
        host_key_index = int(host_id[0])
        hostIndex = int(re.search('(\d+)$', hostname).group(1))
        hostBase = re.search('(.*)\d+$', hostname).group(1)
    else:
        host_key_index = ord(host_id[0][-1])
        hostBase = hostname[:-1] 
    try:
        for i in range(1, _range, 1):
            iplist = []
            #hostIndex += 1
            host_key_index += 1
            for net, ip in ips.iteritems():
                if sysConfig.get(net,'version')['version'] == '4':
                    ip[-1] = str(int(ip[-1]) + 1)
                    iplist.append('%s-%s' % (net, '.'.join(ip)))
                elif sysConfig.get(net,'version')['version'] == '6':
                    ipint = int(ip[-1],16) + i
                    iplist.append('%s-%s' % (net, hex(ipint)[2:]))
                else:
                    raise Exception, 'rebuildRange : ini Error , %s is ilegal host IP' % ip
                if hostname.endswith('a'):
                    sysConfig.set(section, '%s%s' % (hostBase, chr(host_key_index)), '%s %s %s' % \
                              ('%s%s' % (hostBase, chr(host_key_index)),sysConfig.host_delimiter, sysConfig.host_delimiter.join(iplist)))
                else:
                    sysConfig.set(section, '%s%s' % (host_key, host_key_index), '%s %s %s' % \
                              ('%s%s' % (hostBase, host_key_index),sysConfig.host_delimiter, sysConfig.host_delimiter.join(iplist))) 
        return
    except:
        e = '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
        raise Exception, '%s rebuildRange: ini Error, Failed to build server range for \"%s\" section' % \
                (e, section)

def serversDictBuild(sysConfig, section, host_key):
    """
    Convert each server value from string to dict as folow:
    'hostname' : <server hostname>
    'NETWORK SECTION NAME' : <network name> --> key for each netwok
    serversDictBuild convert all IP from <NETNAME>-IP/ID to <x>.<x>.<x>.<x> format
    serversDictBuild validate that each ip belong to a spciphic network else, raise exception.
    Supporting formats:
    server_key<index> = <hostbane> : <networkname>-1.2.3.4 : ...
    server_key<index> = <hostbane> : 1.2.3.4 : ...
    server_key<index> = <hostbane> : <networkname>-4 : ... --> for class C only
    <applist_%server_key> = all default application build according to system.ini
    <reqlist_%server_key> = all third-party requirements for application build according to CORE_APPS
    <runnerapps_%server_key> = all os-level requirements for application build according to UI_APPS
    <group_cluster_index> = server index in cluster group (tm3 = 3 , mngs2a = 2)
    """
    try:
        group_counter = 0
        group_list = []
        network_sections = sysConfig.get('RUNNER', 'network_sections')
        for item in sysConfig.items(section):
            key = item[0]
            if re.match('%s_?\d+' % host_key, item[0]): 
                value = {}
                for info in item[1:]:
                    hostname, ips = getNetworksDict(info.split(sysConfig.host_delimiter), network_sections,sysConfig)
                    for net, ip in ips.iteritems():
                        if sysConfig.get(net, 'version')['version'] == '6' :
                            sysConfig.set(section, 'v6_%s' %key, 'True')
                        d = sysConfig.get(net, 'version')['delimiter']
                        if ip.__len__() == 1:
                            network = sysConfig.get(net, 'network').split(d)[:-1]
                            network.append(ip[0])
                            network = d.join(network)
                        else:
                            getNetworkByIp(d.join(ip), network_sections)
                            network = d.join(ip)
                        value.update({net : network, 'hostname' : hostname})
                sysConfig.set(section, key, value)
                if sysConfig.has_option(section,'apps_%s' % item[0]):
                    sysConfig.set(section,'applist_%s' % item[0],[i.strip().lower() for i in sysConfig.get(section,'apps_%s' % item[0]).split(',')if i.strip()])
                elif not item[0][-1].isdigit() and sysConfig.has_option(section,'apps_%s' % item[0][:-1]):
                    sysConfig.set(section,'applist_%s' % item[0],[i.strip().lower() for i in sysConfig.get(section,'apps_%s' % item[0][:-1]).split(',')if i.strip()])
                elif sysConfig.has_option(section,'apps_%s' % host_key):
                    sysConfig.set(section,'applist_%s' % item[0],[i.strip().lower() for i in sysConfig.get(section,'apps_%s' %host_key).split(',') if i.strip()])
                elif sysConfig.DEFAULT_APPS and sysConfig.DEFAULT_APPS.has_key(section):
                    sysConfig.set(section,'applist_%s' % item[0],sysConfig.DEFAULT_APPS[section])
                else:
                    sysConfig.set(section,'applist_%s' % item[0],[])
                if sysConfig.get(section,'os_type'):
                    sysConfig.set(section,'os_type',sysConfig.get(section,'os_type').lower())
                    sysConfig.get(section,'applist_%s' % item[0]).insert(0,sysConfig.get(section,'os_type'))
                required_list = []
                for app in sysConfig.get(section,'applist_%s' % key):
                    if app in sysConfig.CORE_APPS.keys():
                        required_list.extend([req for req in sysConfig.CORE_APPS[app] if req not in required_list])
                sysConfig.set(section,'reqlist_%s' % key, required_list)
                if item[0][-1].isdigit():
                    group_counter = 1
                else:
                    servid = re.search('^%s(\d+)' % host_key, item[0]).group(1)
                    if not servid in group_list:
                        group_list.append(servid)
                        group_counter += 1
                sysConfig.set(section,'runnerapps_%s' % key, sysConfig.UI_APPS.get(section, []))
                sysConfig.set(section , 'group_cluster_index' , str(group_counter))
            elif re.match( '(?:%s)' % sysConfig.host_delimiter.join(network_sections.keys()) + '[\s\t]?-[\s\t]?\d+', item[1]):
                net = item[1].strip().split('-')
                d = sysConfig.get(net[0], 'version')['delimiter']
                if net[1].split(d).__len__() == 1:
                    network = sysConfig.get(net[0].strip(), 'network').split(d)[:-1]
                    network.append(net[1].strip())
                    #FIXME:Amir - Change delimiter (d)
                    sysConfig.set(section, key, d.join(network))
                else:
                    getNetworkByIp(net[1], network_sections)
                    sysConfig.set(section, key, net[1])
        return
    except:
        e = '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
        raise Exception, '%s serversDictBuild: ini Error Failed to build server info for \"%s\" section' % (e, section)
    
def buildSectionInfo(sysConfig, section, serverID):
    """
    buildSectionInfo adds server info option to sysConfig under server section for simplisity usage in conf file.
    buildSectionInfo set up these option under the server section:
    <network name in lower case>-rip = server nework rip --> for each network in the server dict
    <dg> = server default gw
    <server_id> = set server index number, No [ab]
    <server_key> = set server key/option
    <primary> = True/False only for the first section server
    <server-vip> = relevant server vip --> incluster server only
    <cluster_mode_detect> = set server host_key , if cluster set server host_key with its index
    <cluster_key_detect> =  set server_key index by cluster (mngs1a = mngs1 , tm1 = tm)
    <my_applist_%server_key> = full applications for on my server_key
    buildSectionInfo replace to each "{{ ID }}" string in all section values with server_id,
    exclude servers info options. 
    """
    try:
        server = sysConfig.get(section, serverID)
        sysConfig.set(section, 'server_key', serverID)
        sysConfig.server_key = serverID
        host_key_detect = sysConfig.get(section, sysConfig.host_key_detect)
        try:
            server_id = re.search('^%s(\d+)' % host_key_detect, serverID).group(1)
            sysConfig.set(section, 'server_id', server_id)
            for item in sysConfig.items(section):
                if not re.match('%s_?\d+' % host_key_detect, item[0]) and type(item[1]) == str and \
                       re.search('\{\{[\t\s]?ID[\s\t]?\}\}', item[1]):
                    sysConfig.set(section, item[0], re.sub('\{\{[\t\s]?ID[\s\t]?\}\}', server_id, item[1]))
        except:
            e = '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            raise Exception, '%s IllegalName Failed to get server ID from \"%s\" in %s' % (e, serverID, server)
        network_sections = sysConfig.get('RUNNER', 'network_sections')
        for k,v in server.iteritems():
            if k == 'hostname':
                sysConfig.set(section, k.lower(), v)
            else:
                sysConfig.set(section, k.lower() + '-rip', v)
        default_gateway = sysConfig.get(section,'default_gateway')
        sysConfig.set(section, 'dg', sysConfig.get(default_gateway, 'nexthop'))
        if serverID[-1].isdigit():
            sysConfig.set(section, 'cluster_key_detect', host_key_detect)
            if serverID[-1] == '1': 
                sysConfig.set(section, 'primary', 'True')
        else: 
            sysConfig.set(section, 'cluster_key_detect', host_key_detect+server_id)
            if serverID[-1] == 'a':
                sysConfig.set(section, 'primary', 'True')
        if re.search('^%s(\d+)' % host_key_detect,sysConfig.get(section, 'cluster_key_detect')):
            cluster_id = re.search('^%s(\d+)' % host_key_detect,sysConfig.get(section, 'cluster_key_detect')).group(1)
            sysConfig.set(section, 'cluster_id', cluster_id)
        else:
            sysConfig.set(section, 'cluster_id', '')
        sysConfig.set(section,'my_applist',sysConfig.get(section,'applist_%s' % serverID) + \
                      sysConfig.get(section,'reqlist_%s' % serverID) + sysConfig.get(section,'runnerapps_%s' % serverID))
        if sysConfig.has_option('RUNNER' , 'vip_detect') and sysConfig.get('RUNNER' , 'vip_detect'):
            cluster_vip = sysConfig.get('RUNNER', 'vip_detect')
        else: 
            cluster_vip = 'cluster_vip'
        cluster_vips = [ vip for vip in sysConfig.items(section) \
                         if re.match('%s_?\d+' % cluster_vip, vip[0]) and vip[1] ]
        if cluster_vips.__len__() > 0:
            cluster_vips = dict(cluster_vips)
            foundVip = True
            for nvip,vip in cluster_vips.iteritems():
                if re.search('\d+$', nvip):
                    vip_id = re.search('(\d+)$', nvip).group(1)
                else:
                    vip_id = False
                    continue
                if vip_id and re.search('\D%s[ab]?$' % vip_id, serverID):
                    sysConfig.set(section, 'server-vip', vip)
                    foundVip = True
                    break
            if not foundVip:
                raise Exception, 'buildSectionInfo Failed to get cluster_vip for %s' % server
        return
    except:
        e = '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
        raise Exception, '%s buildSectionInfo Failed to add server hostname/ips to \"%s\" in \"%s\"' % \
                (e, serverID, section)

def getNetworksDict(info, network_sections,sysConfig):
    try:
        info = [ i.strip() for i in info ]
        ips = {}
        for net in info[1:]:
            point = net.rfind('-')
            if point > -1 :
                d = sysConfig.get(net[:point].strip(),'version')['delimiter']
                ips.update({net[:point].strip(): net[point+1:].strip().split(d)})
            else:
                d = sysConfig.get((getNetworkByIp(net.strip(), network_sections)),'version')['delimiter']
                ips.update({getNetworkByIp(net.strip(), network_sections): net.strip().split(d)})
        return info[0], ips
    except:
        e = '%s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
        raise Exception, '%s getNetworksDict Failed to parse server hostname/ips in \"%s\"' % (e, info)
def getKey(self, s,k, required=True, Key=None):
    try:
        if Key:
            if self.get(s,k).has_key(Key):
                return self.get(s,k)[Key]
            else:
                []
        else:
            return self.get(s,k)
    except (NoOptionError, NoSectionError):
        if required:
            error = 'GetKey: Failed to get option \"%s\" from \"%s\" section: %s' % (k,s, sys.exc_info()[1])
            raise Exception, error
        else:
            return ''

def getListOfKeys(self, s, k, newKey=None, required=True, Key=None, reset=''):
    items = []
    j = 0
    try:
        _items = self.items(s)
        _items.sort(optionSorting)
        for i in _items:
            if i[0].startswith(k):
                if j == 0 and re.search('\d+$', i[0]):
                    j = int(re.search('(\d+)$', i[0]).group(1))
                elif j == 0:
                    j = 1
                if newKey:
                    if Key:
                        if not i[1].has_key(Key): raise Exception, "Key error in: %s=%s" % (i[0], i[1])
                        items.append((i[1][Key], re.sub('\{\{[\t\s]?ID[\s\t]?\}\}', str(j), newKey)))
                    else:
                        items.append((i[1], re.sub('\{\{[\t\s]?ID[\s\t]?\}\}', str(j), newKey)))
                else:
                    if Key:
                        if not i[1].has_key(Key): raise Exception, "Key error in: %s=%s" % (i[0], i[1])
                        items.append((i[1][Key], i[0]))
                    else:
                        items.append((i[1], i[0]))
                j += 1
    except:
        if required:
            raise Exception, '%s: Section=%s, KeyStartsWith=%s, newKey="%s", Key="%s" Error: %s' % \
                    ('getListOfKeys', s,k,newKey, Key, sys.exc_info()[1])
    if required and items.__len__() > 0:
        return items
    elif required and items.__len__() == 0:
        raise Exception, \
                '%s: Failed to build list form \"%s\" section with options \"%s\": No items where found.' \
                % ('getListOfKeys', s, k)
    else:
        return items
    

def networkSectionList(sysConfig):
    """
    Build network_sections Dict as:
    <Section network name> : <IP-calc obj for this network>
    """
    network_sections = {}
    for section in sysConfig.sections():
        if sysConfig.has_option(section, 'type') and sysConfig.get(section, 'type') == 'network':
            netsec = ipcalc.Network(sysConfig.get(section, 'network'))
            if netsec.v == 4:
                network_sections[section] =  ipcalc.Network('%s/%s' % (sysConfig.get(section, 'network'), ipcalc.netmask2int(sysConfig.get(section, 'netmask'))))
                delimiter = '.'
            elif netsec.v == 6:
                network_sections[section] =  ipcalc.Network('%s/%s' % (sysConfig.get(section, 'network') ,sysConfig.get(section, 'prefix')))
                delimiter = ':'
            else:
                raise Exception, 'networkSectionList: Failed to calc relevant network section for %s network' % section 
            sysConfig.set(section, 'version' , {'version' :str(netsec.v),'delimiter' : delimiter})          
    sysConfig.set('RUNNER', 'network_sections', network_sections)
    return network_sections

def getNetworkByIp(ip, network_sections):
    """
    Get ip and search in all network section to where it is belong.
    If cant find network for the IP it "raise"
    """
    for netName, netCalc in network_sections.iteritems():
        if netCalc.in_network(ip):
            return netName
    raise Exception, 'getNetworkByIp: Failed to get relevant network section for \"%s\" in %s networks' \
            % (ip, network_sections.keys())

def optionSorting(x,y):
    """
    Warp cmp in order to overcome sort of string. 
    This function replace the default sort cmp func of "sort" method
    """
    def getNum(str):
        if type(str) == tuple or type(str) == list:   
            str = str[0]
        if re.search('\d+$', str):
            return  int(re.search('(\d+)$', str).group(1))
        elif re.search('(\d+[a-z]$)', str):
            index,char = re.search('(\d+)([a-z]+)$', str).groups()
            return int(index) * 10000 + ord(char)
        else: 
            return str
    return cmp(getNum(x),getNum(y))

def dashId(file='/data/comverse/gw/config/component.txt'):
    """
    Gets Dashboard ID from component.txt file.
    For any exception return 1.
    """
    try:
        f = open(file)
        id = f.readline().strip()
        f.close()
        if re.match('\d+', id):
            return id
        else:
            return '1'
    except:
        return '1'
    
def global_required_apps_builder(sysConfig):
    if not sysConfig.GLOBAL_CORE_APPS:return 
    for appkey in sysConfig.GLOBAL_CORE_APPS.keys():
        if sysConfig.getAppsServers(appkey,check_by='full').__len__() > 0 :
            for requirement in sysConfig.GLOBAL_CORE_APPS[appkey]:
                if sysConfig.getAppsServers(requirement['required_by'],check_by='full').__len__() <= 0 :continue
                for section,server_list in sysConfig.getAppsServers(requirement['required_by'],check_by='full').iteritems():
                    for server_key in server_list:
                        sysConfig.set(section,'reqlist_%s' % server_key ,list(set(sysConfig.get(section,'reqlist_%s' % server_key) + requirement['required'] )))
                    if sysConfig.CORE_APPS.has_key(requirement['required_by']):
                        sysConfig.CORE_APPS[requirement['required_by']].extend(requirement['required'])
                    else:
                        sysConfig.CORE_APPS[requirement['required_by']] = requirement['required']
    return          
                    

def include_apps_builder(sysConfig): 
    for section in sysConfig.server_sections:
        for applist in sysConfig.getListOfKeys(section,'applist_'):           
            for app in applist[0] :
                if sysConfig.INCLUDED_APPS.has_key(app):
                    diff = list(set(sysConfig.INCLUDED_APPS[app]) - set(sysConfig.get(section,applist[1])))
                    if diff:
                        raise Exception, '%s dependency : %s application must be required' % (app , diff)
        
        
def setSectionSupportNetwork(sysConfig,section):
    for item in sysConfig.items(section):
        key = item[0]
        if re.match( '(?:%s)' % sysConfig.host_delimiter.join(sysConfig.network_sections.keys()) + '[\s\t]?-[\s\t]?\d+', item[1]):
            net = item[1].strip().split('-')
            d = sysConfig.get(net[0], 'version')['delimiter']
            if net[1].split(d).__len__() == 1:
                network = sysConfig.get(net[0].strip(), 'network').split(d)[:-1]
                network.append(net[1].strip())
                sysConfig.set(section, key, d.join(network))
            else:
                getNetworkByIp(net[1], sysConfig.network_sections)
                sysConfig.set(section, key, net[1])
    return      



