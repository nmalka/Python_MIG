
####################################
#   ModuleNmae: Pyfunc.py          #
####################################

import os, time, re ,sys, glob
from Pykex import DigHostsIPs
from Pytm import DigHostsIP as dighostip
from glob import glob
from pdb import set_trace as st
import fnmatch

def getIpPerApp(app, _, __):
    key_detect = _('MWAS', 'host_key_detect')
    modes =  __('MWAS', 'mode_' + key_detect)
    app_key = None
    for mode in modes:
        if mode[0].lower().find(app) > -1:
            app_key = mode[1].split('mode_'+key_detect)[1]
            break

    ip_port = _('MWAS', 'port_vip_%s%s' % (app, app_key))
    ip = ip_port.split(':')[0].strip()
    if not ip: raise Exception, 'MWAS Section - The value of "port_vip_%s%s" key is empty.' % (app, app_key)
    return ip

def getFiles(basePath, app, fileName):
    if app == 'gw':
        Index, file = getLastIndexFile(basePath, fileName)
        Files = file
        return Index, file

    allAppDirs = [f for f in glob(os.path.join(basePath, app+'*')) if os.path.isdir(f)]
    folderRegEx = re.compile(".*%s\d+" % app)
    indexs = []
    for i in range(0, len(allAppDirs)):
        if not re.match(folderRegEx, allAppDirs[i]):
            indexs.append(i)
    for i in range(0, len(indexs)):
        allAppDirs.pop(i)
        
    if len(allAppDirs) == 0:
        raise Exception,  'Can\'t found folders %s under %s.' % (app, basePath)
    allAppDirs.sort(sortDirs)
    index = 1
    Files = ''
    if len(allAppDirs) == 1:
        Index, file = getLastIndexFile(allAppDirs[0]+'/conf/', fileName)
        Files = file
        return Index, Files
    elif len(allAppDirs) > 1:
        for index in range(0, len(allAppDirs) - 1):
            Index, file = getLastIndexFile(allAppDirs[index]+'/conf/', fileName)
            if index == 0:
                retIndex = Index
            Files += file + ', '
    Index, file = getLastIndexFile(allAppDirs[-1]+'/conf/', fileName)
    Files += file
    return retIndex, Files

def getLastIndexFile(filePath, fileName):
    allFiles = [f for f in glob(os.path.join(filePath, fileName+'*')) if os.path.isfile(f)]
    type(allFiles)
    if len(allFiles) == 0:
        raise Exception,  'Can\'t found file that starts with %s under %s.' % (fileName, filePath)
    elif len(allFiles) > 0:
        allFiles.sort(sortFiles)
        index = int(allFiles[-1].split('xml.')[1])
        return index, allFiles[-1]


def sortFiles(x, y):
    x = os.path.basename(x)
    y = os.path.basename(y)
    x = int(x.split('xml.')[1])
    y = int(y.split('xml.')[1])
    return cmp(x, y)
def sortDirs(x, y):
    x = os.path.basename(x)
    y = os.path.basename(y)
    splitter = re.compile(r'[\D]')
    x = int(splitter.split(x)[-1])
    y = int(splitter.split(y)[-1])
    return cmp(x, y)


def DigHostsIP(reg, file='/etc/hosts'):
    return dighostip(reg, file='/etc/hosts')[0]

def ServerListIp(reg, user='',path='', dellimiter1='@', dellimiter2=':',dellimiter3=', ',suffix='', preffix=''): 
    hash=DigHostsIPs(reg)
    str=''
    for key in hash.keys():
        str=str+user+ dellimiter1 + key + dellimiter2 + path + dellimiter3 
    str=str[:-len(dellimiter3)]    
    str = suffix + str + preffix
    return str

def ServerListHosts(reg, user='',path='', dellimiter1='', dellimiter2='', dellimiter3=', ',suffix='', preffix=''):
    hash=DigHostsIPs(reg)
    str=''
    for value in hash.values():
        value=re.search(r'\s*%s\S*' % reg,value)
        temp_list=value.group().split()
        str=str+user+ dellimiter1 + temp_list[0] + dellimiter2 + path + dellimiter3 
    str=str[:-len(dellimiter3)]
    str = suffix + str + preffix
    return str

def SnmpList(hash):
    str=''
    for value in hash.values():
        if value:
            str=str+value+', '
    str=str[:-2]
    return str

def NumOfSnmpManagers(hash):
    snmp_amount = 0
    for val in hash.values():
        if val:
		    snmp_amount = snmp_amount + 1
    return snmp_amount

def NumOfTrapManagers(hash):
    return len(hash.keys())

def ServerId(reg):
	return re.search(r'(\s*%s)(\d+)' % reg, os.environ['HOSTNAME']).group(2)

def UrlIpAppender(url, hostName):
    '''
    Finds a URL and modifies the hostname to an IP.
    Gets: (url) string that has to be modified,
    (hostName) string to look for in a url.
    Returns: (self.url) a modified URL string.
    '''

    ip = DigHostsIP(hostName)
    startPart, endPart = re.search('(http.?://)(.*)(:.*)+', url).group(1), \
                         re.search('(http.?://)(.*)(:.*)+', url).group(3)
    url = '%s%s%s' % (startPart, ip, endPart)
    return url


