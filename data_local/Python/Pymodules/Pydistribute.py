
import paramiko, socket
import os, time, re ,sys, logging
from threading import Thread, Semaphore, BoundedSemaphore
from datetime import datetime
import pexpect
import  cStringIO
from glob import glob
from dist_config import SYSTEM_INI_REGEX, SSH_DELIMITER, SSH, SCP, QUIT_MODE, DEFAULT_UMASK,SYSTEM_INI_SECTION_REGEX, STATUS_CMD_FILE
import traceback

class AuthenticationError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class SftpClientError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class SshClientError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class ScpClientError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class ConnectionTimeout(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class TimeoutException(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value

class RegexError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return self.value


class TransportBaseThread(Thread):
    # Default Param can be over-ridden vi deployParam
    tmp_suffix = '.TMP'
    index_suffix = ''
    bufsize = 4096
    port = 22
    files = []
    get_files = []
    commands = []
    collects = []
    rsa = None
    dsa = None
    pw = None
    timeOut = 2
    date_format = '%Y-%d-%m_%H-%M-%S'
    threads_sem = False
    ExitStatus = False
    exception = ''
    output = ''
    server_key = ''
    section = ''
    online_logger = False
    logger_name = ''
    connection_message = 'Connection to %s closed.'
    authentication_succeeded = 'Authentication SshClient succeeded for %s'
    su_authentication_succeeded = 'All AdminTools SshClient Authentication Are Done'
    authentication_command = '\echo'
    dummy_regex = '__admintools_ignore_dummy_regex__'
    dummy_regex_send = 'admintools_regex_ignore'
    signature_regex = '\(yes\/no\).'
    pass_regex = '(Password|password):'
    sudo_regex = '\[sudo\] password for (\w+):'
    signature_answer = 'yes'
    su = '/bin/su -'
    sudo_command_regex = '^[\s\t]*\S*sudo[\s\t]+.+'
    quit_mode = QUIT_MODE and ['-q'] or []

    def __init__(self, deployParams, *args, **kwargs):
        self.deployParams = self.initParam(deployParams)
        self.logger = logging.getLogger(self.logger_name)
        Thread.__init__(self, name = '%s-%s' % (self.section, self.ip))
        self.tlog = '[Thread: %s' % self.getName() + ']'
        # Cover the option that files is only one hash
        if type(self.files) == dict:
            self.files = [self.files,]
        if type(self.commands) == dict:
            self.commands = [self.commands,]
        if type(self.collects) == dict:
            self.collects = [self.collects,]
        self.logger.info('%s online_logger: %s' % (self.tlog, self.online_logger))
        if self.online_logger:
            self.deploy = os.path.join(self.online_logger, 'deploy_%s-%s' % (self.hostname, self.ip))
            self.error = os.path.join(self.online_logger, 'error_%s-%s' % (self.hostname, self.ip))
            self.success = os.path.join(self.online_logger, 'success_%s-%s' % (self.hostname, self.ip))
            self.logger.info('%s DEPLOY: %s' % (self.tlog, self.deploy))
            self.logger.info('%s ERROR: %s' % (self.tlog, self.error))
            self.logger.info('%s SUCCESS: %s' % (self.tlog, self.success))

    def initParam(self, deployParams):
        for var, value in deployParams.iteritems():
            setattr(self, var, value)
        self.logger = logging.getLogger('')
        return deployParams

    def file_logger(self, text = False):
        if self.online_logger:
            try:
                _file = open(self.deploy, 'w')
                text and _file.writelines(text)
                _file.close()
            except:
                pass

class SftpBase(TransportBaseThread):

    def connect(self):
        self.logger.debug('%s USER(%s), RSA(%s), DSA(%s), PW(%s)' % (self.tlog, self.user, self.rsa,
                                                                     self.dsa, self.pw))
        if self.rsa and not self.pw:
            key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(self.rsa))
        elif self.dsa and not self.pw:
            key = paramiko.DSSKey.from_private_key_file(os.path.expanduser(self.dsa))
        elif not self.pw:
            raise AuthenticationError('No rsa/dsa/password were given')
        self.sock = socket.socket()
        self.sock.settimeout(self.timeOut)
        self.sock.connect((self.ip, self.port))
        self.t = paramiko.Transport(self.sock)
        if self.pw:
            self.t.connect(username=self.user, password=self.pw)
        else:
            self.t.connect(username=self.user, pkey=key)
        self.logger.debug("%s Connection to %s succeed" % (self.tlog, self.ip))

    def sftpConnect(self):
        self.sftp = paramiko.SFTPClient.from_transport(self.t)
        self.logger.info("%s Sftp Connection to %s succeed" % (self.tlog, self.ip))

    def disconnect(self):
        try:
            try:
                self.sftp.close()
            except: pass
            self.sock.close()
            self.t.close()
        except:
            self.logger.debug('%s %s' % (self.tlog, traceback.format_exc()))

    def filesSuffixSetup(self):
        # contact "." to suffixes if not exists. 
        if self.tmp_suffix and not self.tmp_suffix.startswith('.'):
            self.tmp_suffix = '.' + self.tmp_suffix
        if self.index_suffix and not self.index_suffix.startswith('.'):
            self.index_suffix = '.' + self.index_suffix
            
    def backup(self, rfile):
        try:
            self.sftp.stat(rfile)
        except IOError:
            return
        self.sftp.rename(rfile, self.backup_name(rfile))

    def backup_name(self, rfile):
        p = os.path.dirname(rfile)
        f = os.path.basename(rfile)
        now = datetime.now()
        f = '%s_%s' % (now.strftime(str(self.date_format)), f)
        self.output += '- Backup as %s\n' % f
        return os.path.join(p,f)

class SftpClient(SftpBase):

    def run(self):
        self.SftpCopy()
        if self.threads_sem:
            self.threads_sem.release()

    def SftpCopy(self):                        
        self.created_dirs = []
        self.logger.error('%s ##### Sftp distribute Start #####\n' % self.tlog)
        try:    
            if len(self.files):
                self.filesSuffixSetup()
            else:
                raise SftpClientError, 'No files were given'
            self.connect()
            self.sftpConnect()
            self.copyFiles()
            self.disconnect()
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.exception += 'SftpClient - %s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            self.disconnect()
        else:
            self.ExitStatus = True
        self.writeSftpStatusToLog()
        self.logger.error('%s ##### Sftp distribute End #####\n' % self.tlog)

    def writeSftpStatusToLog(self):
        remote_files = [ f['remote_file'] for f in self.files ]
        if self.ExitStatus:
            self.logger.error('%s Successfully distribute %s' % (self.tlog, remote_files))
        else:
            self.logger.error('%s Failed to distribute %s' % (self.tlog, remote_files))

    def create_dir(self, rfile):
        r_dirname = os.path.dirname(rfile['remote_file'])
        if r_dirname not in self.created_dirs:
            try:
                self.sftp.normalize(r_dirname)
            except IOError:
                self.logger.info('%s The %s dir does not exist on the remote server.' % (self.tlog, r_dirname))
                self.output += 'Creating %s dir on the remote server.\n' % r_dirname
                self.sftp.mkdir(r_dirname)
                self.sftp.chmod(path=r_dirname, mode=DEFAULT_UMASK)
                self.created_dirs.append(r_dirname)
                self.logger.info('%s Creating %s dir on the remote server.' % (self.tlog, r_dirname))

    def copyFiles(self):
            # looping over all file and copying the file.
            self.logger.debug('%s get_files: %s' % (self.tlog, self.files))
            for i in range(0, len(self.files)):
                self.create_dir(self.files[i])
                self.file_logger(text='Copying: %s' % os.path.basename(self.files[i]['remote_file']))
                self.output += 'Copying: %s to %s\n' % (self.files[i]['local_file'], self.files[i]['remote_file']) 
                if self.files[i].get('backup_before_copy', False):
                    self.backup(self.files[i]['remote_file'])
                elif self.tmp_suffix:
                    # Make sure the file does not exist on remote server due to paramiko limitation
                    try:
                        tmp = self.sftp.stat(self.files[i]['remote_file'])
                        self.sftp.remove(self.files[i]['remote_file'])
                        self.logger.debug('%s %s: Exists on remote server, Deleting the file!' % \
                                          (self.tlog, self.files[i]['remote_file']))
                    except:
                        self.logger.debug('%s %s: Does not exists on remote server, skipping deletion!' %\
                                          (self.tlog, self.files[i]['remote_file']))
                self.copy(self.files[i]['local_file'], self.files[i]['remote_file'])
                if self.files[i].get('uid', False) and self.files[i].get('gid', False):
                    self.output += '- Update UID(%s) and GID(%s)\n' % \
                             (self.files[i]['uid'], self.files[i]['gid'])
                    self.logger.info('%s Set UID(%s), GID(%s) to %s' % \
                            (self.tlog, self.files[i]['uid'], self.files[i]['gid'],
                                self.files[i]['remote_file']))
                    self.sftp.chown(path=self.files[i]['remote_file'], uid=self.files[i]['uid'],
                                    gid=self.files[i]['gid'])
                if self.files[i].get('mode', False):
                    self.output += '- Change mode(%s)\n' %  self.files[i]['mode']
                    self.logger.info('%s Change mode(%s) to %s' % \
                            (self.tlog, self.files[i]['mode'], self.files[i]['remote_file']))
                    self.sftp.chmod(path=self.files[i]['remote_file'], mode=self.files[i]['mode'])
                self.output += '- Successfully.\n\n'

    def copy(self, lfile, rfile):
        if self.tmp_suffix:
            suffix = self.tmp_suffix
        elif self.index_suffix:
            suffix = self.index_suffix
            self.logger.error('%s File index: %s%s' % (self.tlog, os.path.basename(rfile), suffix))
        else:
            suffix = ''
        self.logger.info('%s Copy: %s --> %s' % (self.tlog, lfile, rfile + suffix))
        if getattr(lfile, 'readlines', False):
            self.fh_copy(suffix, lfile, rfile)
        else:
            self.sftp.put(lfile, rfile + suffix)
        if self.tmp_suffix:
            self.logger.info('%s Rename: %s %s' % (self.tlog, rfile + suffix, rfile))
            self.sftp.rename(rfile + suffix, rfile)
            
    def fh_copy(self, suffix, lfile, rfile):
        self.logger.info('%s Copy via FH: %s %s' % (self.tlog, lfile, rfile + suffix))
        rfh = self.sftp.open(filename = rfile + suffix, mode = 'w', bufsize = self.bufsize)
        for line in lfile.readlines():
            rfh.write(line)
        rfh.close()
        lfile.close()

class SftpRemoteClient(SftpBase):
    
    def run(self):
        self.SftpRemoteCopy()
        if self.threads_sem:
            self.threads_sem.release()
    
    def SftpRemoteCopy(self):
        self.logger.error('%s ##### Remote Sftp Collect Start #####\n' % self.tlog)
        try:
            if len(self.get_files):
                self.filesSuffixSetup()
            else:
                raise SftpClientError, 'No files were given'
            self.connect()
            self.sftpConnect()
            self.collectFiles()
            self.disconnect()
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.exception += 'SftpClient - %s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            self.disconnect()
        else:
            self.ExitStatus = True
        self.writeSftpCollectStatusToLog()
        self.logger.error('%s ##### Remote Sftp Collect End #####\n' % self.tlog)
        
    def writeSftpCollectStatusToLog(self):
        succes_files = []
        failed_files = []
        for _file in self.get_files:
            if _file.has_key('regex_files'):
                for __file in _file['regex_files']:
                    if __file.get('exception', False):
                        failed_files.append(__file['remote_file'])
                    else:
                        succes_files.append(__file['remote_file'])
            else:
                if _file.get('exception', False):
                    failed_files.append(_file['remote_file'])
                else:
                    succes_files.append(_file['remote_file'])
        if len(succes_files):
            self.logger.error('%s Successfully collect %s' % (self.tlog, succes_files))
        if len(failed_files):
            self.logger.error('%s Failed to collect %s' % (self.tlog, failed_files))

    def collectByRegex(self, i):
        self.logger.info('%s Collecting Files by regex: %s' % (self.tlog, self.get_files[i]['remote_file']))
        try:
            self.sftp.normalize(self.get_files[i]['remote_dir'])
        except IOError:
            self.logger.error('%s %s: Directory does not exists on remote server' %\
                               (self.tlog, self.get_files[i]['remote_dir']))
            self.output += '%s: Directory does not exists on remote server' %\
                               (self.get_files[i]['remote_dir'])
            raise
        try:
            remote_regex = re.compile(self.get_files[i]['remote_file'])
        except:
            self.logger.error('%s "%s" bad regex format' %\
                               (self.tlog, self.get_files[i]['remote_file']))
            self.output += '"%s" bad regex format' %\
                               (self.get_files[i]['remote_file'])
            raise
        files = self.sftp.listdir(self.get_files[i]['remote_dir'])
        self.get_files[i]['regex_files'] = []
        self.logger.debug("%s All files on remote server under %s:\n%s" % \
                          (self.tlog, self.get_files[i]['remote_dir'], files))

        if self.get_files[i].get('use_local_fh', False):
            self.logger.debug('%s Will return dummy file handler for all files that match the %s regex.' % \
                              (self.tlog, self.get_files[i]['remote_file']))
        else:
            self.logger.debug('%s Will collect the file to local HD for all files that match the %s regex.' % \
                              (self.tlog, self.get_files[i]['remote_file']))

        for f in files:
            if remote_regex.search(f):
                self.logger.info('%s Successfully match regex "%s" with %s' % \
                    (self.tlog, self.get_files[i]['remote_file'], os.path.basename(f)))
                remote_file = os.path.join(self.get_files[i]['remote_dir'], f)
                if self.get_files[i].get('use_local_fh', False):
                    local_file = cStringIO.StringIO()
                else:
                    local_file = os.path.join(self.get_files[i]['local_dir'], os.path.basename(f))

                self.get_files[i]['regex_files'].append({'remote_file': remote_file, 'local_file': local_file })
        self.logger.info("%s Match Regex Files List: %s" % (self.tlog, self.get_files[i]['regex_files']))
        if not len(self.get_files[i]['regex_files']):
            if self.get_files[i].get('required', True):
                self.logger.error('%s No files were found on the remote server with "%s" regex under %s folder!' % \
                                  (self.tlog, self.get_files[i]['remote_file'], self.get_files[i]['remote_dir']))
                raise Exception, 'No files were found on the remote server with "%s" regex under %s folder!' % \
                                 (self.get_files[i]['remote_file'], self.get_files[i]['remote_dir'])
            else:
                self.get_files[i]['ignored'] = True
                self.logger.error('%s No files were found on the remote server with "%s" regex under %s folder!, Skipping sftp collect.' % \
                                  (self.tlog, self.get_files[i]['remote_file'], self.get_files[i]['remote_dir']))
                                 
        for f in self.get_files[i]['regex_files']:
            self.file_logger(text='Collecting: %s' % os.path.basename(f['remote_file']))
            self.output += 'Collecting: %s to %s\n' % (f['remote_file'], f['local_file'])
            if not hasattr(f['local_file'], 'write'):
                self.logger.error('%s Collecting: %s to %s' % (self.tlog, f['remote_file'], f['local_file']))
                if self.get_files[i].get('backup_before_copy', False):
                    self.local_backup(f['local_file'])

                if self.tmp_suffix:
                    # Make sure the file does not exist on remote server due to paramiko limitation
                    if os.path.isfile(f['local_file']):
                        os.remove(f['local_file'])
                        self.logger.debug('%s %s: Exists on local server, Deleting the file!' % \
                               (self.tlog, f['local_file']))
                    else:
                        self.logger.debug('%s %s: Does not exists on local server, skipping deletion!' %\
                                   (self.tlog, f['local_file']))
            self.remote_copy(f, f['remote_file'])
 
    def collectFiles(self):
        self.logger.debug('%s get_files: %s' % (self.tlog, self.get_files))
        for i in range(0, len(self.get_files)):
            try:
                if self.get_files[i].get('regex', False):
                    self.collectByRegex(i)
                else:
                    self.file_logger(text='Collecting: %s' % os.path.basename(self.get_files[i]['remote_file']))
                    str_local_file = (self.get_files[i].get('local_file', False) and \
                        not hasattr(self.get_files[i]['local_file'],'write') and 
                            self.get_files[i]['local_file']) or 'File Handler'

                    self.output += 'Collecting: %s to %s\n' % (self.get_files[i]['remote_file'], str_local_file)
                    
                    if self.get_files[i].get('local_file', False) and not hasattr(self.get_files[i]['local_file'], 'write'):
                        self.logger.error('%s Collecting: %s to %s' % (self.tlog, self.get_files[i]['remote_file'], 
                                                                       self.get_files[i]['local_file']))
                        if self.get_files[i].get('backup_before_copy', False):
                            self.local_backup(self.get_files[i]['local_file'])

                        if self.tmp_suffix:
                        # Make sure the file does not exist on remote server due to paramiko limitation
                            if os.path.isfile(self.get_files[i]['local_file']):
                                os.remove(self.get_files[i]['local_file'])
                                self.logger.debug('%s %s: Exists on local server, Deleting the file!' % \
                                           (self.tlog, self.get_files[i]['local_file']))
                            else:
                                self.logger.debug('%s %s: Does not exists on local server, skipping deletion!' %\
                                               (self.tlog, self.get_files[i]['local_file']))
                    elif not self.get_files[i].get('local_file', False):
                        self.get_files[i]['local_file'] = cStringIO.StringIO()

                    self.remote_copy(self.get_files[i], self.get_files[i]['remote_file'])
            except:
                self.logger.error('%s Required = %s, for %s file' %  \
                                 (self.tlog, self.get_files[i].get('required', True), self.get_files[i]['remote_file']) )
                if self.get_files[i].get('required', True):
                    raise
                else:
                    self.get_files[i]['ignored'] = True
                    self.get_files[i]['exception'] = 'SftpClient - %s: %s %s' % \
                                                     (sys.exc_info()[0], self.get_files[i]['remote_file'], sys.exc_info()[1])
                    self.output += '%s\n' % self.get_files[i]['exception']
                    self.logger.error('%s %s' % (self.tlog, self.get_files[i]['exception']))
                    self.logger.info('%s Skipping sftp collect for %s\n.' % \
                       (self.tlog, self.get_files[i]['remote_file']))
                    continue
 
    def remote_copy(self, lfile, rfile):
        if getattr(lfile['local_file'], 'write', False):
            self.remote_fh_copy(lfile, rfile)
        else:
            if self.tmp_suffix:
                suffix = self.tmp_suffix
            elif self.index_suffix:
                suffix = self.index_suffix
                self.logger.error('%s File index: %s%s' % (self.tlog, os.path.basename(lfile), suffix))
            else:
                suffix = ''

            self.logger.info('%s Collect: %s --> %s' % (self.tlog, lfile, rfile + suffix))
            self.sftp.get(rfile, lfile + suffix)
            if self.tmp_suffix:
                self.logger.info('%s Rename: %s %s' % (self.tlog, lfile  + suffix, lfile))
                os.rename(lfile  + suffix, lfile)

    def remote_fh_copy(self, lfile, rfile):
        self.logger.info('%s Collecting via FH: %s to %s' % (self.tlog, rfile, lfile))
        rfh = self.sftp.open(filename = rfile, mode = 'r', bufsize = self.bufsize)
        lfile['local_file'].seek(0)

        for line in rfh.readlines():
            lfile['local_file'].write(line)

        rfh.close()
        lfile['local_file'].seek(0)

class SshClient(TransportBaseThread):
    # FIXME - Remove default values to TransportBaseThread class 
    connectiom_attemps = 2
    cmd_time_out = 60
    ignorecase = True
    port = 22
    def run(self):
        if self.threads_sem:
            self.threads_sem.release()

    def Sshrun(self):
        commnads_status = {}
        self.logger.error('%s ##### Remote SSH Execution Start #####\n' % self.tlog)
        try:
            if not len(self.commands):
                raise SshClientError, 'No commands were given'
            self.logger.debug('%s Commnads: %s' % (self.tlog, self.commands))
            for cmd in self.commands:
                self.file_logger(cmd['name'])
                if not cmd.get('exit_status', '') and cmd.get('exit_status', '') != 0:
                    cmd['exit_status'] = []
                elif type(cmd.get('exit_status', '')) != list:
                    cmd['exit_status'] = [cmd['exit_status'],]
                self.logger.error('%s Execute:\n%s' % (self.tlog, cmd['cmd']))
                self.output += 'Execute: %s\n' % cmd['cmd']
                self.runCmd(cmd)
                self.readOutput()
                if cmd.get('save_cmd_status', False):
                    commnads_status[cmd['name']] = cmd['cmd']
                    self.write_cmd_status_to_files(commnads_status)
            self.ExitStatus = True
            self.logger.error('%s ##### Remote SSH Execution End #####\n' % self.tlog)
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.exception += 'SshClient - %s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            try:
                self.ssh.close()
            except: pass
            self.readOutput()

    def write_cmd_status_to_files(self, command):
        try:
            f = open(STATUS_CMD_FILE , 'w')
            f.write("status = %s" % command)
            f.close()
        except: pass
        
    def clear_regex_list(self, pexpList, expList, sendList, clear_list):
        for c in clear_list:
            expList[c] = self.compile_dummy_regex
            pexpList[c] = '%s replacing: %s' % (self.dummy_regex, pexpList[c])
            sendList[c] = self.dummy_regex_send
        return pexpList, expList, sendList
    
    def runCmd(self, command):
        cmd = SSH
        self.compile_dummy_regex = re.compile(self.dummy_regex)
        self.chuser = getattr(self, 'chuser', False)
        extend_args = command.get('extend_args', [])
        if type(extend_args) != list: extend_args = [extend_args]
        self.logger.info("%s extend_args: %s" % (self.tlog, extend_args))
        bashCmdArgs = extend_args + self.quit_mode + ['-p%s' % self.port, '%s@%s' % (self.user, self.ip), '-t', '-o',
                'ConnectTimeout=%s' % self.timeOut, '-o', 
                'ConnectionAttempts=%s' % self.connectiom_attemps]
        self.logger.debug('%s chuser: %s' % (self.tlog, getattr(self, 'chuser', 'No user were given')))
        self.logger.debug('%s chpw: %s' % (self.tlog, getattr(self, 'chpw', False)))
        try:
            self.authentication_succeeded = self.authentication_succeeded % self.user
        except:
            pass
        auth_command = '%s \"%s\"; ' % (self.authentication_command, self.authentication_succeeded)
        self.logger.info('%s AUTH_SUCCEEDED: %s' % (self.tlog, auth_command))
        if getattr(self, 'chuser', False):
            if not getattr(self, 'chpw', False):
                raise SshClientError, 'no password were given for chuser %s' % self.chuser
            su_auth_command = '%s \"%s\"; ' % (self.authentication_command, self.su_authentication_succeeded)
            self.logger.info('%s SU_AUTH_SUCCEEDED: %s' % (self.tlog, su_auth_command))
            bashCmdArgs.append('%s%s -c %s%s%s%s %s' % \
                    (auth_command, self.su, SSH_DELIMITER, su_auth_command, command['cmd'], SSH_DELIMITER, self.chuser))
        else:
            bashCmdArgs.append('%s%s' % (auth_command, command['cmd']))
        self.chpw = getattr(self, 'chpw', False)
        self.logger.info('%s CMD: %s Args: %s' % (self.tlog, cmd, bashCmdArgs))
        success = False
        sent_pw = False
        sent_sudo = False
        sent_chpw = False
        prompt_pw = False
        prompt_chpw = False
        blackList = []
        pexpList, expList, sendList = self.buildExpectList(command)
        if command.get('time_out', ''):
            self.ssh = pexpect.spawn(cmd, bashCmdArgs, timeout=int(command['time_out']))
        else:
            self.ssh = pexpect.spawn(cmd, bashCmdArgs, timeout=self.cmd_time_out)
        self.logger.debug('%s ssh: %s' % (self.tlog, self.ssh))
        self.set_ssh_logger()
        while success != True and self.ssh.exitstatus == None:
            iRes = self.ssh.expect_list(expList)
            self.logger.debug('%s ssh: %s' % (self.tlog, self.ssh))
            if iRes == 0 or iRes == 1:
                if expList[iRes] == self.compile_dummy_regex:
                    self.logger.debug('%s Dummy Regex(%s): "%s"' % (self.tlog, iRes, pexpList[iRes]))
                    continue
                self.logger.info('%s Ignore due to: "%s"' % (self.tlog, pexpList[iRes]))
                # Reset iRes and Auth (yes/no):
                clear_regex_list = [iRes, 2]
                if iRes == 0:
                    prompt_pw = True
                    if not self.chpw:
                        clear_regex_list.append(3)
                else:
                    prompt_chpw = True
                    clear_regex_list.append(3)
                pexpList, expList, sendList = self.clear_regex_list(pexpList, expList, sendList, clear_regex_list)
            elif iRes == 2:
                # Auth (yes/no):
                self.logger.info('%s Expect: %s Sending "%s"' % (self.tlog, pexpList[iRes], sendList[iRes]))
                self.ssh.sendline(sendList[iRes])
                self.set_ssh_logger()
            elif iRes == 3:
                # Password:
                if not prompt_pw and self.pw and not sent_pw:
                    # User Password first time:
                    self.logger.info('%s Expect: %s Sending "%s"' % \
                            (self.tlog, pexpList[iRes], sendList[iRes]))
                    self.ssh.sendline(sendList[iRes])
                    sent_pw = True
                elif prompt_pw and not prompt_chpw and self.chpw and not sent_chpw:
                    # ChUser Password (Second prompt):
                    self.logger.info('%s Expect(second prompt %s): Sending "%s"' % \
                                      (self.tlog, pexpList[iRes], self.chpw))
                    self.ssh.sendline(self.chpw)
                    sent_chpw = True
                else:
                    raise AuthenticationError, "Authentication failed"
                # Reset ssh logger to remove banner and pass
                self.set_ssh_logger()
            elif iRes == 4:
                # Sudo Password for user %u:
                if not re.search(self.sudo_command_regex, command['cmd']):
                    self.logger.info('%s SUDO Expect: "%s" Ignoring not sudo command' % \
                                     (self.tlog, pexpList[iRes]))
                    continue
                elif not sent_sudo:
                    try:
                        if self.chuser and self.ssh.match.group(1) == self.chuser:
                            self.logger.info('%s SUDO Expect: %s Sending "%s"' % \
                                     (self.tlog, pexpList[iRes], self.chpw))
                            self.ssh.sendline(self.chpw)
                        else:
                            raise
                    except:
                        self.logger.info('%s SUDO Expect: %s Sending "%s"' % \
                                     (self.tlog, pexpList[iRes], sendList[iRes]))
                        self.ssh.sendline(sendList[iRes])
                    sent_sudo = True
                    pexpList, expList, sendList = self.clear_regex_list(pexpList, expList, sendList, [0,1])
                    # Reset ssh logger to remove banner and pass
                    self.set_ssh_logger()
                else:
                    raise AuthenticationError, "Sudo Authentication failed"
            elif iRes == (len(expList) - 3): 
                self.set_ssh_logger()
                raise ConnectionTimeout, 'Connection timeout(%s) exceeded.' % self.timeOut
            # check if command Timeout return
            elif iRes == (len(expList) - 2): 
                if command.get('ignore_timeout', False):
                    self.checkCommandStatus(command, ignore_timeout=True)
                    success = True
                else:
                    raise TimeoutException, '%s: Command timeout(%s) exceeded.' % \
                            (command['name'], command.get('time_out', '') or self.cmd_time_out)
            # check if EOF return
            elif iRes == (len(expList) - 1):
                self.logger.debug('%s Got pexpect.EOF' % self.tlog)
                self.checkCommandStatus(command)
                success = True
            else:
                if expList[iRes] == self.compile_dummy_regex:
                    self.logger.debug('%s Dummy Regex(%s): "%s"' % (self.tlog, iRes, pexpList[iRes]))
                    continue
                self.logger.info('%s iRes(%s) Found: "%s"' % (self.tlog, iRes, pexpList[iRes]))
                if pexpList[iRes] in blackList:
                    raise RegexError, '%s: Expect regex "%s" found more than once' % \
                            (command['name'], pexpList[iRes])
                blackList.append(pexpList[iRes])
                for i in range(2, len(sendList)):
                    if iRes == i and sendList[i]:
                        self.logger.info('%s Sending "%s"' % (self.tlog, sendList[i]))
                        self.ssh.sendline(sendList[i])

    def set_ssh_logger(self):
        self.logger.debug('%s Starting Pexpect logger' % self.tlog)
        self.dummy_fh = cStringIO.StringIO()
        self.ssh.logfile = self.dummy_fh

    def checkCommandStatus(self, command, ignore_timeout=False):
        self.ssh.close(force=True)
        if ignore_timeout:
            self.output += '- Command timeout(%s) exceeded.\n' % \
                    command.get('time_out', '') or self.cmd_time_out
        if not ignore_timeout and len(command.get('exit_status', [])):
            if self.ssh.exitstatus in command['exit_status']:
                self.output += '- Successfully match exit status "%s" in %s.\n' % \
                        (self.ssh.exitstatus, command['exit_status'])
                self.logger.error('%s Successfully match exit status "%s" in %s.' % \
                        (self.tlog, self.ssh.exitstatus, command['exit_status']))
            else:
                raise SshClientError, '%s: Command exit with "%s", expected %s' % \
                        (command['name'], self.ssh.exitstatus, command['exit_status'])
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
                raise SshClientError, '%s: Command output did not match the given command output regex %s' \
                            % (command['name'], command['cmd_output_regex'])
        if not command.get('cmd_output_regex', '') and not len(command.get('exit_status', [])):
            self.logger.error('%s Skipping command exit_status/output check' % self.tlog)
            self.output += '- Skipping command exit_status/output check\n'

    def buildExpectList(self, cmd):
        expectList = []
        pexpectList = []
        sendList = []
        self.logger.info('%s Command Regex ignorecase: %s' % (self.tlog, self.ignorecase))
        # User AUTH_SECCUESS
        try:
            expectList.append(re.compile(self.authentication_succeeded % self.user))
            pexpectList.append(self.authentication_succeeded % self.user)
        except:
            expectList.append(re.compile(self.authentication_succeeded))
            pexpectList.append(self.authentication_succeeded)            
        sendList.append(self.dummy_regex_send)
        # User SU_AUTH_SECCUESS
        if self.chuser:
            expectList.append(re.compile(self.su_authentication_succeeded))
            pexpectList.append(self.su_authentication_succeeded)
        else:
            expectList.append(self.compile_dummy_regex)
            pexpectList.append(self.dummy_regex)
        sendList.append(self.dummy_regex_send)
        # iRes == 2 (Yes/No)
        expectList.append(self.ignorecase and re.compile(self.signature_regex, re.I) or \
                re.compile(self.signature_regex))
        pexpectList.append(self.signature_regex)
        sendList.append(self.signature_answer)
        # iRes == 3 (Password)
        expectList.append(self.ignorecase and re.compile(self.pass_regex) or \
                re.compile(self.pass_regex))
        pexpectList.append(self.pass_regex)
        sendList.append(self.pw)
        expectList.append(self.ignorecase and re.compile(self.sudo_regex) or \
                re.compile(self.sudo_regex))
        pexpectList.append(self.sudo_regex)
        sendList.append(self.pw)
        # System.ini key detect
        if self.server_key:
            self.logger.info('%s Setting server_key expect for system.ini identifier: %s' % \
                    (self.tlog, self.server_key))
            expectList.append(self.ignorecase and \
                    re.compile(SYSTEM_INI_REGEX, re.I) or \
                    re.compile(SYSTEM_INI_REGEX))
            pexpectList.append(SYSTEM_INI_REGEX)
            sendList.append(self.server_key)
        if self.section:
            self.logger.info('%s Setting section expect for system.ini identifier: %s' % \
                    (self.tlog, self.section))
            expectList.append(self.ignorecase and \
                    re.compile(SYSTEM_INI_SECTION_REGEX, re.I) or \
                    re.compile(SYSTEM_INI_SECTION_REGEX ))
            pexpectList.append(SYSTEM_INI_SECTION_REGEX )
            sendList.append(self.section)
        if type(cmd.get('cmd_regex', [])) == dict:
            cmd['cmd_regex'] = [cmd['cmd_regex'],]
        for regex in cmd.get('cmd_regex', []):
            for i in cmd['cmd_regex']:
                expectList.append(self.ignorecase and re.compile(i['regex']) or re.compile(i['regex']))
                pexpectList.append(i['regex'])
                sendList.append(i['send'])
        # Timeout and EOF
        expectList.append(re.compile('Connection timed out'))
        expectList.append(pexpect.TIMEOUT)
        expectList.append(pexpect.EOF)
        pexpectList.append(pexpect.TIMEOUT)
        pexpectList.append(pexpect.EOF)
        self.logger.info('%s Command expectList: %s' % (self.tlog, pexpectList))
        self.logger.info('%s Command sendList: %s' % (self.tlog, sendList))
        return pexpectList, expectList, sendList

    def readOutput(self):
        if getattr(self, 'dummy_fh', None) is None:
            return
        self.dummy_fh.seek(0)
        lines = unicode(self.dummy_fh.read(), encoding='utf-8',errors='ignore')
        # Removing authenticated succeeded:
        if self.chuser:
            authentication_succeeded = self.su_authentication_succeeded
        else:
            try:
                authentication_succeeded = self.authentication_succeeded % self.user
            except:
                authentication_succeeded = self.authentication_succeeded
        prompt_position = lines.find(authentication_succeeded)
        if prompt_position > -1:
            self.logger.debug('%s Removing Prompt/Banner from output' % self.tlog)
            lines = lines[prompt_position + len(authentication_succeeded) + 1:]
        # Connection closed removal:
        if getattr(self, 'connection_message', False) and self.connection_message:
            self.logger.debug('%s Removing close connection message from output' % self.tlog)
            try:
                lines = lines.replace(self.connection_message % self.ip, '')
            except:
                self.logger.debug('Failed to Remove "close connection message" from output' % self.tlog)
        self.dummy_fh.close()
        self.output += '- Command Output:\n%s\n\n' % lines.strip()
        self.logger.error('%s Command Output: %s' % (self.tlog, lines.strip()))

    def Scprun(self):
        self.logger.error('%s SCP Client Start' % self.tlog)
        try:
            if not len(self.files):
                raise ScpClientError, 'No files were given'
            # looping over all file and copying the file.
            self.logger.debug('%s files: %s' % (self.tlog, self.files))
            for i in range(0, len(self.files)):
                self.file_logger(text='Copying: %s' % os.path.basename(self.files[i]['remote_file']))
                self.output += 'Copying: %s to %s\n' % (self.files[i]['local_file'], self.files[i]['remote_file'])
                self.files[i]['exit_status'] = [0]
                extend_args = self.files[i].get('extend_args', [])
                if type(extend_args) != list: extend_args = [extend_args]
                self.scpCopy(self.files[i]['local_file'], self.files[i]['remote_file'],
                             self.files[i].get('time_out', self.cmd_time_out), extend_args)
                try:
                    self.dummy_fh.close()
                except: pass
            self.ExitStatus = True
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.exception += 'ScpClient - %s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            try:
                self.scp.close()
            except: pass
            self.readOutput()

    def ScpRtlrun(self):
        self.logger.error('%s SCP Client Start' % self.tlog)
        try:
            if not len(self.get_files):
                raise ScpClientError, 'No files were given'
            # looping over all file and copying the file.
            self.logger.debug('%s get_files: %s' % (self.tlog, self.get_files))
            for i in range(0, len(self.get_files)):
                self.file_logger(text='Remote Copy: %s' % os.path.basename(self.get_files[i]['remote_file']))
                self.output += 'Remote Copy: %s to %s\n' % (self.get_files[i]['remote_file'], self.get_files[i]['local_file'])
                self.get_files[i]['exit_status'] = [0]
                extend_args = self.get_files[i].get('extend_args', [])
                if type(extend_args) != list: extend_args = [extend_args]
                self.scpCopy(self.get_files[i]['local_file'], self.get_files[i]['remote_file'], 
                             self.get_files[i].get('time_out', self.cmd_time_out), extend_args, True)
                try:
                    self.dummy_fh.close()
                except: pass
            self.ExitStatus = True
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.exception += 'ScpClient - %s: %s\n' % (sys.exc_info()[0], sys.exc_info()[1])
            try:
                self.scp.close()
            except: pass
            self.readOutput()
            
    def scpCopy(self, lfile, rfile, copy_time_out, extend_args, rtl=False):
        cmd = SCP
        self.logger.info("%s extend_args: %s" % (self.tlog, extend_args))
        if rtl:
            bashCmdArgs = extend_args + self.quit_mode + ['-P %s' % self.port, '-o', 'ConnectTimeout=%s' % self.timeOut,
                '-o', 'ConnectionAttempts=%s' % self.connectiom_attemps,
                '%s@%s:%s' % (self.user, self.ip, rfile), lfile]
        else:
            bashCmdArgs = extend_args + self.quit_mode + ['-P %s' % self.port, '-o', 'ConnectTimeout=%s' % self.timeOut, 
                '-o', 'ConnectionAttempts=%s' % self.connectiom_attemps,
                lfile, '%s@%s:%s' % (self.user, self.ip, rfile)]
        self.logger.info('%s CMD: %s Args: %s' % (self.tlog, cmd, bashCmdArgs))
        success = False
        sent_pw = False
        pexpList, expList, sendList = self.buildScpExpectList()
        self.scp = pexpect.spawn(cmd, bashCmdArgs, timeout=copy_time_out)
        self.logger.debug('%s scp: %s' % (self.tlog, self.scp))
        self.set_scp_logger()
        while success != True and self.scp.exitstatus == None:
            iRes = self.scp.expect_list(expList)
            if iRes == 0:
                # Auth (yes/no):
                self.logger.info('%s Expect: %s Sending "%s"' % (self.tlog, pexpList[iRes], sendList[iRes]))
                self.scp.sendline(sendList[iRes])
                self.set_scp_logger()
            elif iRes == 1:
                # Password:
                if not sent_pw:
                    self.logger.info('%s Expect: %s Sending "%s"' % \
                            (self.tlog, pexpList[iRes], sendList[iRes]))
                    self.scp.sendline(sendList[1])
                    sent_pw += 1
                else:
                    raise AuthenticationError, "Authentication failed"
                # Reset scp logger to remove bunner and pass
                self.set_scp_logger()
            elif iRes == 2:
                self.set_scp_logger()
                raise ConnectionTimeout, 'Connection timeout(%s) exceeded.' % self.timeOut
            # check if command Timeout return
            elif iRes == 3: 
                raise TimeoutException, '%s: scp timeout(%s) exceeded.' % \
                        (lfile, self.cmd_time_out)
            # check if EOF return
            elif iRes == 4:
                self.logger.debug('%s SCP pexpect.EOF' % self.tlog)
                self.checkScpStatus(lfile, rfile, rtl)
                success = True

    def checkScpStatus(self, lfile, rfile, rtl=False):
        self.scp.close(force=True)
        if self.scp.exitstatus == 0:
            self.output += '- Successfully.\n\n'
            if rtl:
                self.logger.error('%s Successfully Remote scp: %s to %s' % (self.tlog, rfile, lfile))
            else:
                self.logger.error('%s Successfully scp: %s to %s' % (self.tlog, lfile, rfile))
        else:
            if rtl:
                raise ScpClientError, 'Failed to remote copy: %s to %s' % (rfile, lfile)
            else:
                raise ScpClientError, 'Failed to copy: %s to %s' % (lfile, rfile)

    def buildScpExpectList(self):
        expectList = []
        pexpectList = []
        sendList = []
        self.logger.info('%s SCP Regex ignorecase: %s' % (self.tlog, self.ignorecase))
        # iRes == 0 (Yes/No)
        expectList.append(self.ignorecase and re.compile(self.signature_regex, re.I) or \
                re.compile(self.signature_regex))
        pexpectList.append(self.signature_regex)
        sendList.append(self.signature_answer)
        # iRes == 1 (Password)
        expectList.append(self.ignorecase and re.compile(self.pass_regex) or \
                re.compile(self.pass_regex))
        pexpectList.append(self.pass_regex)
        sendList.append(self.pw)
        # iRes == 2 (Connection Timeout)
        expectList.append(re.compile('Connection timed out'))
        # iRes == 3 (TIMEOUT)
        expectList.append(pexpect.TIMEOUT)
        # iRes == 4 (EOF)
        expectList.append(pexpect.EOF)
        pexpectList.append(pexpect.TIMEOUT)
        pexpectList.append(pexpect.EOF)
        self.logger.info('%s SCP expectList: %s' % (self.tlog, pexpectList))
        self.logger.info('%s SCP sendList: %s' % (self.tlog, sendList))
        return pexpectList, expectList, sendList

    def set_scp_logger(self):
        self.logger.debug('%s Starting SCP Pexpect logger' % self.tlog)
        self.dummy_fh = cStringIO.StringIO()
        self.scp.logfile = self.dummy_fh

# Main Class that invoke the all deploy execution.
class TransportThread(SshClient, SftpClient, SftpRemoteClient):

    deploy_invoke_order = ['distribute', 'execute']

    def rename_log(self):
        try:
            _file = self.success
            if not self.ExitStatus:
                _file = self.error
            if not os.path.isfile(self.deploy):
                f = open(_file, 'w')
                if not self.ExitStatus and self.exception:
                    f.write(self.exception)
                f.close()
            else:
                os.rename(self.deploy, _file)
                if not self.ExitStatus and self.exception:
                    f = open(_file, 'w')
                    f.write(self.exception)
                    f.close()
        except: pass

    def run(self):
        self.logger.error('%s Invoke order: %s' % (self.tlog, self.deploy_invoke_order))
        invoke_order = {'distribute' : {'elements' : self.files,
                                         'method' : self.SftpCopy},
                        'collect' : {'elements' : self.get_files,
                                     'method' : self.SftpRemoteCopy },
                        'execute' : {'elements' : self.commands,
                                     'method' :  self.Sshrun},
                        'scpDistribute' : {'elements' : self.files,
                                           'method' : self.Scprun},
                        'scpRemoteDistribute' : {'elements' : self.get_files,
                                           'method' : self.ScpRtlrun},
                        'scpCollect' : {'elements' : self.get_files,
                                           'method' : self.ScpRtlrun},
                        }
        for invoke in self.deploy_invoke_order:
            if self.deploy_invoke_order.index(invoke) > 0 and not self.ExitStatus:
                prev = self.deploy_invoke_order[self.deploy_invoke_order.index(invoke) - 1]
                self.logger.error('%s Failed on previews invoker "%s", canceling "%s" invoker and existing.'\
                        % (self.tlog, prev, invoke))
                break
            self.logger.debug('%s Elements(%s): %s' % (self.tlog, invoke, \
                    invoke_order[invoke]['elements']))
            if len(invoke_order[invoke]['elements']):
                self.logger.info('%s Running: %s(%s)' % \
                        (self.tlog, invoke, invoke_order[invoke]['method']))
                invoke_order[invoke]['method']()
            else:
                self.logger.info('%s No elemets for : %s(%s)' % \
                        (self.tlog, invoke, invoke_order[invoke]['method'].__name__))
                self.exception += 'No elemets for : %s(%s)\n' % \
                        (invoke, invoke_order[invoke]['method'].__name__)
        self.online_logger and self.rename_log()
        self.logger.info('%s Done with deploy invokers' % self.tlog)
        if self.threads_sem:
            self.threads_sem.release()
