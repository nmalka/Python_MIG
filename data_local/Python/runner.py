#!/usr/bin/env python

###############################
#   Date: 24/05/2011          #
#   FileName: runner.py       #
###############################

# Modules:
import time
import os
import sys, string, datetime, time

PyPath = ['/data_local/Python/Pymodules','/data_local/Python/funcPy']
for path in PyPath:
    if path not in sys.path:
        sys.path.append(path)
        
import re
from Pymodule import *
#from Pyfiledit import filesToBakup,CopyUtils
from Pyfiledit import *
from glob import glob
from Pyrunner import *
import traceback
from Pytraceback import tb_frame_locals
# Exception DEBUG vars:
DEBUG = False
PRINT_DEBUG = False
######### MAIN ########
try:
    conFile = sys.argv[1]
    script = os.path.basename(sys.argv[0])
except:
    print >> sys.stderr,"Usage: %s <configfile full name>" % (os.path.basename(sys.argv[0]))
    #print "Usage: %s <configfile full name>" % \
    #        (os.path.basename(sys.argv[0]))
    sys.exit(111)

# get optional args:
Argv = []
for i in range(2, len(sys.argv)):
    Argv.append(sys.argv[i])

filesDir = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), '.runner')
if not os.path.isdir(filesDir): os.mkdir(filesDir, 0750)
LockFile = os.path.join(filesDir, '%s.pid' % os.getpid())
# get Dict/Module from config file
try:
    if conFile.endswith('.py'):
        if not os.path.isfile(conFile):
            raise Exception, 'No such file: \"%s\"' % conFile
        config = {}
        execfile(conFile, {}, config)
    elif conFile.endswith('.pyc') or conFile.endswith('.pyo'):
        if not os.path.isfile(conFile):
            raise Exception, 'No such file: \"%s\"' % conFile
        path = os.path.dirname(conFile)
        conFile = os.path.basename(conFile)
        if path not in sys.path:
            sys.path.insert(0, path)
        exec('import %s as confPy' % conFile[:-4])
        config = confPy.__dict__
    else:
        config = ReadFileConfig(file=conFile).GetHash()
    if config.has_key('iData') and type(config['iData']) == dict:
        config.update(config['iData']) 
    if config.has_key('iNames') and (type(config['iNames']) == list or type(config['iNames']) == tupe):
        for iName in config['iNames']:
            i = iName.split('=', 1)
            if i.__len__() != 2:
                raise Exception, 'IllegaliRule: iName must contain at least one \"=\" got \"%s\"' % iName
            else:
                config[i[0].strip()] = i[1].strip()
 
except RunnerConfDummy:
    print 
    print '%s: %s' % (sys.exc_info()[0],sys.exc_info()[1])
    print "\n\t\t#####  Script ended successfully.  #####\n"
    sys.exit(0)
except:
    RemovePidLockFile(LockFile)
    if PRINT_DEBUG: print tb_frame_locals(DEBUG)
    #print "Failed to load runner configuration file: %s" % (conFile)
    print >> sys.stderr,"Failed to load runner configuration file: %s" % (conFile)
    raise

unlock = config.get('Unlock', False) or False
# checking if another process is running by any user, if so exit the script with an error 
if not unlock:
    RunnerPidCheck(filesDir, script)
    lfh = open(LockFile, 'w')
    lfh.close()
#extend sys.path module
pythonpath = config.get('PythonPath', False)
if pythonpath and type(pythonpath) == str:
    pythonpath = pythonpath.split(',')
    for i in pythonpath:
        sys.path.append(i) 
# defined SEM variable
if conFile.endswith('.py'): 
    fileName = os.path.basename(conFile[:-3])
elif conFile.endswith('.pyc') or conFile.endswith('.pyo'):
    fileName = os.path.basename(conFile[:-4])
else:
    fileName = os.path.basename(conFile)
    
SEM = False
if config.get('SingleRunning',  False) and config['SingleRunning'].lower() == 'yes':
    SEM = True
    OutputDir = config.get('OutputFilesFolder', False) or filesDir
else:
    # Clean up for reset
    if os.path.isdir(filesDir):
        filesToRemove = [f for f in glob(os.path.join(filesDir, fileName +'_success')) if os.path.isfile(f)]
        filesToRemove2 = [f for f in glob(os.path.join(filesDir, fileName +'_falied')) if os.path.isfile(f)]
        for fileRemove in filesToRemove + filesToRemove2:
            os.remove(os.path.join(filesDir, fileRemove))

