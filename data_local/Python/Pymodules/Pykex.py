
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Ver: 4.8                     #
#   Date: 13/07/09               #
#   ModuleNmae: Pykex.py         #
##################################

from Pyfiledit import builder
from Pydecorators import *
from Pynet import *
import os, time, re ,sys, string
from Pyconstruct.Pysec import *
import pexpect
import traceback

def UserInfo(users):
    UsersInfo = {}
    f = open('/etc/passwd')
    lines = f.readlines()
    f.close()
    for user in users:
        for line in lines:
            if line.find(user+':') == 0:
                UsersInfo[user] = (re.split(':', line)[2], re.split(':', line)[3]), \
                        re.split(':', line)[-2].strip()
    return UsersInfo

def DigHostsIPs(reg, file='/etc/hosts', mode='by_line'):
    import re
    f = open(file)
    lines = f.readlines()
    f.close()
    r_line = re.compile('^[\s\t]*(:?\d{1,3}\.){3}(:?\d{1,3})[\s\t]+.*?' + reg, re.I)
    r_alias = re.compile(reg, re.I)
    IPHost = {}
    for line in lines:
        line =  line.split('#',1)[0].strip()
        if mode == 'by_alias':
            if line:
                split_line = re.split('[\t\s]', line)
                for host_alias in split_line:
                    if r_alias.match(host_alias):
                        IPHost[re.split(r'[\s\t]+', line, 1)[0]] = re.split(r'[\s\t]+', line, 1)[1]
        else:
            if r_line.search(line):
                IPHost[re.split(r'[\s\t]+', line, 1)[0]] = re.split(r'[\s\t]+', line, 1)[1]
    if len(IPHost.keys()) == 0:
        raise Exception, 'RegEx did NOT match \'%s\' in %s file, can NOT get the relevat IP' % (reg ,file)
    else:
        return IPHost


class kex(builder):
    def __call__(self):
        self._servers()

    def _servers(self):
        self.serverList = {}
        tmpList = []
        for key, val in self.config.iteritems():
            if key.startswith('$') and val:
                val = val.split(':', 2)
                if val.__len__() == 1:
                    continue
                local = re.split(r',[\s\t]*', val[0])
                remote = re.split(r',[\s\t]*', val[1])
                if re.match('^(:?\d{1,3}\.){3}(:?\d{1,3})', val[2]):
                    servers = { val[2] : val[2] } 
                else:
                    try:
                        servers = DigHostsIPs(reg=val[2], file='/etc/hosts')
                    except Exception:
                        if self.config.get('RegexRequired', False):
                            raise
                        self.logger.error('%s, Skipping ...' % sys.exc_info()[1])
                        continue
                    for k, v in servers.iteritems():
                        if re.search('[\t\s]+', v):
                            servers[k] = re.search(val[2],v).group().strip()
                            self.logger.error('Key-exchange will use \"%s\" alias for %s server'\
											% (servers[k], k))
                self.serverList[key] = [local, remote, servers]

