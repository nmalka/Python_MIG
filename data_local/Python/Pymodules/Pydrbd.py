from Pyfiledit import builder
import glob
import os
import subprocess

class BuildDrbdConf(builder):
    res_files_dir = '/etc/drbd.d'
    def __call__(self):
        self.delete_res_files()
        self.create_res_files()
        self.update_drbd_global_common()

    def create_res_files(self):
        for val in self.config['iData']['drbd']['resources'].itervalues():
            for k, v in val.iteritems():
                res_file = k[:k.find(':')] + '.res'
                try:
                    print 'Creating: %s ...' %res_file,
                    f = open(self.res_files_dir + '/%s' %res_file, 'w')
                    f.write(v)
                    f.close()
                    print 'Done'
                except IOError:
                    print 'Problem creating the file: ' + self.res_files_dir + '/%s' %res_file

    def update_drbd_global_common(self):
        if not os.path.isfile(self.res_files_dir + '/global_common.conf'):
            print 'Couldn\'t find the file: ' + self.res_files_dir + '/global_common.conf'
        else:
            try:
                print 'Updating: global_common.conf ...',
                f = open(self.res_files_dir + '/global_common.conf', 'w')
                f.write(self.config['iData']['drbd']['global_common'])
                f.close()
                print 'Done'
            except IOError:
                print 'Problem processing the file' + self.res_files_dir + '/global_common.conf'

    def delete_res_files(self):
        os.chdir(self.res_files_dir)
        if os.getcwd() == self.res_files_dir:
            filelist = glob.glob('*.res')
            for f in filelist:
                print 'Removing: %s ...' %f,
                try:
                    os.remove(f)
                    print 'Done'
                except:
                    print 'Failed'
        else:
            print 'Couldn\'t find %s' %self.res_files_dir

class DrbdStart(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DrbdStart, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.drbd_start()

    def drbd_start(self):
        self.logger.error('Starting DRBD service')
        print'About to start DRBD service',
        executed_command = subprocess.Popen('/etc/init.d/drbd start', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            raise Exception, 'Failed to start DRBD service'
        else:
            print '...Succeeded'

class ModprobeDrbd(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(ModprobeDrbd, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.modprobe_drbd()

    def modprobe_drbd(self):
        self.logger.error('Executing modprobe drbd')
        print'About to execute modprobe drbd',
        executed_command = subprocess.Popen('modprobe drbd', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            raise Exception, 'Executing modprobe drbd Failed'
        else:
            print '...Succeeded'

class MakePrimary(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(MakePrimary, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.make_primary()

    def make_primary(self):
        self.logger.error('Executing drbdadm primary --force all')
        print'About to execute drbdadm primary --force all',
        executed_command = subprocess.Popen('drbdadm primary --force all', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            raise Exception, 'Executing drbdadm primary --force all Failed'
        else:
            print '...Succeeded'

class CreateMd(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(CreateMd, self).__init__(config=config, componentID=componentID, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.create_md()

    def create_md(self):
        self.logger.error('Executing drbdadm create-md all')
        print'About to execute drbdadm create-md all',
        executed_command = subprocess.Popen('drbdadm create-md all', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            raise Exception, 'Executing drbdadm create-md all Failed'
        else:
            print '...Succeeded'

