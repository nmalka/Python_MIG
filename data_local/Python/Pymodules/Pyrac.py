
####################################
#   By: Yaron Cohen                #
#   Mail: yaron.cohen@comverse.com #
#   Ver: 4.8                       #
#   Date: 23/09/09                 #
#   ModuleNmae: Pydb.py            #
####################################

import os
import sys, string, datetime
import re
from Pymodule import *
from Pyfiledit import builder
from Pyfiledit import filesToBakup
import pwd
from Pyfunc import *
from Pyconf import HashParser
from commands import getstatusoutput as getstatus
import time
import logging
import shutil

def CheckStatus(status, stage='', Failed='', Other='', loggerName=''):
    logger = logging.getLogger(loggerName)
    logger.debug(': %s ' %status[1])
    if status[0] is 0:
        logger.error("%s %s" %(stage, Other))
    else:
        logger.error("Failed: %s %s" %(Failed, Other))
        raise Exception, 'Error: %s'% status[1] 

def CheckLog(Log, Line, Count=None, Stop=None ,rsh='', other='', Add=''):
    status=getstatus('%s %s grep %s %s %s' %(rsh, other, Line, Log, Add))
    if status[0] is 0: 
        Flag=1
    else:
        if Count and Stop:
            Count=Count+1
            if Count > int(Stop):
                Flag=2
            else:
                Flag=0
        else:
            Flag=2
    return Count,Flag



def RacStop(GridHome, ssh='', server='', loggerName='', Stage=None):
    logger = logging.getLogger(loggerName)
    if server:
        Ser = server
    else:
        Ser = os.environ['HOSTNAME']
    if Stage:
        if Stage == 'StopOnly':
            status=getstatus("%s %s %s/bin/crsctl stop crs" %(ssh, server, GridHome))
            logger.error('Stopping the RAC cluster on %s server' %Ser)
        elif Stage == 'MonOnly':
            status=getstatus("%s %s %s/bin/crsctl status server %s|grep -v STATE=ONLINE" %(ssh, server, GridHome, Ser))
            CheckStatus(status=status, stage='RAC Cluster is offline on %s server' % Ser)
        else:
            logger.error("Failed: Unrecognize Stage = %s" %(Stage))
            raise Exception, 'Error: %s'% status[1]
    else:
        status=getstatus("%s %s %s/bin/crsctl stop crs" %(ssh, server, GridHome))
        logger.error('Stopping the RAC cluster on %s server' %Ser)
        status=getstatus("%s %s %s/bin/crsctl status server %s|grep -v STATE=ONLINE" %(ssh, server, GridHome, Ser))
        CheckStatus(status=status, stage='RAC Cluster is offline on %s server' % Ser)

      


def RacStart(GridHome, ssh='', server='', Stage=None):
    if server:
        Ser = server
    else:
        Ser = os.environ['HOSTNAME']
    if Stage:
        if Stage == 'StartOnly':
            status=getstatus("%s %s %s/bin/crsctl start crs" %(ssh, server, GridHome))
            CheckStatus(status=status, stage='Starting the RAC cluster on %s server' %Ser)
        elif Stage == 'MonOnly':
            status=getstatus("%s %s %s/bin/crsctl status server %s|grep STATE=ONLINE" %(ssh, server, GridHome, Ser))
            CheckStatus(status=status, stage='To Start RAC Cluster on %s server' % Ser)
    else:
        status=getstatus("%s %s %s/bin/crsctl start crs" %(ssh, server, GridHome))
        CheckStatus(status=status, stage='Starting the RAC cluster on %s server' %Ser)
        time.sleep(120)
        status=getstatus("%s %s %s/bin/crsctl status server %s|grep STATE=ONLINE" %(ssh, server, GridHome, Ser))
        CheckStatus(status=status, stage='To Start RAC Cluster on %s server' % Ser)



