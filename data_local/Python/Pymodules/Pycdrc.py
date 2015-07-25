
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#   Date: 12/07/09               #
#   ModuleNmae: Pycdrc.py        #
##################################

from Pykex import DigHostsIPs
from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys

class cdrc_app(builder):

    def __call__(self, editFiles):
        self.Mcdrc = 0
        try:		
            self.Mcdrc = int(self.config['NumOfCDRCMgr'])
            if self.Mcdrc == 0:
                raise Exception
        except:
            self.logger.error('Skipping Multi CDRMgr configuration, NumOfCDRCMgr is disable')
            methodDict = { 'inittab' : '_inittab', }
        else:
            methodDict = { 'ApplicationsCDRMgr.xml' : '_AppCDRMgr',
			    		   'CDRMgr' : '_CDRMgr',
                           'inittab' : '_inittab',
                         }
        super(cdrc_app, self).__call__(editFiles=editFiles, methodDict=methodDict)
        if self.Mcdrc:
            self.logger.error('Restart babysitter in order to reload the new processes(%s) of CDRMgr' % \
                               self.Mcdrc)
    def _inittab(self):
        _ = self.config['_']
        Section = self.config['Section']

        host = _(Section, 'hostname')
        EDN = _(Section, 'admin_network', False) or 'EDN'
        cdrc = {  _(Section, EDN.lower() + '-rip') : host}
       
        self.logger.debug('System Config return for \"%s\": %s' % (_(Section, 'server_key'), cdrc))
        cdrc = cdrc.keys()[0]

        lines = []
        healthRegCDRMgr = re.compile(self.config['HealthRegCDRMgr'], re.I)
        for line in self.linesRef:
            # searching for HealthCheck for CDRMgr
            if healthRegCDRMgr.match(line):
                line = healthRegCDRMgr.match(line).group('cmd') + \
                       cdrc + \
                       healthRegCDRMgr.match(line).group('args') + '\n'
            lines.append(line)
        self.file.writelines(lines)
        self.file.close()
        if os.system('init q %s' % self.log) != 0:
            raise Exception, 'Failed to run \'init q\''
    def _AppCDRMgr(self):
        lines = []
        for line in self.linesRef:
            RegexMcdrc = re.compile('CDRMgr_\d+')
            if RegexMcdrc.search(line):
                line = RegexMcdrc.sub('CDRMgr_%s' % self.Mcdrc, line)
            lines.append(line)
        self.file.writelines(lines)
        
    def _CDRMgr(self):
        lines = []
        for line in self.linesRef:
            RegexMcdrc = re.compile('CdrAgentInvoke\s\d+\s')
            if RegexMcdrc.search(line):
                line = RegexMcdrc.sub('CdrAgentInvoke %s ' % self.Mcdrc, line)
            lines.append(line)
        self.file.writelines(lines)
        