class key_exchange(kex):
    def __init__(self, config, componentID, Argv, *args, **kwargs):
        super(key_exchange, self).__init__(config=config, componentID=componentID, Argv=Argv, 
                *args, **kwargs)
        self.Argv = Argv
        if self.config.get('_', False):
            self.change_user = self.config['_'](self.config['Section'], 'change_user', False) \
                                or self.config['_']('RUNNER', 'change_user', False) or 'root'
        else:
           self.change_user = self.config.get('ChangeUser', 'root')
        try:
            if self.config['LogInUser'] == self.change_user:
                if not self.config.get('ForceSilentKex', False) and len(Argv) == 1:
                    self.loginPw = self.rootPW = Argv[0]
                else:
                    self.loginPw = self.rootPW = self.config['_'](self.config['Section'], 'login_user_pw', False) \
                                  or self.config['_']('RUNNER', 'login_user_pw')
                    if self.config['_']('RUNNER', 'secure_runner', False).lower() == 'yes':
                        self.loginPw = self.rootPW = Decrypt(self.rootPW)
            else:
                if not self.config.get('ForceSilentKex', False) and len(Argv) == 2:
                    self.loginPw = Argv[0] 
                else: 
                    self.loginPw = self.config['_'](self.config['Section'], 'login_user_pw', False) \
                                   or self.config['_']('RUNNER', 'login_user_pw')
                    if self.config['_']('RUNNER', 'secure_runner', False).lower() == 'yes':
                        self.loginPw = Decrypt(self.loginPw)
                if not self.config.get('ForceSilentKex', False) and len(Argv) == 2:
                    self.rootPW = Argv[1]
                else:
                    self.rootPW = self.config['_'](self.config['Section'], 'change_user_pw', False) \
                                  or self.config['_']('RUNNER', 'change_user_pw')
                    if self.config['_']('RUNNER', 'secure_runner', False).lower() == 'yes':
                        self.rootPW = Decrypt(self.rootPW)
        except:
            if self.config['LogInUser'] == self.change_user:
                raise Exception, 'Usage: ./runner.py <Key excange conf file> <root password>\n' + \
                                 'Or add to "RUNNER" section the parameter:\n' + \
                                 '  login_user_pw = <root password> in system.ini file\n' + \
                                 '  secure_runner = yes - for encrypted passwords or omit parameter for plain text passwords'
            else:
                raise Exception, '\nUsage: ./runner.py <Key excange conf file> <LogInUser password> <root password>\n' + \
                                 'Or add to "RUNNER" section the parameters:\n' + \
                                 '  login_user_pw = <LogInUser passwor>\n' + \
                                 '  change_user_pw = <root password> in system.ini file\n' + \
                                 '  secure_runner = yes - for encrypted passowds or omit parameter for plain text passwords'
    def __call__(self):
        super(key_exchange, self).__call__()
        self.send_pub()
    def send_pub(self):
        loginUser = self.config['LogInUser']
        keyType = self.config['KeyType']
        userPromptRegEx = self.config.get('userPromptRegEx', '(:?\-bash\-\d+?\.\d+?\$)|(:?\[%s@.*\])')
        for id, info in self.serverList.iteritems():
            self.logger.info('Working on parametter: %s' % id)
            localUsersInfo = UserInfo(info[0])
            RemoteUserInfo = info[1]
            HostInfo = info[2]
            self.logger.info('Remote servers for %s are: %s' % (id, HostInfo.keys()))
            for ip, name in HostInfo.iteritems():
                t = False
                sftp = False
                sock = False
                key_test = False
                ssh = False
                self.logger.error('Starting key-exchange with \"%s/%s\" server' % (name, ip))
                try:
                    t, sftp, sock = ParaSftp(username=loginUser,
                                       hostname=ip,
                                       password=self.loginPw)
                    ssh = SSHExpect(user=loginUser, host=ip, passwd=self.loginPw)
                    ssh.ConnectHost()
                    if not loginUser == self.change_user:
                        ssh.CMD(send='su - %s' % self.change_user, 
                            promptRegEx=userPromptRegEx % self.change_user, 
                            RegEx= {1:('password:', self.rootPW)}, testExit=None)
                    for user, userHome in localUsersInfo.iteritems():
                        tmpFile = self.config['RemoteTmpDir'] + '/' + ip + '_' + user + '.pub'
                        sftp.put(userHome[1] + '/.ssh/id_%s.pub' % keyType, tmpFile)
                        sftp.chmod(tmpFile, 0666)
                        for Ruser in RemoteUserInfo:
                            # key exchange
                            self.logger.info('Stating Key-Exchange for local user \"%s\" with \"%s@%s\"' % \
                                              (user, Ruser, name))
                            ssh.CMD(send='su - %s' % Ruser, 
                                   promptRegEx=userPromptRegEx % Ruser,
                                   testExit=None)
                            ssh.CMD(send='cat %s >> ~/.ssh/authorized_keys' % tmpFile,
                                    promptRegEx=userPromptRegEx % Ruser)
                            ssh.CMD(send='chmod 600 ~/.ssh/authorized_keys',
                                    promptRegEx=userPromptRegEx % Ruser)
                            ssh.CMD(sendcontrol='d',
                                    promptRegEx=userPromptRegEx % self.change_user)
                            # update known_host
                            self.logger.info('Testing key-exchane for local user \"%s\" to \"%s@%s\"' % \
                                              (user, Ruser, name))
                            key_test = pexpect.spawn('su - %s' % user)
                            key_test.setecho(False)
                            key_test.ignorecase = True
                            index = key_test.expect([userPromptRegEx % user])
                            self.logger.debug('su: %s%s' % (key_test.before, key_test.after))
                            key_test.sendline('ssh %s@%s' % (Ruser, name))
                            index = key_test.expect(['\(yes.no\)', 
                                                     userPromptRegEx % Ruser, 
                                                     'password:'])
                            self.logger.debug('ssh: %s%s' % (key_test.before, key_test.after))
                            if index == 0:
                                key_test.sendline('yes')
                                null = key_test.expect([userPromptRegEx % Ruser])
                                self.logger.debug('yes: %s%s' % (key_test.before, key_test.after))
                            elif index == 1:
                                self.logger.error('Successfully key-exchange with local user \"%s\" and %s@%s'\
 													% (user, Ruser, ip))
                            else:
                                raise Exception, 'Fialed to run key-exchane from local user %s to %s@%s' % \
                                                 (user, Ruser, ip)
                            key_test.close()    
                        sftp.unlink(tmpFile)
                        self.logger.info('Successfully exchanged local user \"%s\" public-key with all remote users: \"%s\" on server %s' % \
                                (user, ' ,'.join(RemoteUserInfo), ip))
                    sftp.close()
                    t.close()
                    sock.close()
                    ssh.Close()
                    self.logger.error('Successfully exchanged public-key with %s/%s server' % \
                                     (name,ip))
                except:
                    e = traceback.format_exc()
                    for c in [key_test, sftp, t, sock, ssh]:
                        try:
                            c.close()
                        except:
                            continue
                    raise Exception, e

