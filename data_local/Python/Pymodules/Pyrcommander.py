
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   Date: 07/03/11                   #
#   ModuleName: Pyrcommander.py       #
######################################


from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys, datetime
import string
from commands import getstatusoutput as getstatus
from Pydistribute import *
from threading import Thread, Semaphore
from copy import deepcopy
from dist_config import CONNECTION_MESSAGE, PASS_REGEX, SYSTEM_INI_REGEX,\
                                      SSH_DELIMITER, SSH, SU, SCP, AUTHENTICATION_SUCCEEDED, \
                                      SUDO_REGEX, SU_AUTHENTICATION_SUCCEEDED, DUMMY_REGEX, DUMMY_REGEX_SEND
def ThreadsDone(Threads):
    for thread in Threads:
        thread.join()
    return True

def ThreadsExitStatus(Threads):
    for thread in Threads:
        if not thread.ExitStatus:
            return False
    return True

class remote_commander(builder):

    def __init__(self, config, loggerName='', *args, **kwargs):
        super(remote_commander, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        self.SEM = self.config.get('SingleRemoteCommandExecution', '').lower() == 'yes' or False
        self.fileDir = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), '.runner')
        self.fileDir = self.config.get('OutputFilesFolder') or self.fileDir
        self.file_name = os.path.basename(sys.argv[1])
        if self.file_name.endswith('.pyc') or self.file_name.endswith('.pyo'):
            self.file_name = self.file_name[:-1]
        elif self.file_name.endswith('.conf'):
            pass
        elif config.get('installer', False):
            pass
        elif not self.file_name.endswith('.py'):
            raise Exception, 'Illegal conf file name, got \"%s\"' % self.file_name
        self.SuccessThreadsObj = []
        if not self.SEM:
            if os.path.isfile(os.path.join(self.fileDir, self.file_name)):
                try:
                    os.remove(os.path.join(self.fileDir, self.file_name))
                except:
                    raise Exception, 'Could not remove the %s file.' % (os.path.join(self.fileDir, self.file_name))

    def __call__(self, *args, **kwargs):
        self._build_iremote_commander()


    def _build_iremote_commander(self):
        iremote_commands = self.config.get('iRemoteCommander', [])
        if len(iremote_commands) == 0:
            print "\nNo iRemoteCommander was given, execution list is empty: []"
            self.logger.error("No iRemoteCommander was given, execution list is empty: []")
            return
        IP_Regex = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        self.regObj = re.compile(IP_Regex)
        self.globalParams = self._set_global_params()
        for cmd in self.globalParams['commands']:
            self._update_command_params(cmd)
        self.sections = [ s.keys()[0] for s in iremote_commands if len(s.keys()) == 1]
        self.logger.error("Section Order: %s" % self.sections)
        self.deployParams = {}
        self.AlreadyExecuted = []
        for section in iremote_commands:
            if len(section.keys()) != 1:
                continue
            section_name = section.keys()[0]
            self.deployParams[section_name] = {}
            for index, info in section[section.keys()[0]].iteritems():
                params = deepcopy(self.globalParams)
                params.update(info)
                params['section'] = section_name
                params['index'] = index
                if re.match(self.regObj, str(index)):
                    if not params.has_key('ip'): params['ip'] = index
                for cmd in params['commands']:
                    self._update_command_params(cmd)
                if not self.deployParams.has_key(section_name):
                    self.deployParams[section_name] = {}
                if not len(params['deploy_invoke_order']):
                    continue
                # Verify SEM if already executed successfully.
                if self.SEM:
                    if self._is_exec_success({section_name : index}):
                        self.SuccessThreadsObj.append({section_name : index})
                        hostname = info.get('hostname', '')
                        host = hostname and '%s-%s' % (info['ip'], hostname) or '%s' % info['ip']
                        self.logger.error("Skipping thread [%s: %s] due previously successfully execution." % (section_name, host))
                        th = '%s: %s -- Skipping thraed due previously successfully execution.' % (section_name, host) 
                        self.AlreadyExecuted.append(th)
                        continue
                params['commands'] = self._verify_deploy_invoke_order('execute', 'commands', params)
                params['files'] = self._verify_deploy_invoke_order('scpDistribute', 'files', params)
                params['get_files'] = self._verify_deploy_invoke_order('scpRemoteDistribute', 'get_files', params)
             	self.deployParams[section_name][index] = params
            self.logger.info("%s: %s" % (section_name, self.deployParams[section_name]))
        Threads = self._exec_deploy_params()
        if len(Threads) == 0:
            self.logger.error("All commands were previously executed successfully, nothing to do!")
            final_out = '\n'.join(self.AlreadyExecuted)
            if final_out: print '\n********* Execution Summaries *********\n'
            print "All commands were previously executed successfully, nothing to do!\n"
            if final_out: print final_out+'\n'
        else:
            _done = ThreadsDone(Threads)
            self._check_exec_status(Threads)

    def _is_exec_success(self, suceess_cmd):
        success = {}
        if os.path.isfile(os.path.join(self.fileDir, self.file_name)):
            try:
                execfile(os.path.join(self.fileDir, self.file_name), {}, success)
            except:
                try:
                    os.remove(os.path.join(self.fileDir, self.file_name))
                    return False
                except:
                    return False
            if success.has_key('success_threads'):
                if suceess_cmd in success['success_threads']:
                    return True
                return False
        return False
        
    def _check_exec_status(self, Threads):
        PrintSummary = self.config.get('printSummaries', False) 
        PrintToScreen = self.config.get('RemotePrintToScreen', False) 
        SuccessedThreads = []
        FailedThreads = []
        NotRunningThreads = []
        none_running_threads = False 
        if len(Threads) != len(self.AllThreads):
            none_running_threads = True
            for th in range(len(Threads), len(self.AllThreads)):
                 NotRunningThreads.append(self.AllThreads[th])
            self.logger.error("Not Executed Thraeds: %s" % NotRunningThreads)
            for i in range(0, len(NotRunningThreads)):
                NotRunningThreads[i] = NotRunningThreads[i] + '  -- Thread not executed'
     
        for T in Threads:
            server = T.hostname and '*' * 8 + ' %s-%s-%s ' % (T.section, T.ip, T.hostname) + '*' * 8 or \
            '*' * 8 + ' %s-%s ' % (T.section, T.ip) + '*' * 8
            sum_server = T.hostname and '%s-%s' % (T.ip, T.hostname) or '%s' % T.ip
            if T.printToScreen:
                server_out = '%s\n\n%s\n%s' % (server, not T.ExitStatus and T.exception or '', T.output)
                self.logger.error(server_out)
                print server_out
            if T.ExitStatus:
                success_out = '%s: %s -- Thread Succeed' % (T.section, sum_server)
                SuccessedThreads.append(success_out)
                self.SuccessThreadsObj.append({ T.section : T.index})
            else:
                falied_out = '%s: %s -- Thread Failed: %s' % (T.section, sum_server, T.exception)
                FailedThreads.append(falied_out)
        if PrintToScreen or PrintSummary:
            printThreads = (none_running_threads and self.AlreadyExecuted + SuccessedThreads + FailedThreads + NotRunningThreads) or \
                           (self.AlreadyExecuted + SuccessedThreads + FailedThreads)
            final_out = '\n'.join(printThreads)
            self.logger.error(final_out)
            if final_out: print '\n********* Execution Summaries *********\n'
            if final_out: print final_out+'\n'
            
        else:
            printThreads = (none_running_threads and self.AlreadyExecuted + FailedThreads + NotRunningThreads) or (self.AlreadyExecuted + FailedThreads)
            final_out = '\n'.join(printThreads)
            self.logger.error(final_out)
            if final_out: print '\n********* Execution Summaries *********\n'
            if final_out: print final_out+'\n'
        self.logger.error("\n\n********* Execution Summaries *********\n\n%s\n" % final_out)
        if self.SEM: self._save_success_threads_to_file()
        for T in Threads:
            if not T.ExitStatus:
                raise Exception, 'Remote Commander error, please view the %s log file.' \
                % self.config['LogFile'] 
                
                
    def _save_success_threads_to_file(self):
        if not os.path.isdir(self.fileDir): os.mkdir(self.fileDir, 0755)
        try:
            file = open(os.path.join(self.fileDir, self.file_name), 'w')
            file.write('success_threads = %s' % self.SuccessThreadsObj)
            file.close()
        except:
            self.logger.error("Could not open the %s file." % os.path.join(self.fileDir, self.file_name))
            print "Could not open the %s file." % os.path.join(self.fileDir, self.file_name)
            raise

    def _exec_deploy_params(self):
        Threads = []
        if not len(self.sections):
            self.logger.error("Section list is empty... nothing to do!")
            return []
        self.execution_mode = self.config.get('execution_mode', 'one_by_one')
        self.logger.error("Thread Mode: %s" % self.execution_mode)
        num_threads_sem = self.config.get('threads_sem', 100)
        threads_sem = Semaphore(int(num_threads_sem))
        if self.execution_mode == 'one_by_one':
            self.logger.error('Invoking Server By Server')
            threads_sem = Semaphore(1)
        elif self.execution_mode == 'section_by_section':
            self.logger.error('Invoking Section By Section')
        else:
            self.logger.error('Parallel invoking with Thread limit (%s)' % num_threads_sem)
        self.AllThreads = []
        for section in self.sections:
            if len(self.deployParams[section].keys()) == 0: continue
            soreted_keys = sorted(self.deployParams[section].keys())
            for key in soreted_keys:
                info = self.deployParams[section][key]
                hostname = info.get('hostname', '')
                host = hostname and '%s-%s' % (key, hostname) or '%s' % key
                th = '%s: %s' % (section, host)
                self.AllThreads.append(th)

        for section in self.sections:
            if len(self.deployParams[section].keys()) == 0: continue 
            soreted_keys = sorted(self.deployParams[section].keys())
            self.logger.error("%s Order keys: %s" %(section, soreted_keys))
            for key in soreted_keys:
                info = self.deployParams[section][key]
                info['threads_sem'] = threads_sem
                th = TransportThread(info)
                Threads.append(th)
                threads_sem.acquire()
                th.start()
                if self.execution_mode == 'one_by_one' and ThreadsDone(Threads) and not ThreadsExitStatus(Threads):
                    return Threads
            if self.execution_mode == 'section_by_section' and ThreadsDone(Threads) and not ThreadsExitStatus(Threads):
                return Threads
        return Threads 
         
    def _verify_deploy_invoke_order(self, mode, element, deployParams):
        if mode not in deployParams['deploy_invoke_order']:
            deployParams[element] = []
            return deployParams[element]
        return deployParams[element]

    def _update_command_params(self, command):
        if not command.has_key('cmd'):
            raise Exception, 'the "cmd" key is required in\ncommand=%s' % command
        if not command.has_key('name'): command['name'] =  command['cmd']
        if not command.has_key('exit_status'): command['exit_status'] = 0
        if not command.has_key('cmd_output_regex'): command['cmd_output_regex'] = ''
        if not command.has_key('ignore_timeout'): command['ignore_timeout'] = False
        if not command.has_key('cmd_regex'): command['cmd_regex'] = []
        if not command.has_key('time_out'): command['time_out'] = 60
        self.logger.debug('command=%s' % command)
        return command
        
    def _set_global_params(self):
        globalParams = {}
        globalParams['printToScreen'] = self.config.get('RemotePrintToScreen', False)
        globalParams['get_files'] = self.config.get('get_files', [])
        globalParams['files'] = self.config.get('files', [])
        globalParams['ip'] = self.config.get('dst_ip', False)
        globalParams['user'] = self.config.get('loginuser')
        globalParams['pw'] = self.config.get('login_user_pw')
        globalParams['chuser'] = self.config.get('chuser')
        globalParams['chpw'] = self.config.get('chuser_pw')
        globalParams['timeOut'] = self.config.get('timeOut', 60)
        globalParams['cmd_time_out'] = self.config.get('cmd_time_out', 60)
        globalParams['tmp_suffix'] = self.config.get('tmp_suffix', '.TMP')
        globalParams['index_suffix'] = self.config.get('index_suffix', '')
        globalParams['port'] = self.config.get('port', 22)
        globalParams['rsa'] = self.config.get('rsa',None)
        globalParams['dsa'] = self.config.get('dsa', '~/.ssh/id_dsa')
        globalParams['bufsize'] = self.config.get('bufsize', 8192)
        globalParams['backup_before_copy'] = self.config.get('backup_before_copy', False)
        globalParams['date_format'] = self.config.get('date_format', '%Y-%d-%m_%H-%M-%S')
        globalParams['logger_name'] = self.config.get('logger_name', '')
        globalParams['server_key'] = self.config.get('server_key', '')
        globalParams['section'] = self.config.get('section', 'RemoteCommander')
        globalParams['hostname'] = self.config.get('hostname', '')
        globalParams['deploy_invoke_order'] = self.config.get('deploy_invoke_order', [])
        globalParams['commands'] = self.config.get('commands', [])
        globalParams['ExitStatus'] = self.config.get('ExitStatus', 0) 
        globalParams['online_logger'] = False
        globalParams['auth_retries'] = self.config.get('auth_retries', 1) 
        globalParams['authentication_succeeded'] = self.config.get('authentication_succeeded', AUTHENTICATION_SUCCEEDED) 
        globalParams['su_authentication_succeeded'] = self.config.get('su_authentication_succeeded', SU_AUTHENTICATION_SUCCEEDED) 
        globalParams['authentication_command'] = self.config.get('authentication_command', '\echo') 
        globalParams['dummy_regex'] = self.config.get('dummy_regex', DUMMY_REGEX)
        globalParams['dummy_regex_send'] = self.config.get('dummy_regex_send', DUMMY_REGEX_SEND) 
        globalParams['signature_regex'] = self.config.get('signature_regex', '\(yes.no\).') 
        globalParams['pass_regex'] = self.config.get('pass_regex',PASS_REGEX) 
        globalParams['sudo_regex'] = self.config.get('sudo_regex',SUDO_REGEX) 
        globalParams['signature_answer'] = self.config.get('signature_answer', 'yes') 
        globalParams['su'] = self.config.get('su', SU) 
        return globalParams
