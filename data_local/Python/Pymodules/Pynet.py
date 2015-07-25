
###############################
#   By: Itzik Ben Itzhak      #
#   Mail: itzik.b.i@gmail.com #
#   Ver: 4.8                  #
#   Date: 08/07/09            #
#   ModuleName: Pynet.py      #
###############################

def ParaSftp(hostname,
                port=22,
                username=None,
                password=None,
                DSApkey=None,
                RSApkey=None,
                connectionAttempts=1,
                loggerName='',
                connectionTimeOut=10,
                connectionDelay=5,):
    import paramiko
    import socket
    import logging
    import time
    import os, sys
    import traceback
    logger = logging.getLogger(loggerName)
    try:
        if RSApkey: key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(RSApkey))
        if DSApkey: key = paramiko.DSSKey.from_private_key_file(os.path.expanduser(DSApkey))
    except (IOError, paramiko.SSHException):
        logger.error(traceback.format_exc())
        logger.error("Please check the Authentication RSA/DSA key file: %s/%s" % \
                (RSApkey,DSApkey))
        sys.exit(1)
    try:
        for i in range(connectionAttempts):
            try:
                sock = socket.socket()
                sock.settimeout(connectionTimeOut)
                sock.connect((hostname, port))
                t = paramiko.Transport(sock)
                if password:
                    t.connect(username=username, password=password)
                else:
                    t.connect(username=username, pkey=key)
                break
            except (socket.error, socket.gaierror, socket.timeout, socket.herror, \
                    paramiko.AuthenticationException, UnboundLocalError):
                logger.error(traceback.format_exc())
                logger.error("Attempt no:%s, Failed to connect: %s" % (i+1, hostname))
                try:
                    t.close()
                    sock.close()
                except:
                    pass
                time.sleep(connectionDelay)
                if i == connectionAttempts-1:
                    raise StopIteration
        sftp = paramiko.SFTPClient.from_transport(t)
        logger.error ("Sftp Connection to %s succeed on Attempt no:%s" % (hostname, i+1))
    except (paramiko.SSHException, StopIteration, socket.error, socket.gaierror, \
            paramiko.AuthenticationException, UnboundLocalError, paramiko.SFTPError,
            socket.timeout, socket.herror):
        logger.error(traceback.format_exc())
        logger.error("Failed to connect: %s@%s" % (username,hostname))
        try:
            t.close()
            sock.close()
        except:
            pass
        raise Exception
    return t, sftp, sock

def ConnectionTest(hostname,
                    port=22,
                    protoMethod=None,
                    connectionAttempts=1,
                    loggerName='',
                    connectionTimeOut=10,
                    connectionDelay=5,):
    import socket
    import logging
    import time
    import os, sys
    import traceback
    logger = logging.getLogger(loggerName)
    if protoMethod == 'udp':
        protoMethod = socket.SOCK_DGRAM
    else:
        protoMethod = socket.SOCK_STREAM
    sock = socket.socket(type=protoMethod)
    sock.settimeout(connectionTimeOut)
    try:
        for i in range(connectionAttempts):
            try:
                sock.connect((hostname,port))
                break
            except (socket.error, socket.gaierror, socket.timeout, socket.herror):
                logger.error(traceback.format_exc())
                logger.error("%s: Attempt no:%s, Failed to connect: %s on port %s" % \
                        (protoMethod, i+1, hostname, port))
                time.sleep(connectionDelay)
                if i == connectionAttempts-1:
                    raise StopIteration
    except (StopIteration, socket.error, socket.gaierror, socket.timeout, socket.herror, \
            UnboundLocalError):
        logger.error(traceback.format_exc())
        logger.error("Failed to connect %s on port %s" % (hostname, port))
        sock.close()
        raise Exception
    else:
        sock.close()
        logger.info("%s: Connection establish successfully via port %s" % (hostname,port))
        return True

