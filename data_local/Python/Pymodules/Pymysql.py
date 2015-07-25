
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   ModuleName: Pymysql.py           #
######################################


from Pyfiledit import builder
from Pyconstruct.Pysec import *
import os, time, re ,sys, pexpect
import string, base64
import cStringIO

class AuthenticationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class TimeoutException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class UsageException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class CommandError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class mysql(builder):
    def __init__(self, config, Argv, loggerName='', *args, **kwargs):
        super(mysql, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

        self.OutputDir = self.config.get('OutputFilesFolder', False) or '/data_local/Python/.runner/'
        self.Commands = self.config.get('Commands', [])
        self.Argv = Argv
        self.DeletePrompt = self.config.get('DeletePrompt', 'yes')
        self.DeletePromptRegEx = self.config.get('DeletePromptRegEx','input statement\.')
        self.CmdTimeOut = self.config.get('CmdTimeOut', 60)
        self.ignorecase = self.config.get('Ignorecase', False)
        self.runnerFileName = os.path.basename(sys.argv[1])
        self.output = ''

        if self.config.get('ExectionMode', 'False').lower() == 'db_config':
            self.db_mode()
        elif self.config.get('ExectionMode', 'False').lower() == 'cluster_config':
            self.mcm_mode()

    def mcm_mode(self):
        self.mode = 'cluster_config'
        self.ConnectCommand = self.config.get('ConnectCommand')
        self.Password = Decrypt(self.config.get('Password', False)) or Decrypt('dIP8wj92y85mDdJys9CeNQ==') 
        self.setCommands()

    def db_mode(self):    
        self.mode = 'db_config'
        self.ConnectCommand = self.config.get('ConnectCommand')
        self.Password = Decrypt(self.config.get('Password', False)) or Decrypt('dIP8wj92y85mDdJys9CeNQ==') 

        self.setCommands()

    def __call__(self, *args, **kwargs):
        
        try:
            self._exec_command()
            self.deletePrompt()
        except:
            if getattr(self, 'mysql', False):
                #try:
                self.mysql.close()
                #except:
                #    pass
            print self.output
            raise 
        if self.mode != 'db_config':
            print self.output

   
    def _exec_command(self):
        if len(self.command_exec) == 0:
            raise Exception, 'No commands arguments were given.'

        pexpList, expList, sendList = self.buildExpectList()
        success = False
        self.mysql = pexpect.spawn(self.ConnectCommand, timeout=int(self.CmdTimeOut))
        self.set_ssh_logger()
        self.index = 0
        #firstPrompt = False
        while success != True and self.mysql.exitstatus == None:
            iRes = self.mysql.expect_list(expList)
            if iRes == 0:
                # Password
                self.mysql.sendline(sendList[0])
                self.set_ssh_logger() 
            elif iRes == 1:
                # Error
                self.close_connection()
                output_error = self.output.split('ERROR')[-1]
                if output_error.endswith('\r\n'):
                    output_error = output_error.split('\r\n')[0]
                len(self.command_exec) and self.logger.info('Command Error: %s' % self.command_exec[self.index -1])
                self.deletePrompt()
                raise CommandError, 'ERROR %s.' % output_error
            elif iRes == 2:
                # Other command prompt
                if self.index < len(self.command_exec):
                    self.logger.info('Prompt Expect: %s Sending "%s"' % \
                    (pexpList[iRes], self.command_exec[self.index]))
                    self.mysql.sendline(self.command_exec[self.index] + ';')
                    self.index += 1 
                else:
                    self.logger.info('Prompt Expect: %s Sending "%s"' % (pexpList[iRes], "exit"))
                    self.mysql.sendline('quit;')
            elif iRes == 3:
                # Timeout
                raise TimeoutException, 'Command timeout exceeded.'
            elif iRes == 4:
                # EOF 
                self.close_connection()
                self.mysql.close()
                self.dummy_fh.close()
                if self.mysql.exitstatus == 0:
                    success = True
                else:
                    raise Exception, 'Existing with exit_status: %s.' % self.mysql.exitstatus 

        self.lock_cluster()           
 
    def lock_cluster(self):
        if self.runnerFileName == 'mysql.py':
            if not os.path.isdir(self.OutputDir): os.mkdir(self.OutputDir, 0755)
            try:
                lock_file = open(os.path.join(self.OutputDir,'lock_cluster'), 'w')
                lock_file.write('Cluster was already created successfully.\n')
                lock_file.close()
            except:
                lock_file.close()
                raise Exception, 'Couln\'t create lock_cluster file under %s.' % self.OutputDir

    def close_connection(self):
        self.dummy_fh.seek(0)
        self.output = ''.join(self.dummy_fh.readlines())
        self.output.replace(str(self.Password), '*' * len(self.Password))
                    
    def setCommands(self):
        self.command_exec = []
        
        if self.Commands != 0:
            self.command_exec += self.Commands
            if len(self.Argv) > 0:
                for i in self.Argv:
                    cmd = i.strip()
                    if cmd: self.command_exec += [ cmd, ]

        if not len(self.command_exec):
            raise UsageException, 'Usage: ./runner.py <config file> <command, or list of commands> ' + \
            'Or The "Commands" value is empty or non exist in the config file.'
            self.logger.error('Usage: ./runner.py <config file> <command, or list of commands>')
            self.logger.error('Or The "Commands" value is empty or non exist in the config file.')

    def buildExpectList(self):
        expectList = []
        sendList = []
        pexpectList = []
        self.logger.info('Regex ignorecase: %s' % self.ignorecase)
        expectList.append(self.ignorecase and re.compile('^Enter password:', re.I) or \
                re.compile('^Enter password:'))
        pexpectList.append('^Enter password:')
        sendList.append(self.Password)
        
        expectList.append(self.ignorecase and re.compile('ERROR.*', re.I) or \
        re.compile('ERROR.*'))
        pexpectList.append('ERROR.*')


        expectList.append(self.ignorecase and re.compile('mcm\>', re.I) or \
                re.compile('mcm\>'))
        pexpectList.append('mcm/>')

        expectList.append(pexpect.TIMEOUT)
        expectList.append(pexpect.EOF)
        pexpectList.append(pexpect.TIMEOUT)
        pexpectList.append(pexpect.EOF)
        self.logger.info('expectList: %s' % pexpectList)
        self.logger.info('sendList: %s' % sendList)
        return pexpectList, expectList, sendList

    def deletePrompt(self):
        if self.DeletePrompt.lower() == 'yes':
            PromptRegEx = self.DeletePromptRegEx
            PromptRegExObj = re.compile(PromptRegEx)
            if PromptRegEx:
                tempOut = re.split(PromptRegEx, self.output)
                if len(tempOut) > 1:
                    self.output = tempOut[1]
                else:
                    tempOut = re.split('ERROR', self.output)
                    self.output = 'ERROR ' + tempOut[1]
        
        for cmd in self.command_exec:
            self.output = self.output.replace('\n' + cmd + ';', '',)
        self.output = self.output.replace('\nquit;', '',)
                
    def set_ssh_logger(self):
        self.logger.debug('Starting Pexpect logger')
        self.dummy_fh = cStringIO.StringIO()
        self.mysql.logfile = self.dummy_fh
