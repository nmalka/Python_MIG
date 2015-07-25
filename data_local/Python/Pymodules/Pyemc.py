
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#	Date: 18/06/2009			 #
#   ModuleNmae: Pyemc.py         #
##################################

from Pyfiledit import builder, CopyUtils
from Pydecorators import *
import os, time, re ,sys, shutil
from glob import glob
from commands import getstatusoutput as getstatus

# GolbalVars
#navicli = '/opt/Navisphere/bin/navicli'
modprobe = '/sbin/modprobe'


def GetInfoFromSP(logger, config, emc_user, emc_pass, ip):
    dic_dev = {}
    logger.debug('Running: /opt/Navisphere/bin/naviseccli  -h %s -user %s -password %s -scope 0  getall\
                 |grep "Server Name:" -B 9 -A 1'  % (ip, emc_user, emc_pass))
    devices = getstatus('/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 getall|grep "Server Name:"\
                       -B 9 -A 1' % (ip, emc_user, emc_pass))[1]
    dev = [ i for i in devices.split('\n') if i != '--\n' and i != '--' ]
    Server_Name = None
    Server_IP = None
    sgName = None
    HBA = None
    for i in dev:
        if re.search('([\s\t]+)?Server Name:[\s\t]+(\w+)',i):
            Server_Name = re.search('([\s\t]+)?Server Name:[\s\t]+(\w+)',i).group(2)
        if re.search('([\s\t]+)?Server IP Address:[\s\t]+(.*)',i):
            Server_IP = re.search('([\s\t]+)?Server IP Address:[\s\t]+(.*)',i).group(2) 
        if re.search('([\s\t]+)?StorageGroup Name:[\s\t]+(.*)',i):
            sgName = re.search('([\s\t]+)?StorageGroup Name:[\s\t]+(.*)',i).group(2)
        if re.search('([\s\t]+)?HBA UID:[\s\t]+(.*)',i):
            HBA = re.search('([\s\t]+)?HBA UID:[\s\t]+(.*)',i).group(2)
    if Server_Name and Server_IP and sgName and HBA:
        dic_dev[HBA]={'Server_Name': Server_Name, 'Server_IP' : Server_IP, 'SG' : sgName }
    return dic_dev 

"""
def LvmDev(logger, config):
    lvm = {}
    for Mount in config['Mounts'].split(', '):
        lvm[Mount.split(':',1)[0]] = {Mount.split(':',1)[1].split(':')[0]:Mount.split(':',1)[1].split(':')[1]}
    logger.debug('lvm hash from config file:\n%s' % lvm)
    return lvm

def HashDev(logger, config):
    logger.debug('Running: /sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
    dev = Getdev(config)
    tmp=[]
    if config.has_key('MultiCDRC') and config['MultiCDRC'] == '1':
        for x in config['Mounts'].split(', '):
            count = 0
            try:
                Luname=re.search('(.*)(:)(.*:)',x).group(1)
            except:
                raise Exception,  'Missmatch between LUN name in the EMC to Mounts parametter from the config file'
            for i in dev:
                if re.search('\[%s\]' %Luname ,i) :
                    tmp.append(dev[count -2])
                    tmp.append(dev[count -1])
                    tmp.append(dev[count])
                count = count + 1
        dev=tmp    
    logger.debug('powermt:\n%s' % dev)
    if len(dev)%3 or len(dev) == 0:
        raise Exception,  '%s/n Canot get pseudo name from emc.' %dev
    lvm = GetLvm(config) 
    logger.debug('lvm:\n%s' % lvm)
    if not config.has_key('MultiCDRC') or config['MultiCDRC'] == '0':
        if len(dev)/3 != len(lvm.keys()):
            raise Exception,  'Missmatch between Pseudo name in the EMC to Mounts parametter fron the config file'
    return dev, lvm
def GetLvm(config):
    lvm = {}
    for Mount in config['Mounts'].split(', '):
        lvm[Mount.split(':',1)[0]] = {Mount.split(':',1)[1].split(':')[0]:Mount.split(':',1)[1].split(':')[1]}
    return lvm

def Getdev(config):
    devices = os.popen('/sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
    dev = devices.readlines()
    dev = [ i for i in dev if i != '--\n' ]
    devices.close()
    return dev

def getPseudo(logger,config):
 
    if not config.has_key('MultiCDRC') or config['MultiCDRC'] == '0':
        logger.debug('/sbin/powermt display dev=all | /bin/grep -i \'Pseudo name\'')
        devices = os.popen('/sbin/powermt display dev=all | /bin/grep -i \'Pseudo name\'')
        pseudo = devices.readlines()
        logger.debug('powermt:\n%s' % pseudo)
        devices.close()
    elif config.has_key('MultiCDRC') and config['MultiCDRC'] == '1':
        tmp=[]
        logger.error('Running: /sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
        devices = os.popen('/sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
        dev = devices.readlines()
        dev = [ i for i in dev if i != '--\n' ] 
        for x in config['Mounts'].split(', '):
            try:
                Luname=re.search('(.*)(:)(.*:)',x).group(1)
            except:
                raise sys.exc_info()[0], '%s\n%s' (sys.exc_info()[1],
                            'Missmatch between LUN name {%s} in the EMC to Mounts parametter fron the config file' %x)
            count = 0
            for i in dev:
                if re.search('\[%s\]' %Luname ,i) :
                    tmp.append(dev[count - 2])
                count = count + 1
        pseudo=tmp
    if len(pseudo) == 0:
        raise Exception,  'Canot get pseudo name from emc.'
    devs = []
    while len(pseudo)>0:
        dev = pseudo.pop(0)[:-1]
        p = re.search('pseudo name=(emcpower\w)', dev, re.I).group(1)
        devs.append('/dev/' + p)
    num = len(devs)
    logger.debug('devs list:\n%s' % devs)
    return num, (' ').join(devs)

def umountCheck(logger, lvm):
    paths = []
    logger.info('Starting to check that all directories are mounted')
    for key, hash in lvm.iteritems():
        paths.append(hash.items()[0][1])
    for path in paths:
        if not os.path.ismount(path):
            raise Exception, 'Directory \'%s\' is not mounted' % path 


"""
def mountCheck(logger, FS_Topology):
    paths = []
    logger.info('Starting to check that there are no mounted directories')
    for FS in FS_Topology:
        for v in FS.values():
            if os.path.ismount(v['MountPoint']):
                raise Exception, 'Directory \'%s\' is allready mounted' % v['MountPoint']
    
