
###############################
#   By: Itzik Ben Itzhak      #
#   Date: 28/02/2011          #
#   Modue: Pyrunner.py        #
###############################

# Modules:
import os
import sys, datetime, time
from glob import glob
import traceback

__all__ = ['SingleExecutionException', 'buildFile', 'ProcessesDuration', 'RemovePidLockFile', 'RunnerPidCheck', 'RunnerConfDummy']

class SingleExecutionException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value
    
class RunnerConfDummy(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

def buildFile(modeStatus, succesModes, logger, fileName, OutputDir):
    classesToWrite = ', '.join(succesModes)
    if modeStatus:
        try:
            file = open(os.path.join(OutputDir, fileName + '_success'), 'w')
            file.write('%s' % classesToWrite)
            file.close()
        except:
            logger.error("Could not create %s file under %s." % (fileName + '_success', OutputDir))
            print "Could not create %s file under %s." % (fileName + '_success', OutputDir)
            print traceback.format_exc()
            try:
                file.close()
            except:
                pass
            sys.exit(153)
    elif not modeStatus:
        try:
            file = open(os.path.join(OutputDir, fileName + '_failed'), 'w')
            file.write('%s' % classesToWrite)
            file.close()
        except:
            logger.error("Could not create %s file under %s." % (fileName + '_failed', OutputDir))
            print "Could not create %s file under %s." % (fileName + '_failed', OutputDir)
            print traceback.format_exc()
            try:
                file.close()
            except:
                pass
            sys.exit(154)
 
def ProcessesDuration(file):
    try:
        now = datetime.datetime.now()
        stats = os.stat(file)
        pid_created = datetime.datetime.fromtimestamp(stats[8])
        return str(now - pid_created).split('.', 1)[0]
    except:
        return 'Unknown'

def RemovePidLockFile(pid_file):
    try:
        os.remove(pid_file)
    except:
        pass

def RunnerPidCheck(folder, process_name, glob_filter='*.pid', 
                   pid_file_spliter='.', pid_split_position=0):
    pids = [f for f in glob(os.path.join(folder, glob_filter)) if os.path.isfile(f)]
    if len(pids) > 0:
        for pid in pids:
            try:
                proc_info = open('/proc/%s/cmdline' % \
                            os.path.basename(pid).split(pid_file_spliter, 1)[pid_split_position], 'r')
                proc_pid = proc_info.readline()
                proc_info.close()
            except:
                os.remove(os.path.join(folder,pid))
                continue
            if proc_pid.find(process_name) > -1:
                print """
Runner is allready running:
    PROCESS_NAME: %(process_name)s
    DURATION: %(duration)s
    CMDLINE: %(cmdline)s
    PID: %(pid)s
""" % \
                           {'pid' : os.path.basename(pid).split(pid_file_spliter, 1)[pid_split_position],
                           'duration' : ProcessesDuration(pid),
                           'cmdline' : proc_pid.replace('\x00', ' '),
                           'process_name' : process_name}
                sys.exit(302)
            else:
                os.remove(os.path.join(folder,pid))
