
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   ModuleName: Pymysql.py           #
######################################


from Pyfiledit import builder
from Pyconstruct.Pysec import *
#from copy import  deepcopy
import os, time, re ,sys, pexpect, datetime
import string, base64
import cStringIO
from pdb import set_trace as st

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

class pypexpect(builder):
    def __init__(self, config, Argv, loggerName='', *args, **kwargs):
        super(pypexpect, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

        self.runnerFileName = os.path.basename(sys.argv[1])
       # self.globalParams = self._set_global_params()
        self.pexParams = self.config.get('PexpectCommands',[])
        #for cmd in self.globalParams['commands']:
        #    self._update_command_params(cmd)
    
    
    def get_time(self):
        DateTimeFormat='%Y%m%d%H%M%S'
        CurrentTimeDate=datetime.now().strftime(DateTimeFormat)
        return CurrentTimeDate
    
    def runPexpect(self):
       
               
        self.logger.error('############ Pexpect Key Excahnge Start ############\n')
        self.logger.debug('Key Excahnge Params: %s ' % self.pexParams)
        #st()
        failed = False
        for px_cmd in self.pexParams:
            try:
                px = self._set_global_params()
                px.update(px_cmd)
                status = self._exec_command(px)
                if not failed and not status:
                    failed = True
                    
                self.pypexpect.close()
                self.deletePrompt(px)
                
                if len(px['output']):
                    out = '%s' % '\n'.join(px['output'])
                    print out
                self.logger.info(self.output)
            except:
                if getattr(self, 'pypexpect', False):
                    self.pypexpect.close()
                    
               
                if px.get('required', False):
                    self.logger.error(self.output)
                    raise
                self.logger.info(self.output)
                pass
        
        self.logger.error('############ Pexpect Key Excahnge Start ############\n')
        if failed:
            raise Exception, 'Test Key Exchange Falied: one or more test key exchange was failed, Please see the log file.'
                            
    def __call__(self, *args, **kwargs):
       
        try:
            self.runPexpect()
        except:
            #print self.output
            raise 

   
    def _exec_command(self, px):
      
        
        self.output = 'su - %s\n' % px['chuser']
        pexpList, expList, sendList = self.buildExpectList(px)
        success = False
        status = True
        self.pypexpect = pexpect.spawn('su - %s' % px['chuser'], timeout=int(px['time_out']))
        self.set_ssh_logger()
        self.index = 0
        first = True
     
        while success != True and self.pypexpect.exitstatus == None:
            iRes = self.pypexpect.expect_list(expList)
            if iRes == 0:
                # su command
                if first:
                    self.logger.info('Prompt Expect: %s Sending "%s"' % (pexpList[iRes], sendList[iRes]))
                    self.pypexpect.sendline(sendList[iRes])
                    first = False
                else:
                    self.pypexpect.sendcontrol('d')
            elif iRes == 1:
                # 'yes/no'
                self.logger.info('Prompt Expect: %s Sending "%s"' % (pexpList[iRes], sendList[iRes]))
                self.pypexpect.sendline(sendList[iRes])
               
            elif iRes == 2:
                if px.get('password'):
                    self.logger.info('Prompt Expect: %s Sending "%s"' % (pexpList[iRes], sendList[iRes]))
                    self.pypexpect.sendline(px['password'])
                else:
                # Password (no key exchange)
                    output_error = 'Test Key Exchange Failed: local user "%s" failed to connect %s@%s server - Reason: Password prompt appeared' % \
                                    (px['chuser'], px['remote_user'],px['remote_server'] )
                    
                    self.output += output_error
                    px['output'].append(output_error)
                    self.logger.error(output_error)        
                    if px['required']:
                        raise CommandError, 'Test Key Exchange Error: %s' %  output_error
                    else:
                        self.pypexpect.sendcontrol('c')
                    status = False
            
            elif iRes == 3:
                # Other command prompt
                
                                 
                if self.index < len(px['commands']):
                    self.logger.info('Prompt Expect: %s Sending "%s"' % \
                    (pexpList[iRes], px['commands'][self.index]))
                    self.pypexpect.sendline(px['commands'][self.index])
                    self.index += 1 
                else:
                    self.logger.info('Prompt Expect: %s Sending "%s"' % (pexpList[iRes], "exit"))
                    if px['exit_cmd']:
                        self.pypexpect.sendline(px['exit_cmd'])
                    else:
                        self.pypexpect.sendcontrol('d')
                        success_output = 'Test Key Exchnage Success: local user "%s" successfully connected to %s@%s remote server.' % \
                                 (px['chuser'], px['remote_user'], px['remote_server'])
                    
                        self.logger.error(success_output)
                        self.output += success_output
                        px['output'].append(success_output)
            elif iRes == 4:
                # Timeout
                status = False
                if  px['required']:
                    self.logger.error('Command Timeout Exception')
                    raise TimeoutException, 'Command timeout exceeded.'
                else:
                    success =  self.close_session(required=px.get('required', False))
                    error_timeout = 'Test Key Exchange Failed: local user "%s" failed to connect %s@%s server. - Reason: Command Timeout Exceeded' % \
                                    (px['chuser'], px['remote_user'],px['remote_server'] )
                    self.logger.error(error_timeout)
                    self.output += error_timeout
                    px['output'].append(error_timeout)
                    
                
            elif iRes == 5:
                # EOF
                success =  self.close_session(required=px.get('required', False)) 
                
        return status
          
    def close_session(self, required=False):
        self.close_connection()
        self.pypexpect.close()
        self.dummy_fh.close()
        if self.pypexpect.exitstatus == 0:
            success = True
        else:
            if required:
                raise Exception, 'Existing with exit_status: %s.' % self.pypexpect.exitstatus
            return True 
          

    def close_connection(self):
        self.dummy_fh.seek(0)
        self.output += ''.join(self.dummy_fh.readlines())
                    

    def buildExpectList(self, px_cmd):
        expectList = []
        sendList = []
        pexpectList = []
        self.ignorecase = px_cmd['ignorecase']
        expectList.append(self.ignorecase and re.compile('\[%s@[\s\t]*.*' % px_cmd['chuser'], re.I) or \
                          re.compile('\[%s@[\s\t]*.*' % px_cmd['chuser']))
        pexpectList.append('\[%s@[\s\t]*.*' % px_cmd['chuser'])
        sendList.append(px_cmd['init_cmd'])
         
        ssh_prompt = px_cmd['remote_user']
        self.logger.info('Regex ignorecase: %s' % self.ignorecase)
        expectList.append(self.ignorecase and re.compile('\(yes\/no\).', re.I) or \
                re.compile('\(yes\/no\).'))
        pexpectList.append('\(yes\/no\).')
        sendList.append('yes')
        
        expectList.append(self.ignorecase and re.compile('(Password|password):', re.I) or \
                re.compile('(Password|password):'))
        pexpectList.append('(Password|password):')
        sendList.append(px_cmd.get('password', ''))
        
        if ssh_prompt:
            expectList.append(self.ignorecase and re.compile('\[%s@[\s\t]*.*' % ssh_prompt, re.I) or \
                re.compile('\[%s@[\s\t]*.*' % ssh_prompt))
            pexpectList.append('\[%s@[\s\t]*.*' % ssh_prompt) 
            
        else:
            expectList.append(self.ignorecase and re.compile('.*', re.I) or \
                re.compile('.*'))
            pexpectList.append('.*')
          
        

        expectList.append(pexpect.TIMEOUT)
        expectList.append(pexpect.EOF)
        pexpectList.append(pexpect.TIMEOUT)
        pexpectList.append(pexpect.EOF)
        self.logger.info('expectList: %s' % pexpectList)
        self.logger.info('sendList: %s' % sendList)
        return pexpectList, expectList, sendList

    def deletePrompt(self, px):
        
        if px['delete_prompt']:
            temp = self.output.replace('\r\n', '')
            temp = self.output.replace('\r', '')
            temp = re.split('\[%s@[\s\t]*.*' % px['chuser'], temp)[1].strip()
            temp = re.split('Connection to %s closed.*' % px['remote_server'], temp)[0].strip()
            if px['print_cmd_out']:
                px['output'].append('CMD Ouput:\n%s' % temp)
                px['output'].append('')

        
    def set_ssh_logger(self):
        self.logger.debug('Starting Pexpect logger')
        self.dummy_fh = cStringIO.StringIO()
        self.pypexpect.logfile = self.dummy_fh

        
    def _set_global_params(self):
        globalParams = {}
        globalParams['init_cmd'] = self.config.get('init_cmd')
        globalParams['commands'] = self.config.get('commands', [])
        globalParams['required'] = self.config.get('required', False)
        globalParams['exit_cmd'] = self.config.get('exit_cmd')
        globalParams['time_out'] = self.config.get('time_out', 60)
        if self.config.get('password', False):
            globalParams['password'] = Decrypt(self.config.get('password'))
        globalParams['ignorecase'] = self.config.get('ignorecase', True)
        globalParams['delete_prompt'] = self.config.get('delete_prompt', True)
        globalParams['output'] = self.config.get('output', [])
        globalParams['print_cmd_out'] = self.config.get('print_cmd_out', False)
        globalParams['delete_prompt_regex'] = self.config.get('delete_prompt_regex', [])
        globalParams['cmd_regex'] = self.config.get('cmd_regex', [])
        globalParams['exit_status'] = self.config.get('exit_status', [0,])
       
        return globalParams
    