def powerPath(cmd, log=''):
    powerPath = '/etc/init.d/PowerPath %s %s' % (cmd, log)
    if getstatus(powerPath)[0] != 0:
        return False
    return True

def reloadHBA(hba, log=''):
    time.sleep(5)
    if getstatus('%s -v -r %s %s' % (modprobe, hba, log))[0] != 0:
        return False
    time.sleep(10)
    if getstatus('%s -v -i %s %s' % (modprobe, hba, log))[0] != 0:
        return False
    time.sleep(5)
    return True

def navi(cmd, log=''):
    navi = '/etc/init.d/hostagent %s %s' %(cmd, log)
    if getstatus(navi)[0] != 0:
        return False
    return True
class agentconfig(builder):
    def __call__(self, *args, **kwargs):
        self.logger.error('Testing the FCS Zoning on the server...')
        self.logger.info('running: cat /proc/scsi/scsi | grep \'Vendor: DGC\'')
        if getstatus('/bin/cat /proc/scsi/scsi | /bin/grep \'Vendor: DGC\' %s' % self.log)[0] != 0:
            raise Exception, 'Problem with the fiber connection, Server can NOT see the EMC storage\n \
                             Check the Zoning on the FCS reboot the server and then rerun the script'
        Hostname = self.config.get('_',None) and self.config['_'](self.config['Section'], 'hostname', False) or \
                  os.environ['HOSTNAME']
        if self.config.get('_',None):
            emc_user = self.config['EMC_User']
            emc_pass = self.config['EMC_Password']
            SPA = self.config['SPA']
            dic_dev = GetInfoFromSP(self.logger, self.config, emc_user, emc_pass, SPA)
            for k,v in dic_dev.iteritems():
                if dic_dev[k]['Server_Name'] == Hostname and self.config['SG'] != dic_dev[k]['SG']:
                    raise Exception, 'Another Host {%s} with the same name {%s} is register, Change to Unique host name'\
                                 %(dic_dev[k]['Server_IP'], dic_dev[k]['Server_Name'])
        mountCheck(logger=self.logger, FS_Topology=self.config['FS_Topology'])
        self.agentID()
        self.navi_sync()
    def agentID(self):
        from Pytm import DigHostsIP 
        ip, name = DigHostsIP(os.environ['HOSTNAME'])
        name = os.environ['HOSTNAME'] + '\n'
        agentID = '/agentID.txt'
        self.logger.error('Starting the parser for: \'agentID.txt\' file')
        file = open(agentID, 'w')
        file.write(name)
        file.write(ip + '\n')
        file.close()
        self.logger.error('\'agentID.txt\' was successfully parsed')
        try:
            os.unlink('/var/log/HostIdFile.txt')
            self.logger.info('/var/log/HostIdFile.txt was removed.')
        except OSError:
            pass 
    def navi_sync(self):
        self.logger.info('Running: dmsetup remove_all -f')
        if getstatus('/sbin/dmsetup remove_all -f')[0] != 0: 
            raise Exception, 'Failed to remove device from multipath'
        if not navi('stop', log=self.log):
            raise Exception, 'Canot stop navi'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('stop', log=self.log):
            raise Exception, 'Can not stop Powerpath'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Realoding fiber %s driver' % self.config['HBA'])
        if not reloadHBA(hba=self.config['HBA'], log=self.log):
            raise Exception, 'Faild to reload fiber %s driver Before rerunning the script \n \
                              make sure the \'%s\' driver is loaded' % (self.config['HBA'], self.config['HBA'])
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('start', log=self.log):
            raise Exception, 'Canot start Powerpath'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not navi('start', log=self.log):
            raise Exception, 'Canot start navi'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Assigning the %s to \'%s\'' % (os.environ['HOSTNAME'], self.config['SG']))
        """
        fc_hosts = glob('/sys/class/fc_host/host*')
        for fc_host in fc_hosts:
            f = os.popen('cat %s/node_name' %fc_host)
            f = f.readline().strip('\n')
            hbauid_node = ':'.join([f[2:][i:i+2] for i in range(0,len(f[2:]),2) ])
            f = os.popen('cat %s/port_name' %fc_host)
            f = f.readline().strip('\n')
            hbauid_port = ':'.join([f[2:][i:i+2] for i in range(0,len(f[2:]),2) ])
            self.logger.info('Running: %s -h %s -User %s -Password %s -Scope 0 storagegroup -setpath -o -gname %s -hbauid %s:%s\
                             -sp a -spport 1 -type 3 -ip %s -host %s -failovermode 1 -arraycommpath 1' %( self.config['naviseccli'],
                             self.config['SPA'],self.config['EMC_User'], self.config['EMC_Password'], self.config['SG'],
                             hbauid_node,hbauid_port, self.config['IP'],os.environ['HOSTNAME']))
            if getstatus('%s -h %s -User %s -Password %s -Scope 0 storagegroup -setpath -o -gname %s -hbauid %s:%s \
                          -sp a -spport 1 -type 3\
                          -ip %s -host %s -failovermode 1 -arraycommpath 1 ' %( self.config['naviseccli'],
                          self.config['SPA'], self.config['EMC_User'],self.config['EMC_Password'],self.config['SG'], 
                          hbauid_node,hbauid_port,self.config['IP'], os.environ['HOSTNAME']))[0] != 0:
                raise Exception, 'Failed to register %s:%s' % (hbauid_port,hbauid_node)
        if getstatus('%s -h %s -User %s -Password %s -Scope 0 storagegroup -sethost -host %s -failovermode 1 -arraycommpath 1 \
                      -type 3 -unitserialnumber array -o ' % (self.config['naviseccli'],
                      self.config['SPA'], self.config['EMC_User'],self.config['EMC_Password'],os.environ['HOSTNAME']))[0] != 0:
            raise Exception, 'Failed to Logged in %s' % (os.environ['HOSTNAME'])
        """
        self.logger.info('Running: %s -h %s -User %s -Password %s -Scope 0 storagegroup -connecthost -o -host %s -gname %s' % \
                        (self.config['naviseccli'], self.config['SPA'],self.config['EMC_User'], self.config['EMC_Password'],
                         os.environ['HOSTNAME'], self.config['SG']))
        if getstatus('%s -h %s  -User %s -Password %s -Scope 0 storagegroup -connecthost -o -host %s -gname %s %s' % \
                    (self.config['naviseccli'], self.config['SPA'], self.config['EMC_User'], 
                     self.config['EMC_Password'], os.environ['HOSTNAME'], self.config['SG'], self.log))[0] != 0:
            raise Exception, 'Failed to assign %s to %s' % (os.environ['HOSTNAME'], self.config['SG'])
        self.logger.error('Sleeping for 20 sec')
        time.sleep(20)
        if not navi('stop', log=self.log):
            raise Exception, 'Can not stop navi'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('stop', log=self.log):
            raise Exception, 'Can not stop Powerpath'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Realoding fiber %s driver' % self.config['HBA'])
        if not reloadHBA(hba=self.config['HBA'], log=self.log):
            raise Exception, 'Faild to reload fiber %s driver Before rerunning the script \n\
                             make sure the \'%s\' driver is loaded' %(self.config['HBA'], self.config['HBA'])
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('start', log=self.log):
            raise Exception, 'Canot start Powerpath'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not navi('start', log=self.log):
            raise Exception, 'Canot start navi'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Verify \'navi_sync\' by getting luns pseudo name form EMC')
        self.logger.error('%s successfully assigned to %s' % (os.environ['HOSTNAME'], self.config['SG']))
        self.logger.error('Running: dmsetup remove_all -f')
        if getstatus('/sbin/dmsetup remove_all -f')[0] != 0:
            raise Exception, 'Failed to remove device from multipath'
        for FS_Topology in self.config['FS_Topology']:
            for v in FS_Topology.values():
                if os.path.isdir('/dev/%s' % v['VG']) : shutil.rmtree('/dev/%s' % v['VG'])

