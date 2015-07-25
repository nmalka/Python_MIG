
##################################
#   By: Itzik Ben Itzhak         #
#   Mail: itzik.b.i@gmail.com    #
#   Date: 03/08/10               #
#   ModuleNmae: Pydist.py        #
##################################

from Pyfiledit import builder
import paramiko, socket
from Pydecorators import *
import os, time, re ,sys, logging
from threading import Thread, Semaphore, BoundedSemaphore
from pdb import set_trace as st
from datetime import datetime
import traceback

class Dist(Thread):
    def __init__(self, user, ip, threads_sem, remote_file, local_file, section, tmp_suffix='', 
                 bufsize=8192, index_suffix='', date_format=None, backup_before_copy=False, 
                 port = 22, timeOut = 2, rsa=None, dsa=None, pw=None, 
                 logger_name='', *args, **kwargs):
        Thread.__init__(self, name = '%s-%s' % (section, ip))
        # setting self var for methid use,
        self.ip = ip
        self.port = port
        self.rsa = rsa
        self.dsa = dsa
        self.bufsize = bufsize
        self.logger_name = logger_name
        self.section = section
        self.user = user
        self.pw = pw
        self.backup_before_copy = backup_before_copy
        self.date_format = date_format
        self.remote_file = remote_file
        self.local_file = local_file
        # contacte "." to suffix if exists. 
        if tmp_suffix and not tmp_suffix.startswith('.'):
            tmp_suffix = '.' + tmp_suffix
        if index_suffix and not index_suffix.startswith('.'):
            index_suffix = '.' + index_suffix
        self.tmp_suffix = tmp_suffix
        self.index_suffix = index_suffix
        self.timeOut = timeOut
        self.logger = logging.getLogger('')
        self.threads_sem = threads_sem
        self.tlog = '[Thread: %s' % self.getName() + ']'
        self.ExitStatus = False
    def run(self):
        self.logger.info('%s Start' % self.tlog)
        try:
            self.connect()
            if type(self.local_file) != list:
                self.local_file = [self.local_file,]
                self.remote_file = [self.remote_file,]
            for i in range(0, len(self.local_file)):
                if self.backup_before_copy:
                    self.backup(self.remote_file[i])
                elif self.tmp_suffix:
                    # Make sure the file does not exist on remote server due to paramiko limitation
                    try:
                        tmp = self.sftp.stat(self.remote_file[i])
                        self.sftp.remove(self.remote_file[i])
                        self.logger.debug('%s %s: Exists on remote server, Deleting the file!' % \
                                          (self.tlog, self.remote_file[i]))
                    except:
                        self.logger.debug('%s %s: Does not exists on remote server, sipping the delete!' % \
                                          (self.tlog, self.remote_file[i]))
                self.copy(self.local_file[i], self.remote_file[i])
            self.disconnect()
        except:
            self.logger.error('%s %s' % (self.tlog, traceback.format_exc()))
            self.ExitStatus = False
            self.disconnect()
        else:
            self.ExitStatus = True
        self.writeStatusToLog()
        self.threads_sem.release()

    def writeStatusToLog(self):
        if self.ExitStatus:
            self.logger.error('%s Successfully distribute %s' % (self.tlog, self.remote_file))
        else:
            self.logger.error('%s Failed distribute %s' % (self.tlog, self.remote_file))
    def connect(self):
        if self.rsa:
            key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(self.rsa))
        elif self.dsa:
           key = paramiko.DSSKey.from_private_key_file(os.path.expanduser(self.dsa))
        elif not self.pw:
            raise 'AuthenticationError', 'No rsa/dsa/password where given'
        self.sock = socket.socket()
        self.sock.settimeout(self.timeOut)
        self.sock.connect((self.ip, self.port))
        self.t = paramiko.Transport(self.sock)
        if self.pw:
            self.t.connect(username=self.user, password=self.pw)
        else:
            self.t.connect(username=self.user, pkey=key)
        self.sftp = paramiko.SFTPClient.from_transport(self.t)
        self.logger.info("%s Sftp Connection to %s succeed" % (self.tlog, self.ip))
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
        f = '%s_%s' % (now.strftime(self.date_format), f)
        return os.path.join(p,f)
    def copy(self, lfile, rfile):
        if self.tmp_suffix:
            suffix = self.tmp_suffix
        elif self.index_suffix:
            suffix = self.index_suffix
            self.logger.error('%s File index: %s%s' % (self.tlog, os.path.basename(rfile), suffix))
        else:
            suffix = ''
        self.logger.info('%s Runnring put: %s %s' % (self.tlog, lfile, rfile + suffix))
        if getattr(lfile, 'readlines', False):
            self.fh_copy(suffix, lfile, rfile)
        else:
            self.sftp.put(lfile, rfile + suffix)
        if self.tmp_suffix:
            self.logger.info('%s Runnring rename: %s %s' % (self.tlog, rfile + suffix, rfile))
            self.sftp.rename(rfile + suffix, rfile)
    def fh_copy(self, suffix, lfile, rfile):
        self.logger.error('%s Copy via FH: %s %s' % (self.tlog, lfile, rfile + suffix))
        rfh = self.sftp.open(filename = rfile + suffix, mode = 'w', bufsize = self.bufsize)
        for line in lfile.readlines():
            rfh.write(line)
        rfh.close()
        lfile.close()
    def disconnect(self):
        try:
            self.sftp.close()
            self.sock.close()
            self.t.close()
        except:
            self.logger.debug('%s %s' % (self.tlog, traceback.format_exc()))

