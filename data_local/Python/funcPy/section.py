from Pyconstruct.Pymatrix import buildSysConfig
from Pyrunner import RunnerConfDummy
from Pyconstruct.Pysec import Encrypt, Decrypt
import os
from app_map import COREPY_PATH,DEFAULT_APPS,CORE_APPS,INCLUDED_APPS,HOST_DELIMITER,UI_APPS,ADMIN_NETWORK,WIRELESS_NETWORK,GLOBAL_CORE_APPS,V6_NETWORK,NET_SUPPORT_SECTIONS

sysConfig, _, __ = buildSysConfig(DEFAULT_APPS=DEFAULT_APPS,CORE_APPS=CORE_APPS,INCLUDED_APPS=INCLUDED_APPS,UI_APPS=UI_APPS,GLOBAL_CORE_APPS=GLOBAL_CORE_APPS,host_delimiter=HOST_DELIMITER,net_support_sections=NET_SUPPORT_SECTIONS)
# BackupPath - where to backup the files
BackupPath = _('RUNNER', 'install_backup_path')

# Log File full path name
LogFile = _('RUNNER', 'logfile')

# Log levels are 0-2: 0-ERROR, 1-INFO and 2-DEBUG
LogLevel = _('RUNNER', 'loglevel')

Section = _('RUNNER','Section')
server_key = _(Section,'server_key')

_D = sysConfig.DynamicOption
_AppVip = sysConfig.AppVip
__AppVip = sysConfig.AppVips
host_key_detect = sysConfig.host_key_detect

iData = {'_' : _ ,
         '__' : __ ,
         'sysConfig' : sysConfig,
         '_D' : sysConfig.DynamicOption,
         'Section' : Section ,
         'host_key_detect' : host_key_detect,
         'server_key' : server_key,
         'RunnerConfDummy' : RunnerConfDummy,
         'COREPY_PATH' : COREPY_PATH,
         'os' : os ,
         'ADMIN_NETWORK' : ADMIN_NETWORK,
         'WIRELESS_NETWORK' : WIRELESS_NETWORK,
         'V6_NETWORK' : V6_NETWORK,
         '_AppVip' : _AppVip,
         '__AppVip' : __AppVip,
        }

__all__ = ['sysConfig', '_', '__','_D','_AppVip','__AppVip','Section','COREPY_PATH','iData',\
           'RunnerConfDummy','server_key','os','ADMIN_NETWORK','WIRELESS_NETWORK','V6_NETWORK','LogLevel','LogFile','BackupPath','NET_SUPPORT_SECTIONS', 'Encrypt', 'Decrypt']
