
###############################
#   By: Itzik Ben Itzhak      #
#   Mail: itzik.b.i@gmail.com #
#   Ver: 5.2                  #
#   Date: 24/08/09            #
#   ModuleName: Pymodule.py   #
###############################


def Pylogger(logFile='/var/logs/MigGenericLogFile',
            logLevel='0',
            rotate='0',
            backupCount=None,
            maxBytes=None,
            loggerName='',
            format=''):
    import logging
    import logging.handlers
    LEVELS = {'2': logging.DEBUG,
              '1': logging.INFO,
              'warning': logging.WARNING,
              '0': logging.ERROR,
              'critical': logging.CRITICAL
              }
    logger = logging.getLogger(loggerName)
    logLevel = LEVELS.get(logLevel, logging.ERROR)
    formatter = format or logging.Formatter('[%(asctime)s] %(message)s','%Y-%m-%d %a %H:%M:%S')
    if rotate == '1' or rotate == 1:
        hdlr1 = logging.handlers.RotatingFileHandler(logFile,
                                                        maxBytes=maxBytes, 
                                                        backupCount=backupCount
                                                        )
        hdlr1.setFormatter(formatter)
        logger.addHandler(hdlr1)
    else:
        hdlr = logging.FileHandler(logFile)
        hdlr.setFormatter(formatter)
        logger.addHandler(hdlr)
    logger.setLevel(logLevel)
    return logger

def userHostSplit(serv,loggerName=''):
    import logging
    logger = logging.getLogger(loggerName)
    try:
        username, hostname = serv.split('@')
        return username, hostname
    except:
        logger.error('Usage: username@hostname/ip given: %s" % (serv)')
        raise StopIteration

def listFilesByDate(dir, extention='',IgnorDate=None,loggerName=''):
    import logging
    import glob, time, os, traceback
    logger = logging.getLogger(loggerName)
    date_file_list = []
    try:
        for _file in glob.glob(dir + extention):
            try:
                stats = os.stat(_file)
                lastmod_date = time.localtime(stats[8])
                date_file_tuple = lastmod_date, _file
                date_file_list.append(date_file_tuple)
            except:
                logger.debug("Can not stat file: %s\n%s" % (_file, traceback.format_exc()))
                continue
        date_file_list.sort()
        date_file_list.reverse()
    except:
        logger.info("Can not list local cdr path: %s\n%s" % (dir, traceback.format_exc()))
        return [], []
    if len(date_file_list)>0:
        if IgnorDate:
            maxDate = time.localtime(time.time() - IgnorDate)
            cdrfiles = []
            oldfiles = []
            for file in date_file_list:
                if file[0] > maxDate:
                    cdrfiles.append(file[1])
                else:
                    oldfiles.append(file[1])
            return oldfiles, cdrfiles
        else:
            return [],[ file for date,file in date_file_list ]
    else:
        logger.debug("Listing %s reveal None!" % (dir+extention))
        return [], []

class ReadFileConfig:
    def __init__(self, file, *args, **kwargs):
        self.file=file
    def GetHash(self):
        import re
        hash = {}
        for line in open(self.file):
            if not line.startswith('#'):
                if line.strip():
                    line = line.strip()
                    line = re.sub(r',[\s\t]*$', '', line) 
                    #hash[line.split('=')[0]] = line.split('=')[1].strip()
                    hash[re.split(r'[\s\t]?=[\s\t]?', 
                        line, 1)[0]] = re.split(r'[\s\t]?=[\s\t]?', line,1)[1].strip()
        return hash

def InstanceDuration(snmptrap, timeDelta=30, scale='Min', loggerName=''):
    import datetime, time, os
    import logging
    userHost = '%s@%s' % (os.environ['USER'],os.environ['HOSTNAME'])
    logger = logging.getLogger(loggerName)
    starts = datetime.datetime.now()
    if scale == 'Min':
        sleepDelta = timeDelta*60
    elif scale == 'Hour':
        sleepDelta = timeDelta*60*60
    else:
        sleepDelta = timeDelta
    time.sleep(sleepDelta)
    now = datetime.datetime.now()
    delta = now - starts
    try:
        snmptrap.send(messageExtend=(userHost,
                            '%s[%s]' % (timeDelta, scale),
                            delta,),
                    logMessage='script passed the threshold time, %s%s, running for %s' % \
                            (timeDelta, scale,delta)
                            )
        logger.error("script passed the threshold time, %s%s, running for %s" % \
                (timeDelta, scale,delta))
    except:
        logger.info("script passed the threshold time, %s%s, Fail to send trap" % \
                (timeDelta, scale))
def dirFix(path):
    if not path.endswith('/'):
        path = path + '/'
    return path
