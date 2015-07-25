from Pyfiledit import builder
import subprocess
import os

'''
sfdisk /dev/sdb -uM << EOF
,1024,8e
,1024,8e
,512,8e
,,E
,512,8e
,512,8e
EOF
'''

class CreatePartitions(builder):

    def __call__(self):
        self.create_partition()

    def create_partition(self):
        command = "sfdisk /dev/%(device)s -uM << EOF\n%(_input)s\nEOF" %{"device":"sdb", "_input":self.config['iData']['fs_structure']['final']}
        print "about to execute the following command:"
        print command + "\n"
        executed_command = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        command_stdout, command_stderr = executed_command.communicate()
        if executed_command.returncode != 0:
            self.logger.error(command_stderr)
            print command_stdout
            raise Exception, 'Failed to execute:\n%s' %command
        else:
            print command_stdout
            print 'Succeeded\n'

class DirsCreation (builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DirsCreation, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.dirs_creation()

    def dirs_creation(self):
        for k,v in self.config['iData']['fs_structure']['DIR_Topology'].iteritems():
            if not os.path.exists(k):
                print "About to create %s ..." %k,
                try:
                    os.makedirs(k)
                except:
                    raise Exception, "Creating of %s Failed"
                else:
                    print 'Succeeded\n'

class DirsPermissions(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(DirsPermissions, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.dirs_permissions()

    def dirs_permissions(self):
        for k,v in self.config['iData']['fs_structure']['DIR_Topology'].iteritems():
            print "About to execute chown %s:%s %s ..." %( v['USER'],v['GROUP'],k),
            CHowner = subprocess.Popen('chown %s:%s %s' %( v['USER'],v['GROUP'],k) , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command_stdout, command_stderr = CHowner.communicate()
            if CHowner.returncode != 0:
                self.logger.error(command_stderr)
                print command_stdout
                raise Exception, 'Failed Changing Owner to %s %s : %s' %(k,v['USER'],v['GROUP'])
            else:
                print 'Succeeded\n'
            print "About to execute chmod %s %s ..." %( v['CHMOD'],k),
            CHmod = subprocess.Popen('chmod %s %s' %( v['CHMOD'],k) , shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            command_stdout, command_stderr = CHmod.communicate()
            if CHmod.returncode != 0:
                self.logger.error(command_stderr)
                print command_stdout
                raise Exception, 'Failed Changing mode to %s %s' %(k,v['CHMOD'])
            else:
                print 'Succeeded\n'