class runcluvfy(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.OtherHosts =''
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts = self.OtherHosts + other.split(':')[0].strip() + ','
        self.OtherHosts = self.OtherHosts[:-1]
        self.stop = self.config['GridStop']
        self.SWLocation = self.config['SWLocation']
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OcrVote = self.config['OcrVote']
        self.log = ' > /home/oracle/adminscripts.log 2>&1'

    def __call__(self):
        self.Fruncluvfy()


    
    def Fruncluvfy(self):
        for ov in self.OcrVote.split(','):
            os.chown('%s' % ov, 1000, 1000)
        status=getstatus('su -c "%s/grid/runcluvfy.sh stage -pre crsinst -n %s -r 11gR2 -verbose %s" oracle ' \
        %(self.SWLocation, self.OtherHosts, self.log))
        CheckStatus(status=status, stage='Pre Installation Finish Succesfully', Failed= 'Check lof file %s' % self.log)

class gridinstall(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        os.chmod(self.config['LogFile'],0666)
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.stop = self.config['GridStop']
        self.SWLocation = self.config['SWLocation']
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome'] 
        self.log = ' > /dev/null 2>&1'

    def __call__(self):
        self.FGridInstall()





     

    def FGridInstall(self):
        Flag = 0
        Counter = 1
        InstallatinStart = None
        self.logger.error('Oracle RAC installation Start')
        status=getstatus('su -c  "%s/grid/runInstaller -silent -responseFile %s/grid.rsp %s" oracle' \
               %(self.SWLocation, self.SWLocation, self.log))
        CheckStatus(status=status, stage='Grid Infrastracture Installation') 
        while Flag == 0 : 
            time.sleep(60)
            Log=getstatus("ls -tr %s/logs/oraInstall*.out "  %(self.Inventory,))
            if Log[0] is 0 and InstallatinStart:
                Counter = 1
                InstallatinStart = None
            if Log[0] is 0:
                Log=getstatus("ls -tr %s/logs/oraInstall*.out|tail -1 " %(self.Inventory))
                self.logger.debug('Logger Name %s' %Log[1])
                self.logger.debug('Try %s of %s' %(Counter, self.stop))
                Counter,Flag = CheckLog(Log=Log[1], Line='"Successfully Setup Software."', Count=Counter, Stop=self.stop)
                if Flag != 0:
                    if Flag == 1:
                        status=getstatus('mkdir -p %s/logs/Temp/ %s' %(self.Inventory, self.log))
                        CheckStatus(status=status, stage='Create Temp Directory in Inventory Path')
                        status=getstatus('mv -f %s/logs/*.out %s/logs/Temp/ %s' %(self.Inventory,self.Inventory, self.log))
                        CheckStatus(status=status, stage='Moving *.out file to Temp directory')
                        self.logger.error("Successfully: Grid Infrastracture Installation")
                    elif Flag == 2:
                        self.logger.error("Failed: Grid Infrastracture Installation, Check the Logs in /u01/oraInventory/logs/")
                        raise Exception, 'Failed: Grid Infrastracture Installation, Check the Logs in /u01/oraInventory/logs/'
            else:
                Counter = Counter + 5
                InstallatinStart = 'Yes'
                self.logger.debug('Checking if the installation Start')
                self.logger.debug('Try %s of %s' %(Counter/5, int(self.stop)/5))
                if Counter > int(self.stop):
                     self.logger.error("Failed: Grid Infrastracture Installation, Check the Logs in /tmp/")
                     raise Exception, 'Failed: Grid Infrastracture Installation, Check the Logs in /tmp/'
                


class gridscripts(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):

        self.LocalGridscripts()
        self.OtherGridscripts()



    def LocalGridscripts(self):
        #Counter=0
        self.logger.error('Running: %s/orainstRoot.sh' %(self.Inventory))
        status=getstatus('%s/orainstRoot.sh' %(self.Inventory))
        CheckStatus(status=status, stage='orainstRoot.sh')
        self.logger.error('Successfully: %s/orainstRoot.sh' %(self.Inventory))
        self.logger.error('Running: %s/root.sh' %(self.GridHome)) 
        status=getstatus('%s/root.sh' %(self.GridHome))
        self.logger.error('Successfully: %s/root.sh' %(self.GridHome)) 
        Log=getstatus("ls -tr %s/install/root_%s*.log "%(self.GridHome, os.environ['HOSTNAME']))
        if Log[0] is 0:
            Log=getstatus("ls -tr %s/install/root_%s*.log |tail -1" %(self.GridHome, os.environ['HOSTNAME']))
            Counter,Flag = CheckLog(Log=Log[1], Line='"Configure Oracle Grid Infrastructure for a Cluster ... succeeded"')
            if Flag != 0:
                if Flag == 1:
                    self.logger.error("Successfully: Finish Grid scripts on the local server") 
                elif Flag == 2:
                    self.logger.error("Failed: Grid Infrastracture Installation")
                    raise Exception, 'Failed: Grid Infrastracture Installation'
        else:
            self.logger.error("Failed: RAC GRID scripts on %s server" % os.environ['HOSTNAME'])
            self.logger.error("Failed: The Status is Unknown the log file didnt exist" % os.environ['HOSTNAME'])
            raise Exception, 'Failed: RAC GRID scripts'
        
    def OtherGridscripts(self):
        #Counter=0
        for other in self.OtherHosts:
            self.logger.error('Running: ssh %s  %s/orainstRoot.sh' %(other, self.Inventory))
            status=getstatus('ssh %s %s/orainstRoot.sh' %(other, self.Inventory))
            CheckStatus(status=status, stage='orainstRoot.sh')
            self.logger.error('Successfully: ssh %s  %s/orainstRoot.sh' %(other, self.Inventory))
            self.logger.error('Running: ssh %s  %s/root.sh' %(other, self.GridHome))
            status=getstatus('ssh %s %s/root.sh' %(other, self.GridHome))
            self.logger.error('Successfully: ssh %s  %s/root.sh' %(other, self.GridHome))

            Log=getstatus("ssh %s ls -tr %s/install/root_%s*.log " %(other, self.GridHome, other))
            if Log[0] is 0:
                Log=getstatus("ssh %s ls -tr %s/install/root_%s*.log |tail -1 " %(other, self.GridHome, other))
                Counter,Flag = CheckLog(Log=Log[1], Line='"succeeded"',\
                          rsh='ssh', other=other, Add='|grep Infrastructure|grep Configure')  
                if Flag != 0:
                    if Flag == 1:
                        self.logger.error("Successfully: Finish Grid scripts on the local server")
                    elif Flag == 2:
                        self.logger.error("Failed: Grid Infrastracture Installation")
                        raise Exception, 'Failed: Grid Infrastracture Installation'

            else:
                self.logger.error("Failed: RAC GRID scripts on %s server" % other)
                self.logger.error("Failed: The Status is Unknown the log file didnt exist" % other)
                raise Exception, 'Failed: RAC GRID scripts'



class dbinstall(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.stop = self.config['DBStop']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
  
        self.CheckRACStatus()
        self.DBinstall()



    def CheckRACStatus(self):
        status=getstatus("%s/bin/crsctl status server %s|grep STATE=ONLINE" %(self.GridHome, os.environ['HOSTNAME']))
        CheckStatus(status=status, stage='RAC Cluster on %s server is online' % os.environ['HOSTNAME'])
        for other in self.OtherHosts:
            status=getstatus("%s/bin/crsctl status server %s|grep STATE=ONLINE" %(self.GridHome, other))
            CheckStatus(status=status, stage='RAC Cluster on %s server is online' % other)
    
    def DBinstall(self):
        Flag=0
        Counter=1
        InstallatinStart = None
        self.logger.error("Starting to Install DB ORACLE")
        status=getstatus('su -c "%s/database/runInstaller -silent -responseFile %s/db.rsp %s" oracle' \
               %(self.SWLocation, self.SWLocation, self.log))
        CheckStatus(status=status, stage='Starting to install RAC DB')
        while Flag == 0 :
            time.sleep(60)
            Log=getstatus("ls -tr %s/logs/oraInstall*.out " %(self.Inventory))
            if Log[0] is 0 and InstallatinStart:
                Counter = 1
                InstallatinStart = None
            if Log[0] is 0:
                Log=getstatus("ls -tr %s/logs/oraInstall*.out|tail -1 " %(self.Inventory))
                self.logger.debug('Logger Name %s' %Log[1])
                if Log[0] is 0:
                    Counter,Flag = CheckLog(Log=Log[1], Line='"Successfully Setup Software."', Count=Counter, Stop=self.stop)
                    self.logger.debug('Try %s of %s' %(Counter, self.stop))
                    if Flag != 0:
                        if Flag == 1:
                            status=getstatus('mv -f %s/logs/Temp/*.out %s/logs/ %s' %(self.Inventory,self.Inventory, self.log))
                            CheckStatus(status=status, stage='Moving *.out file from %s/logs/Temp/ directory' % self.Inventory)
                            status=getstatus('rm -rf %s/logs/Temp/ %s' %(self.Inventory, self.log))
                            CheckStatus(status=status, stage='Remove Temp Directory from %s/logs/' % self.Inventory)
                            self.logger.error("Successfully: RAC DB Installation")
                        elif Flag == 2:
                            self.logger.error("Failed: RAC DB Installation, Check the Logs in /u01/oraInventory/logs/")
                            raise Exception, 'Failed: RAC DB Installation , Check the Logs in /u01/oraInventory/logs/'
            else:
                Counter = Counter + 5  
                InstallatinStart = 'Yes'          
                self.logger.debug('Try %s of %s' %(Counter/5, int(self.stop)/5))
                if Counter > int(self.stop):
                     self.logger.error("Failed: RAC DB Installation, Check the Logs in /tmp/")
                     raise Exception, 'Failed: RAC DB Installation , Check the Logs in /tmp'

    

class dbscripts(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        self.LocalDBscripts()
        self.OtherDBscripts()


    def LocalDBscripts(self):
        self.logger.debug('Runnig %s/root.sh on %s' %(self.OracleHome, os.environ['HOSTNAME']))
        status=getstatus('%s/root.sh %s' %(self.OracleHome, self.log))
        Log=getstatus("ls -tr %s/install/root_%s*.log "  %(self.OracleHome, os.environ['HOSTNAME']))
        if Log[0] is 0:
            Log=getstatus("ls -tr %s/install/root_%s*.log |tail -1 " %(self.OracleHome, os.environ['HOSTNAME']))
            Counter,Flag = CheckLog(Log=Log[1], Line='"Finished product-specific root actions."')
            if Flag != 0:
                if Flag == 1:
                    self.logger.error("Successfully: Finish RAC DB scripts on %s server" % os.environ['HOSTNAME'])
                elif Flag == 2:
                    self.logger.error("Failed: RAC DB scripts on %s server" % os.environ['HOSTNAME'])
                    raise Exception, 'Failed: RAC DB scripts'
        else:
            self.logger.error("Failed: RAC DB scripts on %s server" % os.environ['HOSTNAME'])
            raise Exception, 'Failed: RAC DB scripts'



    def OtherDBscripts(self):
        for other in self.OtherHosts:
            status=getstatus('ssh %s %s/root.sh %s' %(other, self.OracleHome, self.log))
            Log=getstatus("ssh %s ls -tr %s/install/root_%s*.log" %(other, self.OracleHome, other))
            if Log[0] is 0:
                Log=getstatus("ssh %s ls -tr %s/install/root_%s*.log |tail -1" %(other, self.OracleHome, other))
                Counter,Flag = CheckLog(Log=Log[1], Line='"Finished"',\
                          rsh='ssh', other=other, Add='| grep "product-specific"')
                if Flag != 0:
                    if Flag == 1:
                        self.logger.error("Successfully: Finish RAC DB scripts on %s server" % other)
                    elif Flag == 2:
                        self.logger.error("Failed: RAC DB scripts on %s server" % other)
                        raise Exception, 'Failed: RAC DB scripts'

            else:
                self.logger.error("Failed: RAC DB scripts on %s server" % other)
                self.logger.error("Failed: The Status is Unknown the log file didnt exist" )
                raise Exception, 'Failed: RAC DB scripts'



class opatch(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        self.StopHome()
        self.InstallOpatch()
        self.ChangePer()
        self.StartHome()


    def StopHome(self):
        self.logger.error('Running: %s/bin/srvctl stop home -o %s -s %s/Grid_%s.stat -n %s' \
                         %(self.GridHome, self.GridHome, self.SWLocation, os.environ['HOSTNAME'],os.environ['HOSTNAME']))
        status=getstatus('%s/bin/srvctl stop home -o %s -s %s/Grid_%s.stat -n %s' \
                        %(self.GridHome, self.GridHome, self.SWLocation, os.environ['HOSTNAME'],os.environ['HOSTNAME']))
        CheckStatus(status=status, stage='Succesfully finish command on %s' % os.environ['HOSTNAME'])
        for other in self.OtherHosts:
            self.logger.error('Running: ssh %s %s/bin/srvctl stop home -o %s -s %s/Grid_%s.stat -n %s' \
                             %(other, self.GridHome, self.GridHome, self.SWLocation, other,other))
            status=getstatus('ssh %s %s/bin/srvctl stop home -o %s -s %s/Grid_%s.stat -n %s' \
                            %(other, self.GridHome, self.GridHome, self.SWLocation, other,other))
            CheckStatus(status=status, stage='Succesfully finish command on %s' % other)

    def InstallOpatch(self):
        self.logger.error('Running: %s/crs/install/rootcrs.pl -unlock' % self.GridHome)
        status=getstatus('%s/crs/install/rootcrs.pl -unlock' % self.GridHome)
        CheckStatus(status=status, stage='Succesfully: %s/crs/install/rootcrs.pl -unlock' % self.GridHome)
        self.logger.error('Running: %s/8649805/custom/scripts/prepatch.sh -dbhome %s'% (self.SWLocation, self.GridHome))
        status=getstatus('%s/8649805/custom/scripts/prepatch.sh -dbhome %s' % (self.SWLocation, self.GridHome)) 
        CheckStatus(status=status, stage='Succesfully: %s/8649805/custom/scripts/prepatch.sh -dbhome %s' \
                    % (self.SWLocation, self.GridHome))

        os.chdir('/')
        self.logger.error('Running:su -c "%s/OPatch/opatch napply -local -silent -oh %s -id %s/8649805" oracle' \
                         %(self.OracleHome, self.GridHome, self.SWLocation))
        status=getstatus('su -c "%s/OPatch/opatch napply -local -silent -oh %s -id %s/8649805" oracle' \
                         %(self.OracleHome, self.GridHome, self.SWLocation))
        CheckStatus(status=status, stage='Succesfully finish command on %s' % os.environ['HOSTNAME'])

        for other in self.OtherHosts:
            self.logger.error('Running:ssh %s %s/crs/install/rootcrs.pl -unlock' % (other, self.GridHome))
            status=getstatus('ssh %s %s/crs/install/rootcrs.pl -unlock' % (other, self.GridHome))
            CheckStatus(status=status, stage='Succesfully: %s/crs/install/rootcrs.pl -unlock' % self.GridHome) 
            self.logger.error('Running:ssh %s %s/8649805/custom/scripts/prepatch.sh -dbhome %s'\
                           % (other, self.SWLocation, self.GridHome))
            status=getstatus('ssh %s %s/8649805/custom/scripts/prepatch.sh -dbhome %s' % (other, self.SWLocation, self.GridHome)) 
            CheckStatus(status=status, stage='Succesfully: %s/8649805/custom/scripts/prepatch.sh -dbhome %s on %s' \
                              % (self.SWLocation, self.GridHome, other))
            self.logger.error('Running:ssh %s su -c "cd / ; %s/OPatch/opatch napply -local -silent -oh %s -id %s/8649805" oracle'\
                              %(other, self.OracleHome, self.GridHome, self.SWLocation))
            status=getstatus('ssh %s \'su oracle -c "cd /;%s/OPatch/opatch napply -local -silent -oh %s -id %s/8649805" \'' \
                              %(other, self.OracleHome, self.GridHome, self.SWLocation))
            CheckStatus(status=status, stage='Succesfully finish command on %s' % other)


    def ChangePer(self):
        self.logger.error("going to change permission to %s/log/%s/agent" % (self.GridHome.strip("'"), os.environ['HOSTNAME']))
        os.chmod('%s/log/%s/agent'% (self.GridHome.strip("'"), os.environ['HOSTNAME']),0775)
        self.logger.error("going to change permission to %s/log/%s/agent/crsd" % (self.GridHome.strip("'"), os.environ['HOSTNAME'])) 
        os.chmod('%s/log/%s/agent/crsd' % (self.GridHome.strip("'"), os.environ['HOSTNAME']),0775)
        self.logger.error('Running: %s/8649805/custom/scripts/postpatch.sh -dbhome %s'% (self.SWLocation, self.GridHome))
        status=getstatus('%s/8649805/custom/scripts/postpatch.sh -dbhome %s' % (self.SWLocation, self.GridHome)) 
        CheckStatus(status=status, stage='Succesfully: %s/8649805/custom/scripts/postpatch.sh -dbhome %s' \
                   % (self.SWLocation, self.GridHome))

        
        for other in self.OtherHosts:
            self.logger.error("going to change permission to %s/log/%s/agent" % (self.GridHome.strip("'"), other))
            status=getstatus('ssh %s chmod 755 %s/log/%s/agent' %(other, self.GridHome.strip("'"), other))
            CheckStatus(status=status)
            self.logger.error("going to change permission to %s/log/%s/agent/crsd" % (self.GridHome.strip("'"), other))
            status=getstatus('ssh %s chmod 755 %s/log/%s/agent/crsd' %(other, self.GridHome.strip("'"), other))
            CheckStatus(status=status, stage='Successfully: Change permission')

            self.logger.error('Running:ssh %s %s/8649805/custom/scripts/postpatch.sh -dbhome %s'\
                             % (other, self.SWLocation, self.GridHome))
            status=getstatus('ssh %s %s/8649805/custom/scripts/postpatch.sh -dbhome %s' % (other, self.SWLocation, self.GridHome)) 
            CheckStatus(status=status, stage='Succesfully: %s/8649805/custom/scripts/postpatch.sh -dbhome %s on %s' \
                              % (self.SWLocation, self.GridHome, other))



    def StartHome(self):
        self.logger.error('Running: %s/crs/install/rootcrs.pl -patch' % self.GridHome)
        status=getstatus('%s/crs/install/rootcrs.pl -patch' % self.GridHome)
        CheckStatus(status=status, stage='Succesfully: %s/crs/install/rootcrs.pl -patch' % self.GridHome)
        for other in self.OtherHosts:
            self.logger.error('Running: ssh %s %s/crs/install/rootcrs.pl -patch' % (other, self.GridHome))
            status=getstatus('ssh %s %s/crs/install/rootcrs.pl -patch' % (other, self.GridHome))
            CheckStatus(status=status, stage='Succesfully: %s/crs/install/rootcrs.pl -patch on %s' % (self.GridHome, other))
    
        
        self.logger.error('Running: %s/bin/srvctl start home -o %s -s %s/Grid_%s.stat -n %s' \
                         %(self.GridHome, self.GridHome, self.SWLocation, os.environ['HOSTNAME'],\
                          os.environ['HOSTNAME']))
        status=getstatus('%s/bin/srvctl start home -o %s -s %s/Grid_%s.stat -n %s' \
                         %(self.GridHome, self.GridHome, self.SWLocation, os.environ['HOSTNAME'],\
                           os.environ['HOSTNAME']))
        CheckStatus(status=status, stage='Succesfully finish command on %s' % os.environ['HOSTNAME'])
        for other in self.OtherHosts:
            self.logger.error('Running:ssh %s %s/bin/srvctl start home -o %s -s %s/Grid_%s.stat -n %s' \
                             %(other, self.GridHome, self.GridHome, self.SWLocation, other,other))
            status=getstatus('ssh %s %s/bin/srvctl start home -o %s -s %s/Grid_%s.stat -n %s' \
                             %(other, self.GridHome, self.GridHome, self.SWLocation, other,other))
            CheckStatus(status=status, stage='Succesfully finish command on %s' % other)



class rac_config(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.HeartBit = self.config['HeartBit']
        #self.stop = self.config['Stop']
        if self.config.has_key('InterConnectNetworkAddres'):
            if self.config['InterConnectNetworkAddres']:
                self.InterConnectNetworkAddres = self.config['InterConnectNetworkAddres']
            else:    
                self.InterConnectNetworkAddres = '1.1.1.0' 
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        
        self.Interconnect()
        self.css()
        self.PreventStartup()
        
    def Interconnect(self):
        for inter in self.HeartBit.split(','):
            status=getstatus('%s/bin/oifcfg getif|grep cluster_interconnect|grep -v %s'%(self.GridHome, inter))
            if status[0] == 0:
                status=getstatus('%s/bin/oifcfg setif -global %s/%s:cluster_interconnect'%(self.GridHome, inter,\
                       self.InterConnectNetworkAddres))
                CheckStatus(status=status, stage='Succesfully: %s/bin/oifcfg setif -global %s/%s:cluster_interconnect'\
                       %(self.GridHome, inter, self.InterConnectNetworkAddres))


    def css(self):
        status=getstatus('%s/bin/crsctl set css misscount 600'%(self.GridHome))
        CheckStatus(status=status, stage='Succesfully: %s/bin/crsctl set css misscount 600'%(self.GridHome))

    def PreventStartup(self):
        status=getstatus('%s/bin/crsctl disable crs'%(self.GridHome))
        CheckStatus(status=status, stage='Succesfully: %s/bin/crsctl disable crs'%(self.GridHome))
        for other in self.OtherHosts:
            status=getstatus('ssh %s %s/bin/crsctl disable crs' %(other, self.GridHome))
            CheckStatus(status=status, stage='Succesfully: %s/bin/crsctl disable crs on %s '%(self.GridHome, other))


        
 
        
class linking(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        
        self.LVRTSLibary()
        self.RVRTSLibary()
        self.Monitor()


    def LVRTSLibary(self):
        RacStop(GridHome=self.GridHome)
        status=getstatus('su -c "cp -f %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck" oracle' \
                 %(self.OracleHome, self.OracleHome))
        CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck' \
                 %(self.OracleHome, self.OracleHome))
        status=getstatus('su -c "cp -f %s/lib/libodm11.so %s/lib/libodm11.so.oracle.bck" oracle' \
                 %(self.OracleHome, self.OracleHome))
        CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libodm11.so %s/lib/libodm11.so.oracle.bck' \
                 %(self.OracleHome, self.OracleHome))
        status=getstatus('su -c "rm -rf %s/lib/libodm11.so" oracle' %(self.OracleHome))
        status=getstatus('su -c "rm -rf %s/lib/libskgxn2.so" oracle' %(self.OracleHome))
        CheckStatus(status=status, stage='Succesfully: rm -rf %s/lib/libodm11.so && %s/lib/libskgxn2.so' \
                 %(self.OracleHome, self.OracleHome))
        status=getstatus('su -c "ln -s /usr/lib64/libodm.so %s/lib/libodm11.so" oracle' %(self.OracleHome))
        CheckStatus(status=status, stage='Succesfully: ln -s /usr/lib64/libodm.so %s/lib/libodm11.so' % self.OracleHome)
        status=getstatus('su -c "cp -f %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck" oracle' %(self.GridHome, self.GridHome))
        CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck '\
                 %(self.GridHome, self.GridHome))
        status=getstatus('su -c "cp -f /usr/lib64/libvcsmm.so %s/lib/libskgxn2.so" oracle' %(self.GridHome))
        CheckStatus(status=status, stage='Succesfully: cp -rf /usr/lib64/libvcsmm.so %s/lib/libskgxn2.so' %(self.GridHome))
        status=getstatus('su -c "ln -s %s/lib/libskgxn2.so %s/lib/libskgxn2.so" oracle' %(self.GridHome, self.OracleHome))
        CheckStatus(status=status, stage='Succesfully: ln -s %s/lib/libskgxn2.so %s/lib/libskgxn2.so' \
                 %(self.GridHome, self.OracleHome))
        RacStart(GridHome=self.GridHome, Stage='StartOnly')



    def RVRTSLibary(self):
        for other in self.OtherHosts:
            RacStop(GridHome=self.GridHome, ssh='ssh', server=other )
            status=getstatus('ssh %s \'su oracle -c "cp -f %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck" \'' \
                      %(other, self.OracleHome, self.OracleHome))
            CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck on %s' \
                      %(self.OracleHome, self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "cp -f %s/lib/libodm11.so %s/lib/libodm11.so.oracle.bck"\'' \
                      %(other, self.OracleHome, self.OracleHome))
            CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libodm11.so %s/lib/libodm11.so.oracle.bck on %s' \
                      %(self.OracleHome, self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "rm -rf %s/lib/libodm11.so"\'' %(other, self.OracleHome))
            status=getstatus('ssh %s \'su oracle -c "rm -rf %s/lib/libskgxn2.so"\'' %(other, self.OracleHome))
            CheckStatus(status=status, stage='Succesfully: rm -rf %s/lib/libodm11.so && %s/lib/libskgxn2.so on %s' \
                      %(self.OracleHome, self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "ln -s /usr/lib64/libodm.so %s/lib/libodm11.so" \'' %(other, self.OracleHome))
            CheckStatus(status=status, stage='Succesfully: ln -s /usr/lib64/libodm.so %s/lib/libodm11.so on %s ' \
                      % (self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "cp -f %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck" \'' \
                      %(other, self.GridHome, self.GridHome))
            CheckStatus(status=status, stage='Succesfully: cp -rf %s/lib/libskgxn2.so %s/lib/libskgxn2.so.oracle.bck on %s'\
                      %(self.GridHome, self.GridHome, other))
            status=getstatus('ssh %s \'su oracle -c "cp -f /usr/lib64/libvcsmm.so %s/lib/libskgxn2.so" \'' %(other, self.GridHome))
            CheckStatus(status=status, stage='Succesfully: cp -rf /usr/lib64/libvcsmm.so %s/lib/libskgxn2.so on %s' \
                      %(self.GridHome, other))
            status=getstatus('ssh %s \'su oracle -c "ln -s %s/lib/libskgxn2.so %s/lib/libskgxn2.so" \'' \
                      %(other, self.GridHome, self.OracleHome))
            CheckStatus(status=status, stage='Succesfully: ln -s %s/lib/libskgxn2.so %s/lib/libskgxn2.so on %s' \
                      %(self.GridHome, self.OracleHome, other))
            RacStart(GridHome=self.GridHome, ssh='ssh', server=other, Stage='StartOnly')


    def Monitor(self):
        time.sleep(120)
        RacStart(GridHome=self.GridHome, Stage='MonOnly')
        for other in self.OtherHosts:
            RacStart(GridHome=self.GridHome, ssh='ssh', server=other, Stage='MonOnly')
			
			
class listener(object):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        self.Flistener()

			
			
    def Flistener(self):
        self.logger.error('Starting to install listener')        
        status=getstatus('su -c "%s/bin/netca /silent /responsefile %s/netca.rsp" oracle' %(self.GridHome, self.SWLocation))
        CheckStatus(status=status, stage='Succesfully: %s/bin/netca /silent /responsefile %s/netca.rsp'\
                    %(self.GridHome, self.SWLocation))
		



class addinstancetogrid(object):

   def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.SWLocation = self.config['SWLocation']
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())
        self.Inventory = self.config['Inventory']
        self.GridHome = self.config['GridHome']
        self.OracleHome = self.config['OracleHome']
        self.SchemaName = self.config['SchemaName']
        self.log = '> /dev/null 2>&1'

   def __call__(self):
        self.InstanceToGrid()



   def InstanceToGrid(self):
        i=2
        self.logger.error('Starting to config the instance')        
        self.logger.error('Running: %s/bin/srvctl add database -d %s -o %s -p /data/oracle/APPDB/INIT/spfileAPPDB.ora \
                         -n %s -y manual' %(self.OracleHome, self.SchemaName, self.OracleHome, self.SchemaName))
        status=getstatus('su -c "%s/bin/srvctl add database -d %s -o %s -p /data/oracle/APPDB/INIT/spfileAPPDB.ora -n %s\
                -y manual" oracle' %(self.OracleHome, self.SchemaName, self.OracleHome, self.SchemaName))
        CheckStatus(status=status, stage='Successfully: %s/bin/srvctl add database -d %s -o %s \
                    -p /data/oracle/APPDB/INIT/spfileAPPDB.ora \
                    -n %s -y manual' %(self.OracleHome, self.SchemaName, self.OracleHome, self.SchemaName))
        self.logger.error('Running: %s/bin/srvctl add instance -d %s -i %s1 -n %s'\
                         %(self.OracleHome, self.SchemaName, self.SchemaName.strip(), os.environ['HOSTNAME']))
	status=getstatus('su -c "%s/bin/srvctl add instance -d %s -i %s1 -n %s" oracle' \
                        %(self.OracleHome, self.SchemaName, self.SchemaName.strip(), os.environ['HOSTNAME']))
	CheckStatus(status=status, stage='successfully: %s/bin/srvctl add instance -d %s -i %s1 -n %s'\
               		%(self.OracleHome, self.SchemaName, self.SchemaName.strip(), os.environ['HOSTNAME']))
	for other in self.OtherHosts:
            self.logger.error('Runing: %s/bin/srvctl add instance -d %s -i %s%s -n %s'\
                             %(self.OracleHome, self.SchemaName, self.SchemaName.strip(), i, other))
	    status=getstatus('su -c "%s/bin/srvctl add instance -d %s -i %s%s -n %s" oracle' \
                    %(self.OracleHome, self.SchemaName, self.SchemaName.strip(), i, other))
	    CheckStatus(status=status, stage='successfully: %s/bin/srvctl add instance -d %s -i %s%s -n %s'\
               	    %(self.OracleHome, self.SchemaName, self.SchemaName.strip(), i, other))
	    i = i + 1
        self.logger.error('Runing: %s/bin/srvctl start database -d %s' %(self.OracleHome, self.SchemaName))
        status=getstatus('su -c "%s/bin/srvctl start database -d %s" oracle' \
                        %(self.OracleHome, self.SchemaName))
	CheckStatus(status=status, stage='successfully: %s/bin/srvctl start database -d %s'\
               		%(self.OracleHome, self.SchemaName))





class oracleswuntar(builder):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())    
	self.bz2 = self.config['Oracle_BZ2']
        self.log = '> /dev/null 2>&1'
        self.SchemaName = self.config['SchemaName']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'

    def __call__(self):
        self.Luntar()
        self.Runtar()
        self.LFitOracleBZ2()
        self.RFitOracleBZ2()
	
    def Luntar(self):
        if not os.path.isfile(self.bz2):
            self.logger.error('\'%s\' was not found' % self.bz2)
            raise Exception, 'File was not found'
        self.logger.error('\'%s\' was found' % self.bz2)
        os.chdir('/')
        self.logger.error('changed directory to \'/\'')
        self.logger.error('Starting to untar the bz2 file, may take a while...')
        if os.system('/bin/tar xvf %s >> /dev/null' % self.bz2) != 0:
            self.logger.error('Failed to untar bz2 file: %s' % self.bz2)
            raise Exception, '%122%'
        self.logger.error('Succesefully: untar bz2 file: %s' % self.bz2)
		
	
    def Runtar(self):
        for other in self.OtherHosts:
            status=getstatus('ssh %s /bin/ls %s' %(other, self.bz2))
            CheckStatus(status=status, stage='check if the file %s exist in %s ' % (self.bz2, other))
            self.logger.error('ssh %s "cd /;tar xvf %s"' %(other, self.bz2))
            status=getstatus('ssh %s "cd /;tar xvf %s"' %(other, self.bz2))
            CheckStatus(status=status, stage='Succesfully: ssh %s "cd /;tar xvfj %s"' % (self.bz2, other))

   
    def LFitOracleBZ2(self):
        self.logger.error('Runing: /bin/cp -rf %s/log/ServerName %s/log/%s' \
                        %(self.OracleHome, self.OracleHome, os.environ['HOSTNAME']))
        status=getstatus('su -c "/bin/cp -rf %s/log/ServerName %s/log/%s" oracle' \
                        %(self.OracleHome, self.OracleHome, os.environ['HOSTNAME']))
        CheckStatus(status=status, stage='successfully: /bin/cp %s/log/ServerName %s/log/%s'\
                        %(self.OracleHome, self.OracleHome, os.environ['HOSTNAME']))
        self.logger.error('Runing: /bin/cp -rf /u01/oracle/diag/rdbms/appdb/OraSid /u01/oracle/diag/rdbms/appdb/%s1' \
                        %(self.SchemaName))
        status=getstatus('su -c "/bin/cp -rf /u01/oracle/diag/rdbms/appdb/OraSid /u01/oracle/diag/rdbms/appdb/%s1" oracle'\
                        %(self.SchemaName))
        CheckStatus(status=status,stage='successfully:/bin/cp /u01/oracle/diag/rdbms/appdb/OraSid /u01/oracle/diag/rdbms/appdb/%s1'\
                        %(self.SchemaName))
        self.logger.error('Runing: /bin/rm -f %s/dbs/hc_APPDB1.dat' %(self.OracleHome))
        status=getstatus('su -c "/bin/rm -f %s/dbs/hc_APPDB1.dat" oracle'  %(self.OracleHome))
        CheckStatus(status=status,stage='successfully:/bin/rm -f %s/dbs/hc_APPDB1.dat' %(self.OracleHome))
        self.logger.error('Runing: /bin/rm -f %s/dbs/orapwAPPDB1' %(self.OracleHome))
        status=getstatus('su -c "/bin/rm -f %s/dbs/orapwAPPDB1" oracle'  %(self.OracleHome))
        CheckStatus(status=status,stage='successfully:/bin/rm -f %s/dbs/orapwAPPDB1' %(self.OracleHome))
        self.logger.error('Runing: ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s1'\
                        %(self.OracleHome, self.SchemaName))
        status=getstatus('su -c "ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s1" oracle' \
                        %(self.OracleHome, self.SchemaName))
        CheckStatus(status=status,stage='successfully:ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s1'\
                        %(self.SchemaName, self.OracleHome))


    def RFitOracleBZ2(self):
        i=2
        for other in self.OtherHosts:
            self.logger.error('Runing: /bin/cp %s/log/ServerName %s/log/%s on %s'\
                        %(self.OracleHome, self.OracleHome, other, other))
            status=getstatus('ssh %s \'su oracle -c "/bin/cp -rf %s/log/ServerName %s/log/%s" \'' \
                        %(other, self.OracleHome, self.OracleHome, other))
            CheckStatus(status=status, stage='successfully: /bin/cp -rf %s/log/ServerName %s/log/%s on %s'\
                        %(self.OracleHome, self.OracleHome, other, other))
            self.logger.error('Runing: /bin/cp -rf /u01/oracle/diag/rdbms/appdb/OraSid /u01/oracle/diag/rdbms/appdb/%s%s on %s'\
                        %(self.SchemaName, i, other))
            status=getstatus('ssh %s \'su oracle -c "/bin/cp -rf /u01/oracle/diag/rdbms/appdb/OraSid \
                             /u01/oracle/diag/rdbms/appdb/%s%s" \'' %(other, self.SchemaName, i))
            CheckStatus(status=status,stage='successfully:/bin/cp -rf /u01/oracle/diag/rdbms/appdb/OraSid /u01/oracle/diag/rdbms/appdb/%s%s on %s' %(self.SchemaName, i, other))
            self.logger.error('Runing: /bin/rm -f %s/dbs/hc_APPDB1.dat on %s' %(self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "/bin/rm -f %s/dbs/hc_APPDB1.dat" \''  %(other, self.OracleHome))
            CheckStatus(status=status,stage='successfully:/bin/rm -f %s/dbs/hc_APPDB1.dat on %s' %(self.OracleHome, other))
            self.logger.error('Runing: /bin/rm -f %s/dbs/orapwAPPDB1 on %s' %(self.OracleHome, other))
            status=getstatus('ssh %s \'su oracle -c "/bin/rm -f %s/dbs/orapwAPPDB1" \''  %(other, self.OracleHome))
            CheckStatus(status=status,stage='successfully:/bin/rm -f %s/dbs/orapwAPPDB1 on %s' %(self.OracleHome, other))
            self.logger.error('Runing: ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s%s on %s' \
                             %(self.OracleHome, self.SchemaName, i, other))
            status=getstatus('ssh %s \'su oracle -c "ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s%s" \'' \
                            %(other, self.OracleHome, self.SchemaName, i))
            CheckStatus(status=status,stage='successfully:ln -sf /data/oracle/APPDB/INIT/orapwAPPDB %s/dbs/orapw%s%s on %s' \
                       %(self.OracleHome, self.SchemaName, i, other))
            i = i + 1


class instanceuntar(oracleswuntar):
    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.config = config
        self.OtherHosts = []
        for other in self.config['OtherHostname'].split(','):
            self.OtherHosts.append(other.split(':')[0].strip())
        self.log = '> /dev/null 2>&1'
        self.SchemaName = self.config['SchemaName']
        self.OracleHome = self.config['OracleHome']
        self.log = '> /dev/null 2>&1'
	self.bz2 = self.config['Instance_BZ2']

    def __call__(self):
        self.Luntar()
	

