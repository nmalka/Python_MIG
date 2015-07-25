
###############################
#   By: Itzik Ben Itzhak      #
#   Mail: itzik.b.i@gmail.com #
#   Ver: 4.8.0.1_STF7         #
#   ModuleName: Pysnmp.py     #
###############################

# MIG SNMP Module:
class SnmpTrap:
    def __init__(self, 
                version, 
                message,
                managerIP=[], 
                argV1='-v 1 -c', 
                argV2='-v 2c -c', 
                community='public', 
                OID='', 
                SUB_OID='', 
                port=162, 
                num=6, 
                emptyStr='\"\"', 
                logFile='/dev/null',
                loggerName=''):
        import os
        import logging
        self.logger = logging.getLogger(loggerName)
        self.snmptrap = []
        self.managerIP = managerIP
        self.logFile = logFile
#snmptrap <argV1> <community> <managerIP>:<port> <OID> <HOSTNAME> <num> <SUB_OID> <emptyStr> <MOID> s <MESSAGE>
        if version == '1' or version == 1:
            for ip in managerIP:
                self.snmptrap.append('/usr/bin/snmptrap %s %s %s:%s %s %s %s %s %s %s' % ( argV1,
                                    community,
                                    ip,
                                    port,
                                    OID,
                                    os.environ['HOSTNAME'],
                                    num,
                                    SUB_OID,
                                    emptyStr,
                                    message,
                                    ))
        #snmptrap <argV1> <community> <managerIP>:<port> <emptyStr> <OID>.<SUB_OID> <MOID> s <message>
        elif version == '2' or version == 2:
            for ip in managerIP:
                self.snmptrap.append('/usr/bin/snmptrap %s %s %s:%s %s %s.%s %s' % (argV2,
                            community,
                            ip, 
                            port,
                            emptyStr,
                            OID,
                            SUB_OID,
                            message,
                            ))
    def send(self, messageExtend='', logMessage='', loggerName=''):
        import os
        if len(self.managerIP)>0:
            self.logger.error('Sending SNMP Trap: %s To:%s' % (logMessage, self.managerIP))
        for snmptrap in self.snmptrap:
            snmptrap = snmptrap % messageExtend
            self.logger.debug(snmptrap)
            os.system("%s >> %s 2>&1" % (snmptrap,self.logFile))