def ConstDict(Dict, pattern, name='ConstDict()'):
    '''
    Extracts a dictionary from a bigger dictionary.
    Returns a dictionary.
    '''

    NewDict = {}
    for key, value in Dict.iteritems():
        if key.startswith(pattern) and value:
            NewDict[key] = value
    return NewDict

def Red(text):
    '''
    Gets a string and returns it in red.
    '''
    return "\033[31m%s\033[0m" % (text)

def Grn(text):
    '''
    Gets a string and returns it in green.
    '''
    return "\033[32m%s\033[0m" % (text)

def Ylw(text):
    '''
    Gets a string and returns it in yellow.
    '''
    return "\033[33m%s\033[0m" % (text)

def Blu(text):
    '''
    Gets a string and returns it in blue.
    '''
    return "\033[34m%s\033[0m" % (text)

def GetHash(ret,file='/etc/sysconfig/network-scripts/ifcfg-bond0',reg='='):
    hash = {}
    for line in open(file):
        if not line.startswith('#'):
            if line.strip():
                line = line.strip()
                line = re.sub(r',[\s\t]*$', '', line)
                hash[re.split(r'[\s\t]?%s[\s\t]?'%reg,
                line, 1)[0]] = re.split(r'[\s\t]?%s[\s\t]?'%reg, line,1)[1].strip()
    return hash[ret]

def xml_ip_block_builder(tag,reg=False,mode='tm', sysConfig=None):
    import elementtree.ElementTree as ET
    if mode == 'tm':
         root_name='TMsList'
    elif mode == 'mwas':
        root_name='MWASList'
    if sysConfig:
        if mode == 'tm':
            IPs = sysConfig.getListOfKeys(s = mode.strip().upper(), k = 'tm', Key = 'WDN')
            IPs = dict(IPs).keys()
        elif mode == 'mwas':
            IPs = (sysConfig.get(mode.strip().upper(), 'cluster_vip1'),)
    else:
        IPs = DigHostsIPs(reg).keys()
    root=ET.Element(root_name)
    counter=1
    for ip in IPs:
        Info_tag=ET.Element('Info')
        root.append(Info_tag)
        if mode == 'mwas':
            addtional_tag=ET.Element('InstanceID')
            addtional_tag.text=str(counter)
            counter+=1
            Info_tag.append(addtional_tag)
        new_tag=ET.Element(tag)
        new_tag.text=ip
        Info_tag.append(new_tag)
    return ET.ElementTree(root)

def get_gmt_offset():
    return time.strftime('%Z',(2010, 3, 2, 21, 47, 10, 1, 61, 0))

def DigHostsIP_Port(reg, port, file='/etc/hosts'):
    return '%s:%s' % (dighostip(reg, file='/etc/hosts')[0], port)

def DigHostsIPs_Delimiter(reg, staticList, delimiter=',', file='/etc/hosts'):
    return '%s%s%s' % (delimiter.join(DigHostsIPs('WDN|EDN').keys()), delimiter, staticList)

def HostName():
    return os.environ['HOSTNAME']


def RacHostVip(hosts):
    Str=''
    for host in hosts.split(','):
        Str = Str + host.strip() + ':' + host.strip() + '-vip' + ','    
    Str = Str[:-1]
    return Str

def RacNetworkAdd(Eth, HeatNetAdd, BondNetAdd):
    return Eth.split(',')[0] + ':' + HeatNetAdd + ':2,bond0:'  + BondNetAdd + ':1' 


def GetServerID(
                   file='/data_local/Python/system.ini',
                   identifierPath='/data_local/Python/',
                   wildcard='server_*.info',
                   SchemaName='APPDB'):
    serverID = glob.glob(os.path.join(identifierPath,wildcard))
    serverID = re.search('server_(.*)([0-9])\.info', serverID[0]).group(2)
    return SchemaName+str(serverID)

def GetPrimary(                   file='/data_local/Python/system.ini',
                   identifierPath='/data_local/Python/',
                   wildcard='server_*.info',
                   SchemaName='APPDB'):
    serverID = glob.glob(os.path.join(identifierPath,wildcard))
    serverID = re.search('server_(.*)([0-9])\.info', serverID[0]).group(2)
    return serverID

