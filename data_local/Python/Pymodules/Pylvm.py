from Pyfiledit import builder
from commands import getstatus
import os
import subprocess


class Pvcreate(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Pvcreate, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self):
        self.phisical_volume_create()

    def phisical_volume_create(self):
        self.logger.error('Creating PV\'s on the system')
        for app_name, res in self.config['iData']['lvm']['resources'].iteritems():
            for res_name, command in res.iteritems():
                if 'pvcreate' in command:
                    print'About to execute %(command)s...' %{'command':command['pvcreate']},
                    executed_command = subprocess.Popen(command['pvcreate'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    command_stdout, command_stderr = executed_command.communicate()
                    if executed_command.returncode != 0:
                        self.logger.error(command_stderr)
                        raise Exception, 'Executing %(command)s for resource %(res_name)s FAILED: %(command_stdout)s' %{'command':command['pvcreate'],
                                                                                                                          'res_name':res_name[:res_name.find(':')],
                                                                                                                          'command_stdout':command_stdout}
                    else:
                        print "Succeeded\n"
                        print 'About to execute pvscan ...',
                        pvscan = subprocess.Popen('pvscan', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        command_stdout, command_stderr = pvscan.communicate()
                        if pvscan.returncode != 0:
                            self.logger.error(command_stderr)
                            print command_stdout
                            raise Exception, 'Executing pvscan for resource %(res_name)s FAILED...' %{'res_name':res_name[:res_name.find(':')]}
                        else:
                            print 'Succeeded\n'

class Vgcreate(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Vgcreate, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self):
        self.volume_group_create()

    def volume_group_create(self):
        self.logger.error('Creating VG\'s on the system')
        for app_name, res in self.config['iData']['lvm']['resources'].iteritems():
            for res_name, command in res.iteritems():
                if 'vgcreate' in command:
                    print'About to execute %(command)s...' %{'command':command['vgcreate']},
                    executed_command = subprocess.Popen(command['vgcreate'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    command_stdout, command_stderr = executed_command.communicate()
                    if executed_command.returncode != 0:
                        self.logger.error(command_stderr)
                        raise Exception, 'Executing %(command)s for resource %(res_name)s FAILED: %(command_stdout)s' %{'command':command['vgcreate'],
                                                                                                                          'res_name':res_name[:res_name.find(':')],
                                                                                                                          'command_stdout':command_stdout}
                    else:
                        print "Succeeded\n"
                        print 'About to execute vgscan ...',
                        vgscan = subprocess.Popen('vgscan', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        command_stdout, command_stderr = vgscan.communicate()
                        if vgscan.returncode != 0:
                            self.logger.error(command_stderr)
                            print command_stdout
                            raise Exception, 'Executing vgscan for resource %(res_name)s FAILED...' %{'res_name':res_name[:res_name.find(':')]}
                        else:
                            print 'Succeeded\n'

class Lvcreate(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Lvcreate, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self):
        self.logical_volume_create()

    def logical_volume_create(self):
        self.logger.error('Creating LV\'s on the system')
        for app_name, res in self.config['iData']['lvm']['resources'].iteritems():
            for res_name, command in res.iteritems():
                if 'lvcreate' in command:
                    print'About to execute %(command)s...' %{'command':command['lvcreate']},
                    executed_command = subprocess.Popen(command['lvcreate'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    command_stdout, command_stderr = executed_command.communicate()
                    if executed_command.returncode != 0:
                        self.logger.error(command_stderr)
                        raise Exception, 'Executing %(command)s for resource %(res_name)s FAILED: %(command_stdout)s' %{'command':command['lvcreate'],
                                                                                                                          'res_name':res_name[:res_name.find(':')],
                                                                                                                          'command_stdout':command_stdout}
                    else:
                        print "Succeeded\n"
                        print 'About to execute lvscan ...',
                        lvscan = subprocess.Popen('lvscan', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                        command_stdout, command_stderr = lvscan.communicate()
                        if lvscan.returncode != 0:
                            self.logger.error(command_stderr)
                            print command_stdout
                            raise Exception, 'Executing lvscan for resource %(res_name)s FAILED' %{'res_name':res_name[:res_name.find(':')]}
                        else:
                            print "Succeeded\n"

class Mkfs(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Mkfs, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.mkfs()

    def mkfs(self):
        self.logger.error('Running mkfs on the system')
        for app_name, res in self.config['iData']['lvm']['resources'].iteritems():
            for res_name, command in res.iteritems():
                if 'mkfs' in command:
                    print'About to execute %(command)s ...' %{'command':command['mkfs']},
                    executed_command = subprocess.Popen(command['mkfs'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    command_stdout, command_stderr = executed_command.communicate()
                    if executed_command.returncode != 0:
                        self.logger.error(command_stderr)
                        raise Exception, 'Executing %(command)s for resource %(res_name)s FAILED: %(command_stdout)s' %{'command':command['mkfs'],
                                                                                                                          'res_name':res_name[:res_name.find(':')],
                                                                                                                          'command_stdout':command_stdout}
                    else:
                        print "Succeeded\n"

class Mounts(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(Mounts, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.mount()

    def mount(self):
        self.logger.error('Mounting the system')
        for app_name, res in self.config['iData']['lvm']['resources'].iteritems():
            for res_name, command in res.iteritems():
                if 'mount' in command:
                    print'About to execute %(command)s ...' %{'command':command['mount']},
                    executed_command = subprocess.Popen(command['mount'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    command_stdout, command_stderr = executed_command.communicate()
                    if executed_command.returncode != 0:
                        self.logger.error(command_stderr)
                        raise Exception, 'Executing %(command)s for resource %(res_name)s FAILED: %(command_stdout)s' %{'command':command['mount'],
                                                                                                                          'res_name':res_name[:res_name.find(':')],
                                                                                                                          'command_stdout':command_stdout}
                    else:
                        print "Succeeded\n"

class LvmConf(builder):
    text_to_replace = {'write_cache_state = 1':'write_cache_state = 0',
           'filter = [ "a/.*/" ]':'filter = [ "a|drbd.*|", "r|.*|" ]'}

    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(LvmConf, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.lvm_conf()

    def text_replace(self, text, dic):
        for i, j in dic.iteritems():
            text = text.replace(i, j)
        return text

    def lvm_conf(self):
        print "About to configure /etc/lvm/lvm.conf ...",
        try:
            f = open('/etc/lvm/lvm.conf', 'r')
            lvmconf = f.read()
            f.close()
        except IOError:
            self.logger.error('Unable to open /etc/lvm/lvm.conf')
            raise Exception,'Unable to open /etc/lvm/lvm.conf'
        else:
            new_lvmconf = self.text_replace(lvmconf, self.text_to_replace)
            f = open('/etc/lvm/lvm.conf', 'w')
            f.write(new_lvmconf)
            f.close()
            print "Succeeded"

class LockFile(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(LockFile, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.lock_file()

    def lock_file(self):
        for res in self.config['iData']['lvm']['resources'].itervalues():
            for v in res.itervalues():
                if not os.path.isfile('%s/%s' %(v['MountPoint'], self.config['lock_file'])):
                    f = open('%s/%s' % (v['MountPoint'],self.config['lock_file']), 'w')
                    f.close()
                executed_command = subprocess.Popen('chattr +i %s/%s' % (v['MountPoint'],self.config['lock_file']), shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                command_stdout, command_stderr = executed_command.communicate()
                if executed_command.returncode != 0:
                    self.logger.error(command_stderr)
                    self.logger.error("Succesefully created .lock_file for: %s" %v['MountPoint'])
                    raise Exception, 'Faild to run: \'chattr +i %s/%s\'' % (v['MountPoint'], self.config['lock_file'])
                else:
                    print "Succesefully created .lock_file for: %s" %v['MountPoint']
class DelLvmCache(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DelLvmCache, self).__init__(config=config, componentID=componentID,
                loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.del_lvm_cache()

    def del_lvm_cache(self):
                executed_command = subprocess.Popen('rm -f /etc/lvm/cache/.cache', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                command_stdout, command_stderr = executed_command.communicate()
                if executed_command.returncode != 0:
                    self.logger.error(command_stderr)
                    self.logger.error("Succesefully deleted /etc/lvm/cache/.cache")
                    print 'Couldn\'t remove /etc/lvm/cache/.cache please do it manually if you have problems with lvm display'
                else:
                    print "Succesefully removed /etc/lvm/cache/.cache"