class ParaSsh:
    def __init__(self, 
                 hostname, 
                 username, 
                 password=None,
                 DSApkey=None,
                 RSApkey=None,
                 port=22,
                 loggerName='',
                 connectionAttempts=3,
                 connectionDelay=5,
                 connectionTimeOut=10,):
        import paramiko
        import sys, time, socket, logging, os
        import traceback
        self.logger = logging.getLogger(loggerName)
        try:
            if RSApkey: key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(RSApkey))
            if DSApkey: key = paramiko.DSSKey.from_private_key_file(os.path.expanduser(DSApkey))
        except (IOError, paramiko.SSHException):
            self.logger.error(traceback.format_exc())
            self.logger.error("Please check the Authentication RSA/DSA key file: %s/%s" % \
                    (RSApkey,DSApkey))
            sys.exit(1)
        try:
            for i in range(connectionAttempts):
                try:
                    self.sock = socket.socket()
                    self.sock.settimeout(connectionTimeOut)
                    self.sock.connect((hostname, port))
                    self.t = paramiko.Transport(sock)
                    if password:
                        self.t.connect(username=username, password=password)
                    else:
                        self.t.connect(username=username, pkey=key)
                    break
                except (socket.error, socket.gaierror, socket.timeout, socket.herror, \
                        paramiko.AuthenticationException, UnboundLocalError):
                    self.logger.info(traceback.format_exc())
                    self.logger.info("Attempt no:%s, Failed to connect: %s" % (i+1, hostname))
                    try:
                        self.t.close()
                        self.sock.close()
                    except:
                        pass
                    time.sleep(connectionDelay)
                    if i == connectionAttempts-1:
                        raise StopIteration
        except (paramiko.SSHException, StopIteration, socket.error, socket.gaierror, \
                paramiko.AuthenticationException, UnboundLocalError, paramiko.SFTPError,
                socket.timeout, socket.herror):
            self.logger.error(traceback.format_exc())
            self.logger.error("Failed to connect to: %s@%s" % (username,hostname))
            try:
                self.t.close()
                self.sock.close()
            except:
                pass
            raise Exception
        self.out = ''
        self.err = ''
    def _shellOut(self, chan, recv='stdout'):
        import select
        if recv == 'stdout': self.out = ''
        if recv == 'stderr': self.err = ''
        while select.select([chan,], [], []):
            if recv == 'stdout':
                x = chan.recv(1024)
                if not x: break
                self.out += x
            elif recv == 'stderr':
                y = chan.recv_stderr(1024)
                if not y: break
                self.err += y
            select.select([],[],[],.1)
    def ptyShell(self,send,
                 cmd='su - root',
                 term='vt100', 
                 width=80, 
                 height=24,
                 sleep=1,
                 promptExpectReg='Password:',):
        import time, re, sys
        import thread
        import traceback
        exitStatus = 1
        verifyStatus = False
        promptReg = re.compile(promptExpectReg, re.I)
        try:
            chan = self.t.open_session()
            chan.setblocking(1)
            chan.get_pty(term=term, width=width, height=height)                
            chan.invoke_shell()
            thread.start_new_thread(self._shellOut,(chan,))
            s = chan.send(cmd +'\n')
            if s == 0: raise Exception, 'cmd could not be sent'
            time.sleep(sleep)
            if promptReg.search(self.out):
                s = chan.send(send + '\n')
                if s == 0: raise Exception, 'prompt could not be sent'
                time.sleep(sleep)
                s = chan.send('echo $?\n')
                if s == 0: raise Exception, '\'echo $?\' could not be sent'
                time.sleep(sleep)
            else:
                chan.close()
                self.logger.error("prompt shell did NOT match with the RegularExpretion, \'%s\'" % \
                                promptExpectReg)
            if re.search(r'echo \$\?[\s\t]\n0', self.out):
                self.logger.info("\"%s\" exit with status \"0\"" % cmd)
                exitStatus = 0
            else:   
                self.logger.error('Faild to run \"%s\"' % (cmd))
        except:
            self.logger.debug(traceback.format_exc())
            try:
                chan.close()
            except:
                pass
            self.logger.debug('Shell output:\n:%s' % self.out)
            raise
        else:
            self.logger.debug('Shell output:\n:%s' % self.out)
            return exitStatus, self.out
    def run(self,cmd):
        chan = self.t.open_session()
        chan.setblocking(1)
        chan.exec_command(cmd)
        self._shellOut(chan)
        if chan.recv_exit_status() != 0:
            self._shellOut(chan, recv='stderr')
            self.logger.info('Faild to run \"%s\"' % (cmd))
            self.logger.debug('%s' % (self.err))
            self.out = ''
        else:
            self.logger.info('\"%s\" return with exit 0' % (cmd))
            self.logger.debug('%s' % (self.out))
            self.err = ''
        return chan.recv_exit_status(), self.out, self.err
    def kill(self):
        self.t.close()
        self.sock.close()

