
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#   Date: 24/06/09               #
#   ModuleNmae: Pytm.py          #
##################################

from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys

def DigHostsIP(reg, file='/etc/hosts'):
    import re
    f = open(file)
    lines = f.readlines()
    f.close()
    r = re.compile(reg, re.I)
    IPHost = {}
    for line in lines:
        if r.search(line):
            if line.startswith('#'):
                continue
            else:
                return re.split(r'[\s\t]+', line, 1)
    raise Exception, 'RegEx did NOT match \'%s\' in %s file, can NOT get the relevat IP' % (reg ,file)

class tm_app(builder):
    def __call__(self, editFiles):
        methodDict = { 'config.ini' : '_config_ini',
                       'inittab' : '_inittab',
                       'hosts' : '_hosts',
                }
        super(tm_app, self).__call__(editFiles=editFiles, methodDict=methodDict)
    def _hosts(self):
        import os
        host = os.environ['HOSTNAME']
        if os.path.isfile(self.config['IDFile']):
            f = open(self.config['IDFile'])
            id = f.readline()
            f.close()
            if id.endswith('\n'): id = id[:-1]
        else:
            raise Exception, 'Can NOT get ID from \'%s\', no such file.' % self.config['IDFile']
        lines = []
        for line in self.linesRef:
            line = re.sub('(?P<b_id>.*?%s)_\d+?_(?P<a_id>[WE]DN.*)' % host, r'\g<b_id>_%s_\g<a_id>' % \
            id, line)
            lines.append(line)
        self.file.writelines(lines)
    def _config_ini(self):
        gmc, gmcHost = DigHostsIP(self.config['GMC'])
        self.logger.debug('DigHostsIP return for gmc: %s %s' % (gmc, gmcHost[:-1]))
        lines = []
        for line in self.linesRef:
            line = re.sub('(?P<gmcvip>ManagerIPAddress=).*', r'\g<gmcvip>%s' % gmc, line)
            for key, val in self.config.iteritems():
                if key.startswith('$') and val:
                    line = re.sub('(?P<key>%s=).*' % key[1:], r'\g<key>%s' % val, line)
            lines.append(line)
        self.file.writelines(lines)
    def _inittab(self):
        lines = []
        tmIP, TMHost = DigHostsIP(self.config['TMWDN'])
        mdsu, mdsuHost = DigHostsIP(self.config['MDSU'])
        gmc, gmcHost = DigHostsIP(self.config['GMC'])
        self.logger.debug('DigHostsIP return for TM WDN: %s %s' % (tmIP, TMHost[:-1]))
        self.logger.debug('DigHostsIP return for gmc: %s %s' % (gmc, gmcHost[:-1]))
        self.logger.debug('DigHostsIP return for mdsu: %s %s' % (mdsu, mdsuHost[:-1]))
        healthRegEDN = re.compile(self.config['HealthRegEDN'], re.I)
        healthRegWDN = re.compile(self.config['HealthRegWDN'], re.I)
        healthCheckRADIUS = re.compile(self.config['HealthCheckRADIUS'], re.I)
        for line in self.linesRef:
            # searching for HealthCheck to mdsu and gmc
            if healthRegEDN.match(line):
                line = healthRegEDN.match(line).group('cmd') + \
                       tmIP + \
                       healthRegEDN.match(line).group('args') + \
                       gmc + ' ' + \
                       mdsu + '\n'
            # searching for HealthCheck to LBA 8080 
            elif healthRegWDN.match(line):
                line = healthRegWDN.match(line).group('cmd') + \
                       tmIP + \
                       healthRegWDN.match(line).group('args') + '\n'
            # searching for HealthCheck to LBA Radius
            elif healthCheckRADIUS.match(line):
                line = healthCheckRADIUS.match(line).group('cmd') + \
                       tmIP + \
                       healthCheckRADIUS.match(line).group('args') + '\n'
            lines.append(line)
        self.file.writelines(lines)
        self.file.close()
        if os.system('init q %s' % self.log) != 0:
            raise Exception, 'Failed to run \'init q\''