class build_arch(object):
    def __build_arch__(self, config, componentID, loggerName='', *args, **kwargs):
        EMC = False
        for FS_Topology in self.config['FS_Topology']:
            if EMC : break
            for k,v in FS_Topology.iteritems():
                if v['type'].upper() == 'EMC':
                    EMC = True
                    break
        if EMC: self.GetEMCdev()
        self.CheckMissingDev()

    def GetEMCdev(self):
        devices = getstatus('/sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')[1]
        dev = [ i for i in devices.split('\n') if i != '--\n' ]
        pseudoName = None
        sgName = None
        lunName = None
        for pseudo in dev:
            if re.search('pseudo name=(emcpower\w)', pseudo, re.I):
                pseudoName = re.search('pseudo name=(emcpower\w)', pseudo, re.I).group(1)
                pseudoName = '/dev/' + pseudoName
            if re.search('.* ID=.*\[(.*?)\]', pseudo, re.I):
                sgName = re.search('.* ID=.*\[(.*?)\]', pseudo, re.I).group(1)
            if re.search('Logical device ID=.*\[(.*?)\]', pseudo, re.I):
                lunName = re.search('Logical device ID=.*\[(.*?)\]', pseudo, re.I).group(1)
            if pseudoName and sgName and lunName:
                for FS_Topology in self.config['FS_Topology']:
                    for k,v in FS_Topology.iteritems():
                        if v['type'].upper() == 'EMC' and k == lunName:
                            v['pseudo'] = pseudoName 
                pseudoName = None
                sgName = None
                lunName = None
                
    def CheckMissingDev(self):
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                if not v['pseudo']:
                    raise Exception, 'Missmatch between Lun %s  name in the EMC to Mounts parametter fron the config file' % k
                
            
