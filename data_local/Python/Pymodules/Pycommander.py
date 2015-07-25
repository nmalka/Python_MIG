
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   Ver: 5.5.5                       #
#   Date: 15/07/10                   #
#   ModuleName: Pycommander.py       #
######################################


from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys
from pdb import set_trace as st
import string
from commands import getstatusoutput as getstatus

 
class icommander(builder):

    def __init__(self, config, loggerName='', *args, **kwargs):
        super(icommander, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        self.icommands = self.config.get('iCommander', [])
        self.AppendToLogger = False
        if self.config.get('AppendToLogger',False) and not self.config.get('printToScreen', False):
            self.AppendToLogger = self.config.get('AppendToLogger',False)
            self.logger.info("AppendToLogger=%s Log: \"%s\"" % (self.AppendToLogger, self.log))

    def __call__(self, *args, **kwargs):
        if len(self.icommands) == 0:
            print "\nNo iCommander was given, execution list is empty: []"
            self.logger.error("No iCommander was given, execution list is empty: []")
            return
        self.SEM = False
        self.successCommands = []
        self.ignoreCommands = []
        self.filesDir = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), '.runner')
        if self.config.get('SingleCommandExecution', False) and self.config['SingleCommandExecution'].lower() == 'yes':
            self.SEM = True
            self.OutputDir = self.config.get('OutputFilesFolder') or self.filesDir
            self.fname_success = os.path.basename(sys.argv[1])[:-3]  + '_commander'
        if self.SEM:
            if not os.path.isdir(self.OutputDir): os.mkdir(self.OutputDir, 0755)            
            if os.path.isfile(os.path.join(self.OutputDir, self.fname_success)):
                try:
                    file = open(os.path.join(self.OutputDir, self.fname_success), 'r')
                    lines = file.read()
                    lines = [ i.strip('\n') for i in lines.split('@' * 10) if i and i != '\n']
                    for command in lines:
                        self.ignoreCommands.append(command)
                    file.close()
                except:
                    self.logger.error("Could not open the %s file." % os.path.join(self.OutputDir, self.fname_success))
                    print "Could not open the %s file." % os.path.join(self.OutputDir, self.fname_success)
                    file.close()
                    raise
                os.remove(os.path.join(self.OutputDir, self.fname_success))
    
        #self.logger.info('\n'.join(self.icommands[len(self.ignoreCommands):]))
        if len(self.icommands) == len(self.ignoreCommands): self.dummy = True
        else: self.dummy = False
         
        for _cmd in [ c for c in self.icommands if c ]:
            exit_status_list = [0,]
            if type(_cmd) == dict:
                cmd = _cmd['cmd']
                exit_status_list += _cmd['exit_status']
            else:
                cmd = _cmd

            if self.SEM:
                if cmd.__repr__() in self.ignoreCommands:
                    self.successCommands.append(cmd)
                    self.logger.error("Skipping %s command, due previously execution." % cmd.__repr__())
                    self._buildFile()
                    continue
                else:
                    self.dummy = False
            self.logger.error('Execute: %s' % cmd.__repr__())
            try:
                self._exec_command(cmd, exit_status_list)
                if self.SEM:
                    self.successCommands.append(cmd)
                    self._buildFile()
            except:
                if self.SEM:
                    self._buildFile()
                raise
        if self.SEM:
            self._buildFile(complete=True)
    def _buildFile(self, complete=False):
        if not complete:
            try:
                file = open(os.path.join(self.OutputDir, self.fname_success), 'w')
                for c in self.successCommands:
                    file.write(c.__repr__() + '\n')
                    file.write('@' * 10 + '\n')
                file.close()
            except:
                self.logger.error("Could not create %s file under %s." % (self.fname_success, self.OutputDir))
                print "Could not create %s file under %s." % (self.fname_success, self.OutputDir)
                file.close()
        else:
            if self.dummy:
                self.logger.error("All iCommander commands were previously executed successfully!")
                if self.config['Mode'] == 'icommander':
                    print "\nAll iCommander commands were previously executed successfully!"
                  
    def _exec_command(self, cmd, exit_status_list=[0,]):
        if self.AppendToLogger:
            status = getstatus('%s %s' % (cmd, self.log))
        else:
            status = getstatus(cmd)
        if not status[0] in exit_status_list:
            self.logger.error('Faild Executed: %s' % cmd.__repr__())
            if status[1]: 
                self.logger.error('Command Output: %s' % status[1])
                raise Exception, 'Faild Executed: %s\nCommand Output: %s' % (cmd.__repr__(), status[1])
            else:
                raise Exception, 'Faild Executed: %s' % (cmd.__repr__())
        else:
            if status[1]:
                if self.config.get('printToScreen', False):
                    if cmd.startswith('echo'):
                        print '\n%s' % status[1]
                    else: 
                        print '\nExecute: %s\n%s' % (cmd.__repr__(), status[1])
                    if self.config.get('Flush', False):
                        sys.stdout.flush()
                self.logger.error('\n%s' % status[1])
            self.logger.error('Succssfully executed: %s' % cmd.__repr__())