# Automatic modules loader:
mod = 'from %s import *'
Modules = []
if  config.has_key('Modules'):
    if type(config['Modules']) == str or type(config['Modules']) == unicode:
        Modules = [ m.strip() for m in config['Modules'].split(',') if m] 
    else:
        Modules = config['Modules']
    for module in Modules:
        try:
            exec mod % module
        except:
            RemovePidLockFile(LockFile)
            #print "Can not load the given module: %s" % module
            print >> sys.stderr,"Can not load the given module: %s" % module
            raise

# RUNNER ID:
if config.get('_', False) and config.get('Section', False):
    componentID = config.get('Section')
elif config.get('componentID') and config['componentID']:
    componentID = config['componentID']
else:
    try:
        ID = config['componentIDFile']
        file = open(ID)
        componentID = file.readline()
        componentID = string.upper(componentID.strip())
        file.close()
    except:
        componentID = 'GENERIC'
#time.sleep(300)
# Building the global VAR
try:
    mode = config['Mode']
except:
    RemovePidLockFile(LockFile)
    if PRINT_DEBUG: print tb_frame_locals(DEBUG)
    #print "Could not get \"Mode\" param from config file: %s" % conFile
    print >> sys.stderr,"Could not get \"Mode\" param from config file: %s" % conFile
    raise

# Setting up the log:
try:
    logFile = config['LogFile']
    if not logFile: raise Exception, 'LogFile parameter is empty.'
    if int(config['LogLevel']) > 2: raise Exception, 'Usage LogLevel: 0/1/2 - Normal/Info/Debug\nGiven: %s' \
           % config['LogLevel']
except:
    RemovePidLockFile(LockFile)
    if PRINT_DEBUG: print tb_frame_locals(DEBUG)
    print >> sys.stderr,'Error in LogFile parameters in \'%s\' file' % conFile
    #print 'Error in LogFile parameters in \'%s\' file' % conFile
    raise

logger = Pylogger(logFile=logFile,
                  logLevel=str(config['LogLevel']),
                  loggerName='',
                  )
logger.error("\n\n\t\t##### RUNNER SCRIPT STARTS #####")
logger.error("componentID=%s, MODE=%s" % (componentID, mode))

# Runner Lock
if config.get('_', False):
    _ = config['_']
    section = config.get('Section', False)
    if _(section, 'runner_lock', False).lower() == 'yes':
        logger.error("Runner is locked for %s Section!!!" % section)
        #print "Runner is locked for %s Section!!!" % section
        print >> sys.stderr,"Runner is locked for %s Section!!!" % section
        RemovePidLockFile(LockFile)
        sys.exit(151)
    elif _('RUNNER', 'runner_lock', False).lower() == 'yes' and \
        ((not _(section, 'runner_lock', False)) or _(section, 'runner_lock', False).lower() == 'yes'):
        logger.error("Global Runner is locked!!!")
        #print "Global Runner is locked!!!"
        print >> sys.stderr,"Global Runner is locked!!!"
        RemovePidLockFile(LockFile)
        sys.exit(150)
if SEM:
    ignoreModes = []
    try:
        if not os.path.isdir(OutputDir): os.mkdir(OutputDir, 0750)
        if os.path.isfile(os.path.join(OutputDir, fileName + '_failed')):
            try:
                file = open(os.path.join(OutputDir, fileName + '_failed'), 'r') 
                line = file.readline()
                for modeClass in line.split(', '):
                    ignoreModes.append(modeClass)
                file.close()
            except:
                logger.debug(tb_frame_locals(DEBUG))
                logger.error(traceback.format_exc())
                logger.error("Could not open the %s file." % os.path.join(OutputDir, fileName + '_failed'))
                file.close()
                print "Could not open the %s file." % os.path.join(OutputDir, fileName + '_failed')
                raise
            os.remove(os.path.join(OutputDir, fileName + '_failed'))
        elif os.path.isfile(os.path.join(OutputDir, fileName + '_success')):
            raise SingleExecutionException, '"%s" runner was already successfully executed on "%s".' % ((fileName), \
                            time.ctime(os.path.getmtime(os.path.join(OutputDir, fileName + '_success'))))
    except SingleExecutionException:
        logger.error('%s: %s' % (sys.exc_info()[0], sys.exc_info()[1]))
        print >> sys.stderr,'%s: %s' % (sys.exc_info()[0], sys.exc_info()[1])
        #print '%s: %s' % (sys.exc_info()[0], sys.exc_info()[1])
        logger.error('runner script was failed. Bye Bye!')
        print >> sys.stderr,'runner script was failed. Bye Bye!'
        #print 'runner script was failed. Bye Bye!'
        RemovePidLockFile(LockFile)
        sys.exit(155)    
            