class key_generate(kex):
    def __call__(self):
        super(key_generate, self).__call__()
        self.key_generate()
    def key_generate(self):
        LocalUserList = []
        force = self.config['ForceKeyGen'].lower()
        keyType = self.config['KeyType']
        keyBytes= self.config.get('keyBytes', '1024')
        CMD = 'ssh-keygen -t %s' % keyType
        CMD += ' -b %s' % keyBytes
        CMD += ' -P \"\" -C %s'
        expectList = ['(?i)\(\/.*?\/\.ssh\/id_%s\):' % keyType, '(?i)\(y\/n\)\?', pexpect.EOF, pexpect.TIMEOUT]
        if force != 'y' and force != 'n':
            raise Exception, 'In valid \"ForceKeyGen\" value: \"%s\"' % force
        self.logger.info('\"ForceKeyGen\" parameter value: \"%s\"' % force)
        for id, info in self.serverList.iteritems():
            self.logger.info('Working on parametter: %s' % id)
            localUsersInfo = UserInfo(info[0])
            self.logger.info('Local users info taken from passwd file: %s' % localUsersInfo)
            if len(localUsersInfo.keys()) != len(info[0]):
                raise Exception, 'Can NOT find all loacl users in passwd file: %s' % info[0]
            for user, id_home in localUsersInfo.iteritems():
                if user in LocalUserList:
                    continue
                if not os.path.isdir(id_home[1] + '/.ssh'):
                    self.logger.error('%s/.ssh does not exists, will be created by the script' % \
                            id_home[1])
                    os.mkdir(id_home[1] + '/.ssh', 0700)
                    os.chown(id_home[1] + '/.ssh', int(id_home[0][0]), int(id_home[0][1]))
                self.logger.info('Starting to generatine a key for user: %s to file: %s/.ssh/id_%s' % \
                        (user, id_home[1], keyType))
                key = pexpect.spawn(CMD % id_home[0][0], timeout=5)
                gen = True
                while key.exitstatus != 0:
                    index = key.expect(expectList)
                    self.logger.debug('%s %s' % (key.before, key.after))
                    if index == 0:
                        key.sendline(id_home[1] + '/.ssh/id_%s' % keyType)
                    elif index == 1:
                        key.sendline(force)
                        if force == 'n':
                            gen = False
                            self.logger.error('file %s/.ssh/id_%s is already exists, skipping the key-generator' \
                                           % (id_home[1], keyType))
                        if force == 'y':
                            self.logger.error('file %s/.ssh/id_%s was overwrited' % (id_home[1], keyType))
                    elif index == 2:
                        key.close()
                        if gen:
                            self.logger.error('Successfully generated a key for user: %s to: %s/.ssh/id_%s' \
                                           % (user, id_home[1], keyType))
                        gen = True
                        break
                    elif index == 3:
                        key.close()
                        raise Exception, 'Generate-key was reached to TIMEOUT for user %s' % user
                    else:
                        raise Exception, 'Generate-key was failed for user %s' % user
                key.close()
                os.chown(id_home[1] + '/.ssh/id_%s' % keyType, int(id_home[0][0]), int(id_home[0][1]))
                os.chown(id_home[1] + '/.ssh/id_%s.pub' % keyType, int(id_home[0][0]), int(id_home[0][1]))
                LocalUserList.append(user)
            