class Pvcreate(builder,build_arch):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Pvcreate, self).__init__(config=config, componentID=componentID, loggerName=loggerName, 
                *args, **kwargs)        
        super(Pvcreate, self).__build_arch__(config=config, componentID=componentID, loggerName=loggerName, 
                *args, **kwargs)        
        mountCheck(logger=self.logger, FS_Topology=self.config['FS_Topology'])
    def __call__(self, *args, **kwargs):
        self.pv_vg_create()
    def pv_vg_create(self):
        self.logger.error('Creating pv and vg on the system')
        LUNs= []
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                if k not in LUNs:
                    LUNs.append(k)
                    self.logger.error('Running: %s %s' %(v['pvcreate'], v['pseudo']))
                    if getstatus('%s %s %s' % (v['pvcreate'], v['pseudo'], self.log))[0] != 0:
            	        raise Exception,  'Faild to run: \'pvcreate %s\'' % v['pseudo']
                    self.logger.error('successfully: %s %s' %(v['pvcreate'], v['pseudo']))
                    self.logger.error('Running: %s %s %s' % (self.config['vgcreate'],v['VG'], v['pseudo']))
                    if getstatus('%s %s %s %s' % (self.config['vgcreate'],v['VG'], v['pseudo'], self.log))[0] != 0:
                        self.logger.error('Faild to run: \'vgcreate %s %s\'' % (v['VG'],v['pseudo']))
                        print  getstatus('%s %s %s %s' % (self.config['vgcreate'],v['VG'], v['pseudo'], self.log))[1] 
                        if getstatus('%s %s %s %s' % (self.config['vgextend'],v['VG'], v['pseudo'], self.log))[0] != 0:
                            raise Exception,  'Faild to run: \'vgextend %s %s\'' % (v['VG'],v['pseudo'])
                        else:
                            self.logger.error('successfully: vgextend %s %s' % (v['VG'], v['pseudo']))
                    else:
                        self.logger.error('successfully: vgcreate %s %s' % (v['VG'], v['pseudo']))

        