class dist_ini(builder):
    def __init__(self, config, componentID, Argv, *args, **kwargs):
        super(dist_ini, self).__init__(config=config, componentID=componentID, *args, **kwargs)
        self.disable_dist = config['DisableDistKey']
        self.net = config['Network'].upper()
        if len(Argv) != 1:
            print '\nUsage: ./runner.py <dist_ini.py> <%s password>\n' % config['RemoteUser']
            raise 'UsageError', 'Usage: ./runner.py <dist_ini.py> <%s password>' % config['RemoteUser']
        self.pw = Argv[0]
        if config.get('BackupBeforeCopy', '').lower() == 'yes':
            self.backupBeforeCopy = True
        else:
            self.backupBeforeCopy = False
        self.dateFormat = config.get('DateFormat', '%Y-%d-%m_%H-%M-%S')
        self.skipLocal = config.get('SkipLocal', 'yes').lower()
        self.forceSections = config.get('ForceSections', '') or []
        if type(self.forceSections) == str:
            self.forceSections = [ f.strip() for f in self.forceSections.split(',') ]
        self.tmpSuffix = config.get('TmpSuffix', '')
        self.timeOut = int(config['SocketTimeout'])
        self.Ruser = config['RemoteUser']
        self.threads_sem = Semaphore(int(config['MaxThreads']))
        self.sysConfig, self._, self.__ = config['sysConfig'], config['_'], config['__']
        self.tree = self.getSectionServers()
    def getSectionServers(self):
        tree = {}
        forceSections = False
        if len(self.forceSections):
            forceSections = True
            self.logger.error('forceSections: %s' % ', '.join(self.forceSections))
        for section in [ s for s in self.sysConfig.sections()\
                if self._(s, 'type', False).lower() == 'server' and\
                not self._(s, self.disable_dist, False).lower() == 'yes']:
            self.logger.info('Section: %s' % section)
            if forceSections and section in self.forceSections or not forceSections:
                admin_net = self._(section, 'admin_network', False) or self.net
                ips = [ ip[0] for ip in self.__(section, self._(section, 'host_key_detect'), 
                    Key=admin_net)]
                self.logger.info('IPs: %s' % ', '.join(ips))
                if len(ips) and self.skipLocal == 'yes' and\
                            self.config['Section'] == section and\
                            self._(section, admin_net.lower() + '-rip') in ips:
                        ip = self._(section, admin_net.lower() + '-rip')
                        ips.remove(ip)
                        self.logger.error('removing local IP: %s from Section: %s' % (ip, section))
                if len(ips):
                    tree[section] = ips
        self.logger.debug(tree)

        return tree
    def __call__(self, editFiles):
        ### Main ###
        Threads = self.dist(editFiles)
        th = self.ThreadsDone(Threads)
        self.threadTest(Threads)
    def threadTest(self, Threads):
        self.logger.error(' ------ Distribute summarized -------\n')
        for t in sorted(Threads, key=lambda t: t.ExitStatus, reverse=True):
            self.logger.error('%s, %s: %s, %s' % (t.section, t.ip, \
                               t.ExitStatus and 'Successfully' or 'Failed', t.local_file))
        if False in [ t.ExitStatus for t in Threads ]:
            raise 'DistError', 'Not all servers where distribute.'
    def dist(self, editFiles):
        Threads = []
        self.logger.info('Distribute: %s' % editFiles)
        for section, ips in self.tree.iteritems():
            for ip in ips:
                th = Dist(ip=ip, pw=self.pw, timeOut=self.timeOut, backup_before_copy=self.backupBeforeCopy,
                        local_file=editFiles, remote_file=editFiles, tmp_suffix=self.tmpSuffix,
                        user=self.Ruser, threads_sem=self.threads_sem, date_format=self.dateFormat, section=section)
                Threads.append(th)
                self.threads_sem.acquire()
                th.start()
        return Threads
    def ThreadsDone(self, Threads):
        self.logger.info('All threads where released, waiting for the join...')
        for thread in Threads:
            thread.join()
        return True
