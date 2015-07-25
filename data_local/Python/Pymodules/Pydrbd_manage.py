from Pyfiledit import builder
import subprocess


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
        self.modprobe_drbd()

    def modprobe_drbd(self):
        self.logger.error('Executing drbdadm primary --force all')
        print'About to execute drbdadm primary --force all',
        executed_command = subprocess.Popen('drbdadm primary --force all', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            raise Exception, 'Executing drbdadm primary --force all Failed'
        else:
            print '...Succeeded'