class IPCalc:
    def __init__(self,ip, subnet):
        self.ip = ip
        self.subnet = subnet
    def calcNet(self):
        import os, re
        inp = os.popen('ipcalc -n ' + self.ip + ' ' + self.subnet)
        net = inp.readlines()
        inp.close()
        net   = re.compile('.+=(.+)').search(net[0]).group(1)
        return net
    def calcBroadcast(self):
        import os, re
        inp = os.popen('ipcalc -b ' + self.ip + ' ' + self.subnet)
        broad = inp.readlines()
        inp.close()
        broad   = re.compile('.+=(.+)').search(broad[0]).group(1)
        return broad

class SSHExpect(object):
    def __init__(self, user, host, passwd, timeout=5, login=[ \
                '\(yes.no\)',
                'password:',
                '(:?\-bash\-\d+?\.\d+?\$)|(:?\[%s@.*\])'],
                ignorecase = True,
                loggerName='',
                ):
        import logging
        self.logger = logging.getLogger(loggerName)
        self.ignorecase = ignorecase
        self.user = user
        self.host = host
        self.login = login
        self.passwd = passwd
        self.timeout = timeout
        try:
            self.login[2] = self.login[2] % user
        except:
            pass
    def ConnectHost(self):
        import pexpect
        self.logger.info('Connecting to: ssh %s@%s' % (self.user, self.host))
        self.connect = pexpect.spawn('ssh %s@%s' % (self.user, self.host), timeout=self.timeout)
        self.connect.ignorecase = self.ignorecase
        index = 0
        num = 0
        self.logger.debug('Compare List: %s' % self.login)
        while index <= 1:
            num += 1
            index = self.connect.expect(self.login)
            self.logger.debug('%s %s' % (self.connect.before, self.connect.after))
            self.logger.info('Match %s: %s' % (index, self.login[index]))
            if num > 3:
                raise Exception, '\n%s %s\nFailed to log into %s@%s' % ( \
                        self.connect.before, self.connect.after, self.user, self.host)
            elif index == 0:
                self.connect.sendline('yes')
            elif index == 1:
                self.connect.sendline(self.passwd)
            else:
                self.logger.info('Successfully connected to: %s@%s' % (self.user, self.host))
                break
    def CMD(self, promptRegEx, send=None, sendcontrol=None, RegEx=None, ignorecase=None, \
            testExit='echo $?', exitCompare=None):
        if ignorecase:
            self.connect.ignorecase = ignorecase
        index = 1
        compare = [promptRegEx]
        if RegEx:
            for val in RegEx.values():
                compare.append(val[0])
        self.logger.debug('Compare list: %s' % (compare))
        self.connect.setecho(False)
        if send:
            self.connect.sendline(send)
            self.logger.info('Sending: %s' % send)
        else:
            self.logger.info('Send Ctrl-%s' % sendcontrol)
            testExit = None
            self.connect.sendcontrol(sendcontrol)
        while index > 0:
            index = self.connect.expect(compare)
            self.logger.debug('%s %s' % (self.connect.before, self.connect.after))
            if index > 0:
                self.connect.sendline(RegEx[index][1])
            elif index == 0:
                if send:
                    self.logger.info('Done sending: %s' % send)
                else:
                    self.logger.info('Done sending Ctrl-%s' % sendcontrol)
                if testExit:
                    if exitCompare:
                        exitCompare = [ exitCompare ]
                    else:
                        exitCompare = [ 'echo \$\?[\s\t]\n0' ]
                    self.logger.debug('Compare list: %s' % (exitCompare))
                    self.logger.info('Testing the exit status of: %s' % send)
                    self.logger.debug('By sending: %s' % testExit)
                    try:
                        self.connect.sendline(testExit)
                        self.connect.expect(exitCompare)
                        self.logger.debug('%s %s' % (self.connect.before, self.connect.after))
                        self.logger.info('Testing: exit status is OK!')
                    except:
                        import sys
                        import traceback
                        self.logger.error(traceback.format_exc())
                        raise Exception, 'Failed to run: %s' % send
                else:
                    break

    def Close(self):
        self.connect.close()
        self.logger.info('Connection to %s was closed' % self.host)