def publight_prx_config(configuration_file,Sysconfig,destenation_file,*args,**kargs):
    import copy,Pyfunc
    from elementtree import ElementTree as Etree
    import re
    from Pyxml import get_parent,tree_xpath,ReformatXmlTree

    PRX1HAIP='[prx1haIp]'
    PRX1GWIP='[prx1GwIp]'
    PRX1HAGWIP='[prx1haGwIp]'
    PRX1PEMADDR='[prx1pemAddr]'
    TIMEZONE='[Europe/Berlin]'
    SITEID='siteId'

    _=Sysconfig
    def sorted_dict_keys(D):
        P=D.keys()
        for I in range((len(P)-1)):
            for J in range((len(P) - 1) - I):
                if D[P[J]] > D[P[J+1]]:
                    TMP=P[I]
                    P[I]=P[I+1]
                    P[I+1] = TMP
        return P


    tree=Etree.parse(configuration_file)
    root=tree.getroot()
    ##########################Reformat General Configurations###############################
    ##Configure Site ID
    Site_ID_Tag=tree_xpath(root=root,xpath='/configuration/folder/param/name', text=SITEID)
    Site_ID_Parent=get_parent(root,Site_ID_Tag[0])
    Site_ID_Value_Tag=(tree_xpath(root=Site_ID_Parent,xpath='/param/value'))[0]
    Site_ID_Value_Tag.text=_('APP_CONFIG', 'site_id', False) or '1'
    ##configure SNMP community
    if _('SNMP', 'community',False):
        Snmp_Tag=tree_xpath(root=root,xpath='/configuration/folder/folder', attributes={'name':'trap'})[0]
        tree_xpath(root=Snmp_Tag,xpath='/folder/param/value',text='public')[0].text= _('SNMP', 'community')
    else:
        raise Exception('Snmp Community is not defined')
    ####################################Load Prxs Templates#################################
    Prx_Template=tree_xpath(root=root,xpath='/configurations/folder/folder/folder', attributes={'name':'prxs1'})
    if len(Prx_Template) >1:
        raise Exception('Prx template Error too many prxs templates (only 1 template must be defined)')
    elif len(Prx_Template) <1 :
        raise Exception('No Prx template found')
    else:
        Prx_Template=Prx_Template[0]
    ####################Load All PRX Servers and modify tempalte to match###################
    Prx_servers=Pyfunc.DigHostsIPs('prx\d+\b*')
    Sorted_Prx_servers=sorted_dict_keys(Prx_servers)
    Prx_Template_Root=get_parent(parent=root,elem=Prx_Template)
    Prx_Template_Root.remove(Prx_Template)
    ####Do we have DPI in the system ?
    if not _('DPI', 'type',False):
         return
    for I in range(len(Sorted_Prx_servers)):
         Template_Clone=copy.deepcopy(Prx_Template)
         Template_Clone.set('name','prxs'+str(I+1))
         tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=r'prx\d+\b')[0].text=Prx_servers[Sorted_Prx_servers[I]].strip()

         if _('DPI', 'haprx'+str(I+1)+'haip',False):
             tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=PRX1HAIP)[0].text=_('DPI', 'haprx'+str(I+1)+'haip')
         else:
             raise Exception('haprx'+str(I+1)+'haip is not defined')
         if _('DPI', 'haprx'+str(I+1)+'gwip',False):
             tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=PRX1GWIP)[0].text=_('DPI', 'haprx'+str(I+1)+'gwip')
         else:
             raise Exception ('haprx'+str(I+1)+'gwip is not defined')
         if _('DPI', 'haprx'+str(I+1)+'hagwip',False):
             tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=PRX1HAGWIP)[0].text=_('DPI', 'haprx'+str(I+1)+'hagwip')
         else:
             raise Exception('haprx'+str(I+1)+'hagwip is not defined')
         if _('DPI', 'haprx'+str(I+1)+'pemaddr',False):
             tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=PRX1PEMADDR)[0].text=_('DPI', 'haprx'+str(I+1)+'pemaddr')
         else:
             raise Exception('haprx'+str(I+1)+'pemaddr is not defined')
         tree_xpath(root=Template_Clone,xpath='/folder/param/value',text=TIMEZONE)[0].text=_('GENERAL','time_zone')


         Prx_Template_Root.append(Template_Clone)
    #######################################Reformat the Tree################################
    ReformatXmlTree(elem=root,level=0)
    tree.write(destenation_file)
    return True


def build_log_rotate(dir):
    matches = []
    for root, dirnames, filenames in os.walk(dir):
        for filename in fnmatch.filter(filenames, '*.log'):
            matches.append(os.path.join(root, filename))

    for root, dirnames, filenames in os.walk(dir):
        for filename in fnmatch.filter(filenames, '*.err'):
            matches.append(os.path.join(root, filename))

    try:
        f = open(os.path.join('/etc/logrotate.d/', 'mysqlprocess'), 'w')

        template = '{\n    size 10M\n    create 660 mysql mysql\n    rotate 4\n    copytruncate\n}\n\n'
        for log in matches:
            f.write(log+'\n')
            f.write(template)
        f.close()
    except:
        f.close()
        raise Exception, 'Couln\'t write %s file under /etc/logrotate.d/.' % os.path.join(out_file_dir, 'mysqlprocess')

def build_logrotate(dir, force=False):
    if os.path.isfile(os.path.join('/etc/logrotate.d/', 'mysqlprocess')):
        if not force:
            return
        else:
            build_log_rotate(dir)
    else:
        build_log_rotate(dir)