class lvm_clean(builder, build_arch):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(lvm_clean, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)  
        super(lvm_clean, self).__build_arch__(config=config, componentID=componentID, loggerName=loggerName, 
                *args, **kwargs)        

    def __call__(self, *args, **kwargs):
        self.clean()

    def clean(self):
        VGs = []
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                if v['VG'] not in VGs: 
                    VGs.append(v['VG'])
                    self.logger.error('Starting to clean old LVM from the system')
                    self.logger.error('Trying to vgimport %s' % v['VG'])
                    if getstatus('%s %s %s' % (self.config['vgimport'], v['VG'], self.log))[0] != 0:
                        self.logger.error('vgimport was not needed - This step can be ignored')
                    else:
                        self.logger.error('successfully: vgimport %s' % v['VG'])
                    self.logger.error('Trying to vgchange %s' % v['VG'])
                    if getstatus('%s %s %s' % (self.config['Disable_VG'], v['VG'], self.log))[0] != 0:
                        self.logger.error('vgchange was not needed - This step can be ignored')
                    else:
                        self.logger.error('successfully: vgchange %s' % v['VG'])
                    self.logger.error('Trying to vgremove  %s' % v['VG'])
                    if getstatus('%s  %s %s' % (v['vgremove'], v['VG'], self.log))[0] != 0:
                        self.logger.error('vgremove was not needed - This step can be ignored')
                    else:
                        self.logger.error('successfully: vgremove  %s' % v['VG'])
                self.logger.error('%s %s' % (v['pvremove'],v['pseudo']))
                if getstatus('%s %s %s' % (v['pvremove'],v['pseudo'], self.log))[0] != 0:
                    self.logger.error('pvremove was not needed - This step can be ignored')
                else:
                    self.logger.error('successfully: %s %s' % (v['pvremove'],v['pseudo']))

class lvm_scan(builder):
        def __call__(self, *args, **kwargs):
            self.logger.error('Preforming LMV scan by running: \'vgscan\', \'lvscan\'')
            if getstatus('%s %s' % (self.config['vgscan'],self.log))[0] != 0:
                raise Exception,  'Faild to run: \'vgscan\''
            self.logger.error('successfully: vgscan')
            if getstatus('%s %s' % (self.config['lvscan'],self.log))[0] != 0:
                raise Exception, 'Faild to run: \'lvscan\'' 
            self.logger.error('successfully: lvscan')

class GetPVSize(build_arch):
    def __GetPVSize__(self, config, componentID, loggerName='', *args, **kwargs):
        super(GetPVSize, self).__build_arch__(config=config, componentID=componentID, loggerName=loggerName,
                *args, **kwargs)
        self.getPVSize()
    def getPVSize(self):
        TMP = {}
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                pvdisplay = getstatus('%s %s' % (self.config['pvdisplay'], v['pseudo']))[1]
                for i in pvdisplay.split('\n'):
                    if re.search('Total PE[\t\s]*(\d+).*', i, re.I):
                        Totals = re.search('Total PE[\t\s]*(\d+).*',i, re.I).group(1)
                        if int(v['percent']) > 100 or int(v['percent'])<0 :
                            raise Exception, 'percent must to be 0-100'
                        else:
                            percent = int(v['percent'])
                        if TMP.has_key(k):
                            Remain = int(TMP[k]['Remain'])
                        else:
                            Remain = int(Totals)
                        Total = percent*int(Totals)/100.0
                        if int(str(Total).split('.')[1]) > 5: Total = int(str(Total).split('.')[0]) + 1
                        else : 
                            Total = int(str(Total).split('.')[0])
                        if Total > Remain : Total = Remain
                        Remain = Remain - Total
                        TMP[k] = {'Remain' : Remain}
                        v['total'] = Total
             
