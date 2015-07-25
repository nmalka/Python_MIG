
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#       Date: 18/06/2009                         #
#   ModuleNmae: Pyemc.py         #
##################################

from Pyfiledit import builder, CopyUtils
from Pydecorators import *
import os, time, re ,sys
from commands import getstatusoutput as getstatus
from pdb import set_trace as st

# GolbalVars
navicli = '/opt/Navisphere/bin/navicli'
modprobe = '/sbin/modprobe'

def LvmDev(logger, config):
    lvm = {}
    for Mount in config['Mounts'].split(', '):
        lvm[Mount.split(':',1)[0]] = {Mount.split(':',1)[1].split(':')[0]:Mount.split(':',1)[1].split(':')[1]}
    logger.debug('lvm hash from config file:\n%s' % lvm)
    return lvm


def GetDgName(logger):
    t=[]
    logger.debug("Running: /opt/VRTS/bin/vxdg list|awk {'print $1'}|grep -v NAME")
    Dg = os.popen(" /opt/VRTS/bin/vxdg list|awk {'print $1'}|grep -v NAME")
    dg = Dg.readlines()
    for i in dg:
        t.append( i.strip('\n')) 
    Dg.close()
    return t

def HashDev(logger, config):
    logger.debug('Running: /sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
    devices = os.popen('/sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
    dev = devices.readlines()
    dev = [ i for i in dev if i != '--\n' ]
    tmp=[]
    if config.has_key('MultiCDRC') and config['MultiCDRC'] == '1':
        for x in config['Mounts'].split(', '):
            count = 0
            try:
                Luname=re.search('(.*)(:)(.*:)',x).group(1)
            except:
                logger.error('Missmatch between LUN name in the EMC to Mounts parametter fron the config file')
                raise Exception,  'Missmatch between LUN name in the EMC to Mounts parametter fron the config file'
            for i in dev:
                if re.search('\[%s\]' %Luname ,i) :
                    tmp.append(dev[count -2])
                    tmp.append(dev[count -1])
                    tmp.append(dev[count])
                count = count + 1
        dev=tmp
    logger.debug('powermt:\n%s' % dev)
    devices.close()
    if len(dev)%3 or len(dev) == 0:
        logger.error('Canot get pseudo name from emc.')
        raise Exception,  '%111%'
    lvm = {}
    uniq_lvm=[] 
    for Mount in config['Mounts'].split(', '):
        lvm[Mount.split(':',1)[0]] = {Mount.split(':',1)[1].split(':')[0]:Mount.split(':',1)[1].split(':')[1]+ ' , ' +  Mount.split(':',1)[1].split(':')[2]}
        if re.split(r'[\s\t]*_[0-9]+$',Mount.split(':',1)[0], 1)[0] not in uniq_lvm:
            uniq_lvm.append( re.split(r'[\s\t]*_[0-9]+$',Mount.split(':',1)[0], 1)[0])
    logger.debug('lvm:\n%s' % lvm)
    if not config.has_key('MultiCDRC') or config['MultiCDRC'] == '0':
        if len(dev)/3 != len(uniq_lvm):
            logger.error('Missmatch between Pseudo name in the EMC to Mounts parametter fron the config file')
            raise Exception,  '%112%'
    return dev, lvm, uniq_lvm

def getPseudo(logger,config):
    if not config.has_key('MultiCDRC') or config['MultiCDRC'] == '0':
        logger.debug('/sbin/powermt display dev=all | /bin/grep -i \'Pseudo name\'')
        devices = os.popen('/sbin/powermt display dev=all | /bin/grep -i \'Pseudo name\'')
        pseudo = devices.readlines()
        logger.debug('powermt:\n%s' % pseudo)
        devices.close()
    elif config.has_key('MultiCDRC') and config['MultiCDRC'] == '1':
        tmp=[]
        logger.debug('Running: /sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
        devices = os.popen('/sbin/powermt display dev=all | /bin/grep -A 2 -i \'Pseudo name\'')
        dev = devices.readlines()
        dev = [ i for i in dev if i != '--\n' ]
        for x in config['Mounts'].split(', '):
            try:
                Luname=re.search('(.*)(:)(.*:)',x).group(1)
            except:
                logger.error('Missmatch between LUN name in the EMC to Mounts parametter fron the config file')
                raise Exception,  'Missmatch between LUN name in the EMC to Mounts parametter fron the config file'
            count = 0
            for i in dev:
                if re.search('\[%s\]' %Luname ,i) :
                    tmp.append(dev[count - 2])
                count = count + 1
        pseudo=tmp
    if len(pseudo) == 0:
        logger.error('Canot get pseudo name from emc.')
        raise Exception,  '%111%'
    devs = []
    while len(pseudo)>0:
        dev = pseudo.pop(0)[:-1]
        p = re.search('pseudo name=(emcpower\w)', dev, re.I).group(1)
        devs.append('/dev/' + p)
    num = len(devs)
    logger.debug('devs list:\n%s' % devs)
    return num, (' ').join(devs)

def mountCheck(logger, lvm):
    paths = []
    logger.info('Starting to check that there are no mounted directories')
    for key, hash in lvm.iteritems():
        paths.append(hash.items()[0][1])
    for path in paths:
        if os.path.ismount(path):
            logger.error('Directory \'%s\' is allready mounted' % path)
            raise Exception, '%120%'

def umountCheck(logger, lvm):
    paths = []
    logger.info('Starting to check that all directories are mounted')
    for key, hash in lvm.iteritems():
        paths.append(hash.items()[0][1])
    for path in paths:
        if not os.path.ismount(path):
            logger.error('Directory \'%s\' is not mounted' % path)
            raise Exception, '%121%'
def navi(cmd, log=''):
    navi = '/etc/init.d/naviagent %s %s' %(cmd, log)
    if os.system(navi) != 0:
        return False
    return True

def powerPath(cmd, log=''):
    powerPath = '/etc/init.d/PowerPath %s %s' % (cmd, log)
    if os.system(powerPath) != 0:
        return False
    return True

def reloadHBA(hba, log=''):
    time.sleep(5)
    if os.system('%s -v -r %s %s' % (modprobe, hba, log)) != 0:
        return False
    time.sleep(10)
    if os.system('%s -v -i %s %s' % (modprobe, hba, log)) != 0:
        return False
    time.sleep(5)
    return True

class agentconfig(builder):
    def __call__(self, *args, **kwargs):
        self.logger.error('Testing the FCS Zoning on the server...')
        self.logger.info('running: cat /proc/scsi/scsi | grep \'Vendor: DGC\'')
        if os.system('/bin/cat /proc/scsi/scsi | /bin/grep \'Vendor: DGC\' %s' % self.log) != 0:
            self.logger.error('Problem with the fiber connection, Server can NOT see the EMC storage')
            self.logger.error('Check the Zoning on the FCS reboot the server and then rerun the script')
            raise Exception, '%131%'
        self.lvm = LvmDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
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
        if not navi('stop', log=self.log):
            self.logger.error('Canot stop navi')
            raise Exception, '%124%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('stop', log=self.log):
            self.logger.error('Can not stop Powerpath')
            raise Exception, '%125%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Realoding fiber %s driver' % self.config['HBA'])
        if not reloadHBA(hba=self.config['HBA'], log=self.log):
            self.logger.error('Faild to reload fiber %s driver' % self.config['HBA'])
            self.logger.error('Before rerunning the script make sure the \'%s\' driver is loaded' % self.config['HBA'])
            raise Exception, '%128%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('start', log=self.log):
            self.logger.error('Canot start Powerpath')
            raise Exception, '%125%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not navi('start', log=self.log):
            self.logger.error('Canot start navi')
            raise Exception, '%124%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Assigning the %s to \'%s\'' % (os.environ['HOSTNAME'], self.config['SG']))
        self.logger.info('Running: %s -h %s storagegroup -connecthost -o -host %s -gname %s' % \
                        (navicli, self.config['SPA'], os.environ['HOSTNAME'], self.config['SG']))
        if os.system('%s -h %s storagegroup -connecthost -o -host %s -gname %s %s' % \
                    (navicli, self.config['SPA'], os.environ['HOSTNAME'], self.config['SG'], self.log)) != 0:
            self.logger.error('Failed to assign %s to %s' % (os.environ['HOSTNAME'], self.config['SG']))
            raise Exception, '%124%'
        self.logger.error('Sleeping for 20 sec')
        time.sleep(20)
        if not navi('stop', log=self.log):
            self.logger.error('Can not stop navi')
            raise Exception, '%124%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('stop', log=self.log):
            self.logger.error('Can not stop Powerpath')
            raise Exception, '%125%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('Realoding fiber %s driver' % self.config['HBA'])
        if not reloadHBA(hba=self.config['HBA'], log=self.log):
            self.logger.error('Faild to reload fiber %s driver' % self.config['HBA'])
            self.logger.error('Before rerunning the script make sure the \'%s\' driver is loaded' % self.config['HBA'])
            raise Exception, '%128%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not powerPath('start', log=self.log):
            self.logger.error('Canot start Powerpath')
            raise Exception, '%125%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        if not navi('start', log=self.log):
            self.logger.error('Canot start navi')
            raise Exception, '%124%'
        self.logger.error('Sleeping for 5 sec')
        time.sleep(5)
        self.logger.error('%s successfully assigned to %s' % (os.environ['HOSTNAME'], self.config['SG']))

class vx_disk_init(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_disk_init, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self.Fvx_disk_init()
    def Fvx_disk_init(self):
        self.logger.error('Veritas disk Init')
        pseudoNum, pseudo = getPseudo(logger=self.logger,config=self.config)
        if pseudoNum != 0:
            pseudo=pseudo.replace('/dev/', ' ')
            for Pseudo in pseudo.split():
                self.logger.error('Running: vxdisksetup -i %s' % Pseudo)
                if getstatus('/opt/VRTS/bin/vxdisksetup -i %s %s' % (Pseudo, self.log))[0] != 0:
                    self.logger.error('Faild to run: \'vxdisksetup -i %s\'' % Pseudo)
                    raise Exception,  '%113%'
                self.logger.error('successfully: vxdisksetup -i %s' % Pseudo)


class vx_disk_uninit(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_disk_uninit, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self.Fvx_disk_uninit()

    def  Fvx_disk_uninit(self):
        self.logger.error('Veritas disk Unsetup')
        pseudoNum, pseudo = getPseudo(logger=self.logger,config=self.config)
        if pseudoNum != 0:
            pseudo=pseudo.replace('/dev/', ' ')
            for Pseudo in pseudo.split():
                self.logger.error('Running: vxdiskunsetup -C %s' % Pseudo)
                if getstatus('/opt/VRTS/bin/vxdiskunsetup -C %s %s' % (Pseudo, self.log))[0] != 0:
                    self.logger.error('Faild to run: \'vxdiskunsetup -C %s\'' % Pseudo)
                    raise Exception,  '%113%'
                self.logger.error('successfully: vxdiskunsetup -C %s' % Pseudo)


class vx_vg_create(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_vg_create, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self.Fvx_vg_create(lvm=self.lvm, uniq_lvm=self.uniq_lvm)

    def Fvx_vg_create(self, lvm, uniq_lvm):
        if len(uniq_lvm) == len(self.dev)/3:
            tmp = []
            while len(self.dev)>0:
                pseudoName = self.dev.pop(0)[:-1]
                pseudoName = re.search('pseudo name=(emcpower\w)', pseudoName, re.I).group(1)
                lunName = self.dev.pop(0)[:-1]
                lunName = self.dev.pop(0)[:-1]
                lunName = re.search('Logical device ID=.*\[(.*?)\]', lunName, re.I).group(1)
                if lunName in tmp:
                    break
                if lunName not in lvm.keys():
                    for k in lvm.keys():
                        if k.startswith(lunName):
                            lunName=k
                            tmp.append(lunName)

                if self.config['Share_FS'].upper() == 'YES':
                    share = '-s'
                else:
                    share = ' '

                for k,v in lvm[lunName].iteritems():
                    self.logger.error('Running: vxdg %s init  %s %s' % (share, v.split(',')[1], pseudoName))
                    if getstatus('/opt/VRTS/bin/vxdg %s init  %s %s %s' % (share, v.split(',')[1], pseudoName,  self.log))[0] != 0:
                        self.logger.error('Faild to run: \'/opt/VRTS/bin/vxdg %s init  %s %s\'' % (share, v.split(',')[1], pseudoName))
                        self.logger.error('Try to add the disk %s to %s group' %(pseudoName, v.split(',')[1]))
                        if getstatus('/opt/VRTS/bin/vxdg -g %s adddisk %s %s' %( v.split(',')[1], pseudoName,  self.log))[0] != 0:
                            self.logger.error('Faild to run: \'/opt/VRTS/bin/vxdg -g %s adddisk %s %s\'' %( v.split(',')[1], pseudoName,  self.log))
                            raise Exception,  '%113%'
                        else:
                            self.logger.error('successfully: vxdg -g %s adddisk %s' % (v.split(',')[1], pseudoName))
                    else:
                        self.logger.error('successfully: vxdg init share %s %s' % (v.split(',')[1], pseudoName))


class vx_vg_destroy(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_vg_destroy, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self.Fvx_vg_destroy()
                    
    def Fvx_vg_destroy(self):
                DG=GetDgName(self.logger)
                for dg in DG:
                    self.logger.error('Running: vxdg destroy  %s ' % (dg))
                    if getstatus('/opt/VRTS/bin/vxdg destroy  %s  %s' % (dg,  self.log))[0] != 0:
                        self.logger.error('Faild to run: \'/opt/VRTS/bin/vxdg destroy %s \'' % (dg))
                        raise Exception,  '%113%'
                    else:
                        self.logger.error('successfully: vxdg destroy  %s' % (dg))



class vx_volume_create(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_volume_create, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self.NonStandartVol=self.GetNonStandartVol(self.lvm)
        self.Fvx_volume_create1( self.NonStandartVol)
        self.Fvx_volume_create2(self.lvm, self.NonStandartVol)


    def GetNonStandartVol(self, lvm):
        FirstDo={}
        for k,hash in lvm.iteritems():
            if self.config.has_key(k):
                FirstDo[k]={hash.keys()[0]:hash.values()[0]} 
        return FirstDo 

    def Fvx_volume_create1(self,lvm):
        for k,hash in lvm.iteritems():
            String = '' 
            for Str in self.config[k].split(':'):
                String = String + ' ' + Str
            if not re.search('NONE_[0-9]+' ,hash.keys()[0]) :
                self.logger.error('Running: vxassist -g %s make %s %s' % (hash.values()[0].split(',')[1], hash.keys()[0], String))
                if getstatus('/opt/VRTS/bin/vxassist -g %s make %s %s %s' % (hash.values()[0].split(',')[1], hash.keys()[0], String, self.log))[0] != 0:
                    self.logger.error('Faild to run: \'/opt/VRTS/bin/vxassist -g %s make %s\'' % (hash.values()[0].split(',')[1], hash.keys()[0], String))
                    raise Exception,  '%113%'
           
    def Fvx_volume_create2(self,lvm,NonStandartVol={}): 
        for k,hash in lvm.iteritems():
            if not NonStandartVol.has_key(k):
                if not re.search('NONE_[0-9]+' ,hash.keys()[0]) :
                    Size = getstatus('/opt/VRTS/bin/vxassist -g  %s maxsize layout=concat' %(hash.values()[0].split(',')[1]))[1].split(':')[1].split()[0]
                    self.logger.error('Running: vxassist -g %s make %s %s' % (hash.values()[0].split(',')[1], hash.keys()[0], Size))
                    if getstatus('/opt/VRTS/bin/vxassist -g %s make %s %s %s' % (hash.values()[0].split(',')[1], hash.keys()[0], Size, self.log))[0] != 0:
                        self.logger.error('Faild to run: \'/opt/VRTS/bin/vxassist -g %s make %s %s\'' % (hash.values()[0].split(',')[1], hash.keys()[0], Size))
                        raise Exception,  '%113%'



class vx_mkfs(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_mkfs, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self. Fvx_mkfs(self.lvm)


    def Fvx_mkfs(self, lvm):
        for k,hash in lvm.iteritems():
            if not re.search('NONE_[0-9]+' ,hash.keys()[0]) :
                self.logger.error('Running: /opt/VRTS/bin/mkfs -t vxfs /dev/vx/rdsk/%s/%s' %(hash.values()[0].split(',')[1].strip(), hash.keys()[0].strip()))
                if getstatus('/opt/VRTS/bin/mkfs -t vxfs /dev/vx/rdsk/%s/%s %s' %(hash.values()[0].split(',')[1].strip(), hash.keys()[0].strip(), self.log))[0] != 0:
                    self.logger.error('Faild to run: \'/opt/VRTS/bin/mkfs -t vxfs /dev/vx/rdsk/%s/%s\'' %(hash.values()[0].split(',')[1].strip(), hash.keys()[0].strip()))
                    raise Exception,  '%113%' 



class vxdg_import(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vxdg_import, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self. Fvxdg_import(self.lvm)


    def Fvxdg_import(self, lvm):
        for k,hash in lvm.iteritems():
            self.logger.error('Checking if %s need to import' %( hash.values()[0].split(',')[1].strip()))
            self.logger.error('Running: /opt/VRTS/bin/vxdg list  %s' %( hash.values()[0].split(',')[1].strip()))
            if getstatus('/opt/VRTS/bin/vxdg list  %s' %( hash.values()[0].split(',')[1].strip()))[0] != 0:
                self.logger.error('Running: /opt/VRTS/bin/vxdg import %s' %( hash.values()[0].split(',')[1].strip()))
                if getstatus(' /opt/VRTS/bin/vxdg import %s %s' %( hash.values()[0].split(',')[1].strip(), self.log))[0] != 0:
                    self.logger.error('Faild to run: \'/opt/VRTS/bin/vxdg import %s' %( hash.values()[0].split(',')[1].strip()))
                    raise Exception,  '%113%'



class vxdg_deport(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vxdg_deport, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self. Fvxdg_deport(self.lvm)


    def Fvxdg_deport(self, lvm):
        for k,hash in lvm.iteritems():
            self.logger.error('Checking if %s need to deport' %( hash.values()[0].split(',')[1].strip()))
            self.logger.error('Running: /opt/VRTS/bin/vxdg list  %s' %( hash.values()[0].split(',')[1].strip()))
            if getstatus('/opt/VRTS/bin/vxdg list  %s' %( hash.values()[0].split(',')[1].strip()))[0] == 0:
                self.logger.error('Running: /opt/VRTS/bin/vxdg deport %s' %( hash.values()[0].split(',')[1].strip()))
                if getstatus(' /opt/VRTS/bin/vxdg deport %s %s' %( hash.values()[0].split(',')[1].strip(), self.log))[0] != 0:
                    self.logger.error('Faild to run: \'/opt/VRTS/bin/vxdg deport %s' %( hash.values()[0].split(',')[1].strip()))
                    raise Exception,  '%113%'






class vx_mount(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(vx_mount, self).__init__(config=config, componentID=componentID, loggerName=loggerName, \
                *args, **kwargs)
        self.dev, self.lvm, self.uniq_lvm = HashDev(self.logger, self.config)
        mountCheck(logger=self.logger, lvm=self.lvm)
    def __call__(self, *args, **kwargs):
        self. Fvx_mount(self.lvm)


    def Fvx_mount(self, lvm):
        if self.config['Share_FS'].upper() == 'YES':
            share = '-t vxfs -o cluster' 
        else:
            share = '-t vxfs'

        for k,hash in lvm.iteritems():
            self.logger.error('Running: /opt/VRTS/bin/mount %s /dev/vx/dsk/%s/%s  %s' %(share, hash.values()[0].split(',')[1].strip(), hash.keys()[0].strip(),\
                              hash.values()[0].split(',')[0].strip()))
            if getstatus('/opt/VRTS/bin/mount %s /dev/vx/dsk/%s/%s  %s %s' %(share, hash.values()[0].split(',')[1].strip(), hash.keys()[0].strip(),\
                         hash.values()[0].split(',')[0].strip(), self.log))[0] != 0:
                if getstatus('/opt/VRTS/bin/df %s' %( hash.values()[0].split(',')[0].strip()))[0] != 0:
                    self.logger.error('Faild to run: \'/opt/VRTS/bin/mount %s /dev/vx/dsk/%s/%s  %s\'' %(share, hash.values()[0].split(',')[1].strip(),\
                                      hash.keys()[0].strip(), hash.values()[0].split(',')[0].strip()))
                    raise Exception,  '%113%'




