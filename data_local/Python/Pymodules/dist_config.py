CONNECTION_MESSAGE = 'Connection to %s closed.'
PASS_REGEX = '(Password|password):'
SUDO_REGEX = '\[sudo\] password for (\w+):'
AUTHENTICATION_SUCCEEDED = 'Authentication admintools SshClient succeeded for %s'
SU_AUTHENTICATION_SUCCEEDED = 'All Authentication SshClient Are Done'
DUMMY_REGEX = '__admintools_ignore_dummy_regex__'
DUMMY_REGEX_SEND = 'admintools_regex_ignore'
SYSTEM_INI_REGEX = '\[Runner\] What is \"\w+\" server index from system\.ini file\?: \w+' 
SYSTEM_INI_SECTION_REGEX = "\[Runner\] What is the section name from system\.ini file\?: "
SSH_DELIMITER = '\'\'\''
SSH = '/bin/ssh'
SU = '/bin/su -'
SCP = '/bin/scp'
import os
if os.uname()[-1] == "x86_64":
    SSH = '/usr/bin/ssh'
    SCP = '/usr/bin/scp'
QUIT_MODE = False
DEFAULT_UMASK = 488
STATUS_CMD_FILE = '/data_local/Python/Installer/.status_cmds'