# Create a backup to the files
try:
    files = config.get('Files', False)
    if files and type(config['Files']) == list:
        config['Files']= ','.join(str(n) for n in config['Files'])
    if filesToBakup(config):
# building instance for file utils.
        loggy = '>> %s 2>&1' % logFile
        File = CopyUtils(Files=config['Files'], Path=config['BackupPath'], log=loggy) 
        logger.error('Starting the backup:')
        editFiles = File.Backup()
except:
    logger.error(traceback.format_exc())
    print traceback.format_exc()
    logger.error('Got exception while performing backup to the files/dirs. Bye!.')
    print '\tGot exception while performing backup to the files/dirs. tail the log for more info!.'
    RemovePidLockFile(LockFile)
    sys.exit(109)

# Print for dummy execution.
if not mode:
    print "Dummy runner execution, nothing were executed!"
if type(mode) == list or type(mode) == tuple :
    mode = ','.join(str(n) for n in mode) 
if SEM: succesModes = []
for klass in [ m.strip() for m in mode.split(',') if m ]:
    if SEM:
        if klass in ignoreModes:
            succesModes.append(klass)
            logger.error("Skipping \'%s\' module, due previously execution." % klass)
            buildFile(False, succesModes, logger, fileName, OutputDir)
            continue
    logger.error("\n\n\t\t@@@@@@ Starting to invoke \'%s\' class @@@@@@@\n" % klass)
    try:
    # Class caller:
        instance = locals()[klass](config=config, componentID=componentID, Argv=Argv)
    except:
        logger.debug(tb_frame_locals(DEBUG))
        logger.error(traceback.format_exc())
        logger.error('Initialized error at the instance constructor on \'%s\' mode' % klass)
        print traceback.format_exc()        
        print '\tInitialized error at the instance constructor on \'%s\' mode' % klass
        if SEM:
            buildFile(False, succesModes, logger, fileName, OutputDir)
        RemovePidLockFile(LockFile)
        sys.exit(111)

    try:
    # instance caller:
        if filesToBakup(config) and editFiles :
            instance(editFiles=editFiles)
        else:
            instance()
    except:
        logger.debug(tb_frame_locals(DEBUG))
        logger.error(traceback.format_exc())
        logger.error('runner script with mode: \'%s\' was failed. Bye Bye!' % klass)
        print traceback.format_exc()
        print >> sys.stderr,'runner script with mode: \'%s\' was failed. Bye Bye!' % klass
        #print 'runner script with mode: \'%s\' was failed. Bye Bye!' % klass
        if filesToBakup(config):
            logger.error('Going to roll-back the files and Bye Bye!.')
            print >> sys.stderr,'Going to roll-back the files and Bye Bye!.'
            #print 'Going to roll-back the files and Bye Bye!.'
            File.RollBack()
        if SEM:
            buildFile(False, succesModes, logger, fileName, OutputDir)
        RemovePidLockFile(LockFile)
        sys.exit(111)
    if SEM:
        succesModes.append(klass)
        buildFile(False, succesModes, logger, fileName, OutputDir)
            
    logger.error("\n\n\t\t@@@@@@ \'%s\' class ended successfully. @@@@@@@\n" % klass)

if SEM:
    buildFile(True, succesModes, logger, fileName, OutputDir)
    if os.path.isfile(os.path.join(OutputDir, fileName + '_failed')):
        os.remove(os.path.join(OutputDir, fileName + '_failed'))
logger.error("#####  Script ended successfully.  #####\n")
print "\n\t\t#####  Script ended successfully.  #####\n"
RemovePidLockFile(LockFile)
