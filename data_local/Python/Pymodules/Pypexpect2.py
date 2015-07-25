
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   ModuleName: Pypexpect2.py        #
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

class SshClientError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class pexpect2(builder):
    def __init__(self, config, Argv, loggerName='', *args, **kwargs):
        super(pexpect2, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

        self.OutputDir = self.config.get('OutputFilesFolder', False) or '/data_local/Python/.runner/'
        self.Commands = self.config.get('Commands', [])
        self.Argv = Argv
        self.DeletePrompt = self.config.get('DeletePrompt', 'no')
        self.DeletePromptRegEx = self.config.get('DeletePromptRegEx','input statement\.')
        self.CmdTimeOut = self.config.get('CmdTimeOut', 60)
        self.ignorecase = self.config.get('Ignorecase', False)
        self.runnerFileName = os.path.basename(sys.argv[1])
        self.output = ''
        self.tlog = '[ Pexpect: %s ]' % self.runnerFileName
        self.modes = {'password' : 'password_autontication',
                      'no_password' : 'no_password'}
       
        self.build_regex_list()
        if self.config.get('ExectionMode', 'False').lower() == self.modes['password']:
            self.password_autontication()
        elif self.config.get('ExectionMode', 'False').lower() == self.modes['no_password']:
            self.no_password_autontication() 

    def build_regex_list(self):
        self.userExpectList = self.config.get('RegexExpectList', {})
    
    def password_autontication(self):
        self.mode = self.modes['password']
        try:
            self.init_command = self.config.get('ConnectCommand')
            self.Password = Decrypt(self.config.get('Password', False)) 
        except:
            raise Exception, 'In "%s" mode: "ConnectCommand, Password" keys are required.' % self.mode

    def no_password_autontication(self):
        self.mode = self.modes['no_password']
        try:
            self.init_command = self.config.get('InitCommand')
        except:
            raise Exception, 'In "%s" mode: "InitCommand" key is required.' % self.mode  

    def __call__(self, *args, **kwargs):
        
        try:
            self._exec_command()
            self.deletePrompt()
        except:
            if getattr(self, 'pexpect2', False):
                self.pexpect2.close()
            print self.output
            raise 
        #if self.mode != 'db_config':
        #    print self.output

   
    def _exec_command(self):
        command = self.init_command
        pexpList, expList, sendList = self.buildExpectList()
        success = False
        self.pexpect2 = pexpect.spawn(command['cmd'], timeout=int(self.CmdTimeOut))
        self.set_ssh_logger()
        self.index = 0
        #firstPrompt = False
        count = 0
        while success != True and self.pexpect2.exitstatus == None:

            iRes = self.pexpect2.expect_list(expList)
            
            if iRes == (len(expList) - 3):
                self.set_ssh_logger()
                raise ConnectionTimeout, 'Connection timeout(%s) exceeded.' % self.timeOut
            # check if command Timeout return
            elif iRes == (len(expList) - 2):
                if command.get('ignore_timeout', False):
                    self.checkCommandStatus(command, ignore_timeout=True)
                    success = True
                else:
                    self.set_ssh_logger()
                    raise TimeoutException, '%s: Command timeout(%s) exceeded.' % \
                            (command['name'], command.get('time_out', '') or self.CmdTimeOut)
            # check if EOF return
            elif iRes == (len(expList) - 1):
                self.logger.debug('%s Got pexpect.EOF' % self.tlog)
                self.checkCommandStatus(command)
                success = True
            else:
                if type(sendList[iRes]) == list:
                    self.logger.info('%s Prompt Expect: %s Sending "%s"' % (self.tlog, pexpList[iRes], sendList[iRes][count]))
                    self.pexpect2.send(sendList[iRes][count])    
                    count = count + 1
                    self.set_ssh_logger()
                    if count >= len(sendList[iRes]):
                        count = 0
                else:
                    self.logger.info('%s Prompt Expect: %s Sending "%s"' % (self.tlog, pexpList[iRes], sendList[iRes]))
                    self.pexpect2.sendline(sendList[iRes])
                    self.set_ssh_logger()
            #   for i in range(0, len(sendList)):
            #        if iRes == i and sendList[i]:
            #            self.logger.info('%s Prompt Expect: %s Sending "%s"' % (self.tlog, pexpList[i], sendList[i]))
            #            self.pexpect2.sendline(sendList[i])
 


    def checkCommandStatus(self, command, ignore_timeout=False):
        self.pexpect2.close(force=True)
        self.close_connection()
        if ignore_timeout:
            self.output += '- Command timeout(%s) exceeded.\n' % \
                    command.get('time_out', '') or self.CmdTimeOut
        if not ignore_timeout and len(command.get('exit_status', [])):
            if self.pexpect2.exitstatus in command['exit_status']:
                self.output += '- Successfully match exit status "%s" in %s.\n' % \
                        (self.pexpect2.exitstatus, command['exit_status'])
                self.logger.error('%s Successfully match exit status "%s" in %s.' % \
                        (self.tlog, self.pexpect2.exitstatus, command['exit_status']))
            else:
                raise CommandError, '%s: Command exit with "%s", expected %s' % \
                        (command['name'], self.pexpect2.exitstatus, command['exit_status'])
        if command.get('cmd_output_regex', ''):
            self.dummy_fh.seek(0)
            output = unicode(self.dummy_fh.read(), encoding='utf-8',errors='ignore')
            if (self.ignorecase and re.search(command['cmd_output_regex'], output, re.I)) or \
                                    re.search(command['cmd_output_regex'], output):
                self.output += '- Successfully match command output with regex "%s".\n' % \
                                command['cmd_output_regex']
                self.logger.error('%s Successfully match command output with regex "%s".' \
                                % (self.tlog, command['cmd_output_regex']))
            else:
                raise CommandError, '%s: Command output did not match the given command output regex %s' \
                            % (command['name'], command['cmd_output_regex'])
        if not command.get('cmd_output_regex', '') and not len(command.get('exit_status', [])):
            self.logger.error('%s Skipping command exit_status/output check' % self.tlog)
            self.output += '- Skipping command exit_status/output check\n'

    def close_connection(self):
        self.dummy_fh.seek(0)
        self.output = ''.join(self.dummy_fh.readlines())
        if self.mode == self.modes['password']:
            self.output.replace(str(self.Password), '*' * len(self.Password))
        self.dummy_fh.seek(0)
                    
    def buildExpectList(self):
        expectList = []
        sendList = []
        pexpectList = []
        self.logger.info('Regex ignorecase: %s' % self.ignorecase)
        self.logger.info('Pexpect mode is: %s' % self.mode)
        if self.mode == self.modes['password']: 
            expectList.append(self.ignorecase and re.compile(self.password_prompt, re.I) or \
                    re.compile(self.password_prompt))
            pexpectList.append(self.password_prompt)
            sendList.append(self.Password)

        for pex in self.userExpectList:
            expectList.append(self.ignorecase and re.compile(pex['regex'], re.I) or \
                    re.compile(pex['regex']))
            pexpectList.append(pex['regex'])
            sendList.append(pex['send'])

        expectList.append(re.compile('Connection timed out'))
        expectList.append(pexpect.TIMEOUT)
        expectList.append(pexpect.EOF)
        pexpectList.append('Connection timed out')
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
        
        #for cmd in self.command_exec:
        #    self.output = self.output.replace('\n' + cmd + ';', '',)
        #self.output = self.output.replace('\nquit;', '',)
                
    def set_ssh_logger(self):
        self.logger.debug('Starting Pexpect logger')
        self.dummy_fh = cStringIO.StringIO()
        self.pexpect2.logfile = self.dummy_fh