class lvm_create(builder,GetPVSize):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(lvm_create, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)        
        super(lvm_create, self).__GetPVSize__(config=config, componentID=componentID, loggerName=loggerName, 
                *args, **kwargs)        
    def __call__(self, *args, **kwargs):
        self.lvcreate()        
    def lvcreate(self):    
        self.logger.error('Creating lv on the system')
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                lvcreate = '%s %s %s' % (v['lvcreate'],v['total'], self.log)
                self.logger.error('Runnnig: %s' % lvcreate)
                if getstatus(lvcreate)[0] != 0:
                    raise Exception, 'Faild to run: \'%s %s\'' % (v['lvcreate'],v['total'])
                self.logger.error('Succesefully: %s %s' % (v['lvcreate'],v['total']))

class Makefs(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Makefs, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        self.makefs()
    def makefs(self):
        self.logger.error('Running makefs on the system')
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                self.logger.error('Runnnig: %s' % v['mkfs'])
                if getstatus(v['mkfs'])[0] != 0:
                    raise Exception, 'Faild to run: \'%s\'' % v['mkfs ']
                else:
                    self.logger.error('Succesefully: %s' % v['mkfs'])


class DirsCreation (builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DirsCreation, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        self.makeDirsAndPer()
    def makeDirsAndPer(self):
        for k,v in self.config['DIR_Topology'].iteritems():
            if not os.path.exists(k):
                os.makedirs(k)
                self.logger.error('mkdir %s' %(k))

class DirsPermissions(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DirsPermissions, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        self.makeDirsAndPer()
    def makeDirsAndPer(self):
        for k,v in self.config['DIR_Topology'].iteritems():
            CHowner = getstatus('\chown %s:%s %s' %( v['USER'],v['GROUP'],k))
            if CHowner[0] != 0: 
                raise Exception, 'Failed Changing Owner to %s %s : %s\n%s' %(k,v['USER'],v['GROUP'], CHowner[1])
            self.logger.error('Changing Owner to %s %s : %s' %(k,v['USER'],v['GROUP']))
            CHmod = getstatus('\chmod %s %s' %( v['CHMOD'],k))
            if CHmod[0] != 0:
                raise Exception, 'Failed Changing mode to %s %s\n%s' %(k,v['CHMOD'], CHowner[1])

class Vgenable(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Vgenable, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        self.vgenable()
    def vgenable(self):
        VG = []
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                if v['VG'] not in VG:
                    VG.append(v['VG'])
                    if getstatus('%s %s %s' % (self.config['vgimport'],v['VG'], self.log))[0] != 0:
                        self.logger.error('vgimport was not needed - This step can be ignored')
                    else:
                        self.logger.error('successfully: vgimport %s' % v['VG'])
                    if getstatus('%s  %s %s' % (self.config['Enable_VG'],v['VG'], self.log))[0] != 0:
                        self.logger.error('vgchange was not needed - This step can be ignored')
                    else:
                        self.logger.error('successfully: %s %s' % (self.config['Enable_VG'],v['VG']))
                    self.logger.error('Runnnig: %s' % v['Enable_LV'])

                    if getstatus('%s %s' % (v['Enable_LV'], self.log))[0] != 0:
                        raise Exception, 'Faild to run: \'%s\'' % v['Enable_LV'] 
                    self.logger.error('Succesefully: \'%s\'' % v['Enable_LV'])
            
        

class mount_lvm(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(mount_lvm, self).__init__(config=config, componentID=componentID, 
                loggerName=loggerName, *args, **kwargs)        
    def __call__(self, *args, **kwargs):
        self.mount()
    def mount(self):
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems(): 
                if not os.path.ismount(v['MountPoint']):
                    if getstatus('%s' % (v['Mount_Command']))[0] != 0:
                        raise Exception, 'Faild to run: \'%s\'' % (v['Mount_Command'])
                    else:
                        self.logger.error('Succesefully: \'%s\'' % v['Mount_Command'])
                else:
                    self.logger.error('Already Mounted %s' %(v['MountPoint']))

class edit_fstab(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(edit_fstab, self).__init__(config=config, componentID=componentID, 
                loggerName=loggerName, *args, **kwargs)    
    def __call__(self, *args, **kwargs):
        methodDict = {'/etc/fstab' : 'fstab'}
        super(edit_fstab, self).__call__(editFiles=['/etc/fstab'], methodDict=methodDict)
    def fstab(self):
        lines=[]
        Flag = False
        for line in self.linesRef:
            for FS_Topology in self.config['FS_Topology']:
                for k,v in FS_Topology.iteritems():
                    if re.search('.*[\s\t]+%s[\s\t]+.*'% v['MountPoint'],line):
                        Flag = True
                        break
            if not Flag:
                lines.append(line)
                Flag = False
        for FS_Topology in self.config['FS_Topology']:
            if v['FSTAB']:lines.append('%s\n' %v['FSTAB'])
        self.file.writelines(lines)

class lock_file(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(lock_file, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        for FS_Topology in self.config['FS_Topology']:
            for k,v in FS_Topology.iteritems():
                if not os.path.isfile('%s/%s' %(v['MountPoint'], self.config['lock_file'])):
                    f = open('%s/%s' % (v['MountPoint'],self.config['lock_file']), 'w')
                    f.close()
                    if getstatus('chattr +i %s/%s' % (v['MountPoint'],self.config['lock_file']))[0] != 0:
                         raise Exception, 'Faild to run: \'chattr +i %s/%s\'' % (v['MountPoint'], self.config['lock_file'])
                    self.logger.error('Succesefully: \'%s/%s\'' % (v['Mount_Command'],self.config['lock_file']))

class PP_Lic(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(PP_Lic, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)
    def __call__(self, *args, **kwargs):
        PP_Lic = getstatus('%s -add key %s' % (self.config['emcpreg'],self.config['PP_lic']))
        if PP_Lic[0] != 0:
             Fault = True
             for line in PP_Lic[1].split('\n'):
                 if re.search('[\s\t]+%s[\s\t]+is already present'%self.config['PP_lic'],line):
                     self.logger.error('Ignore: license already installed')
                     Fault = None 
             if Fault:
                 raise Exception, 'Faild to run: \'%s -add key %s - %s\'' % (self.config['emcpreg'],self.config['PP_lic'], PP_Lic[1])
        self.logger.error('Succesefully: \'%s -add key %s\'' % (self.config['emcpreg'],self.config['PP_lic']))
                
class deregister(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(deregister, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        if self.config.get('_',None):
            self.SPA = self.config.get('_',None) and self.config['_']('GENERAL', 'spa', False)
            self.emc_user = self.config.get('_',None) and self.config['EMC_User'] or 'root'
            self.emc_pass = self.config.get('_',None) and self.config['EMC_Password'] 
            #self.dic_dev = GetInfoFromSP(self.logger, self.config, self.emc_user, self.emc_pass, self.SPA)
            self.deregister()

    def deregister(self):
        fc_hosts = glob('/sys/class/fc_host/host*') 
        if not fc_hosts:
            raise Exception, 'Can not Get WWN Check why there is no directories under /sys/class/fc_host/'
        for fc_host in fc_hosts:
            f = os.popen('cat %s/node_name' %fc_host)
            f = f.readline().strip('\n')
            hbauid_node = ':'.join([f[2:][i:i+2] for i in range(0,len(f[2:]),2) ])
            f = os.popen('cat %s/port_name' %fc_host)
            f = f.readline().strip('\n')
            hbauid_port = ':'.join([f[2:][i:i+2] for i in range(0,len(f[2:]),2) ])
            self.removeHBA(hbauid_port,hbauid_node)
            self.removeHBA(hbauid_node,hbauid_port)

    def removeHBA(self,hbauid_port,hbauid_node):
        self.logger.error('Running: /opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -Scope\
                               0 port -removeHBA -hbauid %s:%s -o'\
                             %(self.config['SPA'], self.emc_user, self.emc_pass, hbauid_port, hbauid_node))
        if getstatus("/opt/Navisphere/bin/naviseccli  -h %s -user %s -password %s -Scope\
                              0 port -removeHBA -hbauid %s:%s -o"\
                             %(self.config['SPA'], self.emc_user, self.emc_pass, hbauid_port,hbauid_node))[0] != 0:
            self.logger.error('Failed deregister %s:%s' %(hbauid_port,hbauid_node) )
        else:
            self.logger.error('successfully deregister %s:%s' %(hbauid_port,hbauid_node))

class remove_privilege(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(remove_privilege, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)

    def __call__(self):
        if self.config.get('_',None):
            self.SPA = self.config.get('_',None) and self.config['_']('GENERAL', 'spa', False)
            self.emc_user = self.config.get('_',None) and self.config['EMC_User'] or 'root'
            self.emc_pass = self.config.get('_',None) and self.config['EMC_Password'] 
            self.spa_privilage_users = self.GetPrivilege(self.SPA) 
            self.DelPrivilege(self.SPA, self.spa_privilage_users)

    def GetPrivilege(self, SP):
        SP_list = []
        devices = os.popen('/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 remoteconfig -getconfig\
                            -users' %(SP, self.emc_user, self.emc_pass))
        dev = devices.readlines()
        dev = [ i for i in dev if i != '--\n' and i != '--' and i != '\n']
        for P in dev:
            if len(P.split()) > 1: 
                SP_list.append(P.split()[1].strip())   
            else:
                SP_list.append(P.split()[0].strip())
        return SP_list

    def DelPrivilege(self, SP, sp_privilage_users):
        for U in sp_privilage_users:
            self.logger.error("Running: /opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 remoteconfig\
                              -setconfig -rmuser %s -o" %(SP, self.emc_user, self.emc_pass, U))
            status = getstatus("/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 remoteconfig -setconfig\
                               -rmuser %s -o" % (SP, self.emc_user, self.emc_pass, U))
            if status[0] == 0:
                self.logger.error('successfully Remove Privilage for User %s' % U)
            else:
                raise Exception, 'Failed Remove Privilage for User %s' % U    
                



class memory_cache_conf(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(memory_cache_conf, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)

    def __call__(self):
        if self.config.get('_',None):
            self.SPA = self.config.get('_',None) and self.config['_']('GENERAL', 'spa', False)
            self.emc_user = self.config.get('_',None) and self.config['EMC_User'] or 'root'
            self.emc_pass = self.config.get('_',None) and self.config['EMC_Password'] 
            self.mem_read_spa = self.config.get('_',None) and self.config['_']('RUNNER', 'mem_read_spa', False) or '378'
            self.mem_read_spb = self.config.get('_',None) and self.config['_']('RUNNER', 'mem_read_spb', False) or '378'
            self.mem_write =  self.config.get('_',None) and self.config['_']('RUNNER', 'mem_write', False) or '220'
            self.cache_read_spa =  self.config.get('_',None) and self.config['_']('RUNNER', 'cache_read_spa', False) or '1'
            self.cache_read_spb =  self.config.get('_',None) and self.config['_']('RUNNER', 'cache_read_spb', False) or '1'
            self.cache_write =  self.config.get('_',None) and self.config['_']('RUNNER', 'cache_write', False) or '1'
            self.page_size = self.config.get('_',None) and self.config['_']('RUNNER', 'emc_page_size', False) or '8'
            self.low_watermark = self.config.get('_',None) and self.config['_']('RUNNER', 'emc_low_watermark', False) or '60'
            self.high_watermark = self.config.get('_',None) and self.config['_']('RUNNER', 'emc_high_watermark', False) or '80'
            self.SetMemory(self.SPA)
            self.SetPageSize_WaterMark(self.SPA)
            self.SetCache(self.SPA)

    def SetMemory(self, SP):
        self.logger.error('Running: /opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -wsz %s -rsza %s\
                           -rszb %s' %(SP, self.emc_user, self.emc_pass, self.mem_write, self.mem_read_spa, self.mem_read_spb))
        stat = getstatus('/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -wsz %s -rsza %s -rszb %s'\
                  %(SP, self.emc_user, self.emc_pass, self.mem_write, self.mem_read_spa, self.mem_read_spb))
        if stat[0] == 0:
            self.logger.error('successfully configure Memory')
        else:
                raise Exception, 'Failed to onfigure Memory \n %s' % stat[1]
    def SetCache(self, SP):
        self.logger.error('Running: /opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -wc %s -rca %s\
                           -rcb %s' %(SP, self.emc_user, self.emc_pass, self.mem_write, self.mem_read_spa, self.mem_read_spb))
        stat = getstatus('/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -wc %s -rca %s -rcb %s'\
                  %(SP, self.emc_user, self.emc_pass, self.cache_write, self.cache_read_spa, self.cache_read_spb))
        if stat[0] == 0:
            self.logger.error('successfully configure Cache')
        else:
                raise Exception, 'Failed to onfigure Cache \n %s' % stat[1]



    def SetPageSize_WaterMark(self, SP):
        self.logger.error('Running: /opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -p %s -l %s -h %s'                          %(SP, self.emc_user, self.emc_pass, self.page_size, self.low_watermark, self.high_watermark))
                           
        stat = getstatus('/opt/Navisphere/bin/naviseccli -h %s -user %s -password %s -scope 0 setcache -p %s -l %s -h %s'                          %(SP, self.emc_user, self.emc_pass, self.page_size, self.low_watermark, self.high_watermark))
                           
        if stat[0] == 0:
            self.logger.error('successfully configure Page Size and WaterMark')
        else:
                raise Exception, 'Failed to onfigure Page Size and WaterMark\n %s' % stat[1]
