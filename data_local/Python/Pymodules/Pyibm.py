from Pyfiledit import builder
import re
import paramiko
import os, sys
import time
import subprocess

     
class ibm_sizing(builder):
    ''' This class configure the storewize storage according configuration file '''
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(ibm_sizing, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        c = config['iData']
        self._config = c['storewize']
        
    def __call__(self, *args, **kwargs):
      
        self.logger.error('start creating mdisk') 
        self.drive_ds()
        self.build_mdisk_ds()
        self.get_configure_disks()
        self.run_mdisk()
        self.logger.error('finish creating mdisk') 
        
    def build_mdisk_ds(self):
        ''' This function build the mdisk data structure '''
        self.logger.info('Start - Bulid the mdisk data structure')
        self.mdisks = {}
        for key, value in self._config.iteritems():
            if not key.startswith('mounts_') or not value:
                continue
            mounts = [m.strip() for m in value.split(',') if m.strip() ]
            for mdisk in mounts:
                mdisk_splited = mdisk.split(':')
                mdisk_name = mdisk_splited[0].strip()
                mdisk_path = mdisk_splited[1].strip()
                mdisk_raid = mdisk_splited[2].strip()
                mdisk_drives = mdisk_splited[3].strip().lower()
                if not self.mdisks.has_key(mdisk_name):
                    self.mdisks[mdisk_name] = {}
                self.mdisks[mdisk_name]['path'] = mdisk_path
                self.mdisks[mdisk_name]['raid_type'] = mdisk_raid.lower()
                _drives = mdisk_drives.split('disks-')[1]
                self.mdisks[mdisk_name]['drives'] =  _drives.replace('-', ':')
                self.mdisks[mdisk_name]['mdisk_cmd1'] = 'svctask mkmdiskgrp -ext 1024 -guiid 0 -name %s -warning 80%s' % (mdisk_name,'%')
        self.logger.info('Finished - Bulid the mdisk data structure')
        
    def connect(self):
        ''' Create the connection via ssh to the storewize '''
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh.connect(self._config['storewize_ip'], int(self._config['storewize_port']), self._config['storewize_user'], self._config['storewize_password'])
            self.logger.info('connection passed successfully') 
        except:
            raise Exception, 'Error - Connection problem...to %s' % self._config['storewize_ip']
            
    def disconnect(self):
        ''' Disconnect from the storewize '''
        try:
            self.ssh.close()
            self.logger.info('Disconnect from the storewize passed successfully')
        except:
            raise Exception, 'Error - failed to disconnect from %s' % self._config['storewize_ip']
        
    def exec_cmd(self,cmd):
        ''' Execute the command from the cmd '''
        self.stdin, self.stdout, self.stderr = self.ssh.exec_command(cmd)
        if self.stdout.channel.recv_exit_status() != 0:
            raise Exception, 'Error - failed to run "%s"' % cmd
        else:
            self.logger.info('command: "%s" passed successfully' % cmd)
        
    def get_volume_info(self, mdisk_name, set_size=True):
        ''' Retrieve the information from the storewize in order to configure the storage size to a volume'''
        cmd = 'lsmdiskgrp -delim :'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
            line_splited = line.strip().split(':')
            mdisk_name_from_storage = line_splited[1].strip()
            if mdisk_name_from_storage.lower() == mdisk_name.lower():
                mdisk_id = line_splited[0].strip()
                status = line_splited[2].strip()
                capacity = line_splited[7]
                _size = capacity[:-2]
                _type = capacity[-2:]
                capacity = '0'
                if set_size:
                    capacity = self.convert_to_mb(_size, _type)
                self.mdisks[mdisk_name]['mdisk_id'] = mdisk_id
                self.mdisks[mdisk_name]['status'] = status
                self.mdisks[mdisk_name]['capacity'] = _size
                self.mdisks[mdisk_name]['volume_cmd1'] = 'svctask mkvdisk -cache readwrite -copies 1 -iogrp io_grp0 -mdiskgrp %s -name %s -size %s -syncrate 50 -unit mb -vtype striped' % (mdisk_name,mdisk_name, capacity)
                raidparam = self.mdisks[mdisk_name]['raid_type'] == 'raid0' and '0' or '1'
                self.mdisks[mdisk_name]['mdisk_cmd2'] = 'svctask mkarray -drive %s -level %s -sparegoal %s %s' % (self.mdisks[mdisk_name]['drives'], self.mdisks[mdisk_name]['raid_type'],raidparam ,self.mdisks[mdisk_name]['mdisk_id'])
                self.mdisks[mdisk_name]['cleanup_cmd'] = 'svctask rmmdiskgrp -force %s' % self.mdisks[mdisk_name]['mdisk_id']
                
    def convert_to_mb(self, _size, _type):
        ''' Converse GB/TB to MB in order to put it in the volume creation '''
        self.logger.info('Converse GB/TB to MB in order to put it in the volume creation')
        self.logger.info('size: %s , type: %s' % (_size, _type))
        c_type = _type.lower()
        if c_type == 'gb':
            size = int(float(_size)*1024)
        elif c_type == 'tb':
            size = int(float(_size)*1024*1024)
        elif c_type == 'mb':
            size = _size
        return size 
        
    def run_mdisk(self):
        ''' This is the maim fuction '''
        self.logger.info('START the mdisk creation on storewize')
        self.disk_validation()
        import time
        self.connect()
        for mdisk_name, mdisk_info in self.mdisks.iteritems():
            self.exec_cmd(mdisk_info['mdisk_cmd1'])
            self.get_volume_info(mdisk_name, set_size=False)
            self.exec_cmd(mdisk_info['mdisk_cmd2'])
            time.sleep(2)
            self.get_volume_info(mdisk_name)
            self.exec_cmd(mdisk_info['volume_cmd1'])
        self.disconnect()
        
    def cleanup(self):
        ''' Clean all the storage configuration '''
        self.logger.info('Delete all the storewize configuration - ALL DATA DELETED !!!!!')
        self.connect()
        for mdisk_name, mdisk_id in self.mdisks.iteritems():
            self.get_volume_info(mdisk_name, set_size=False)
            self.exec_cmd(mdisk_id['cleanup_cmd'])
            
    def drive_ds(self):
        ''' Create drives data stracture for validation '''
        self.logger.info('START - Create drives data stracture for validation')
        self.drive_info = {}
        self.connect()
        cmd = 'lsdrive'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
            if not line.startswith('id'):
                line = line.strip().lower().split()
                slot_id = line[0].strip()
                drive_status = line[1].strip()
                drive_use = line[2].strip()
                drive_type = line[3].strip()
                if not self.drive_info.has_key(slot_id):
                    self.drive_info[slot_id] = {}
                self.drive_info[slot_id]['drive_status'] = drive_status
                self.drive_info[slot_id]['drive_use'] = drive_use
                self.drive_info[slot_id]['drive_type'] = drive_type
        self.logger.info('FINISHED - Create drives data stracture for validation')
        
    def get_configure_disks(self):
        ''' Get the disks from the configuration file in order to compare it to the drive on the storage '''
        self.logger.info('START - Get the disks from the configuration file in order to compare it to the drive on the storage')
        self._configure_disks = {}
        self.drives_mdisks = []
        for key, value in self._config.iteritems():
            if not key.startswith('mounts_') or not value:
                continue
            mounts = [m.strip() for m in value.split(',') if m.strip() ]
            for mdisk in mounts:
                mdisk_splited = mdisk.split(':')
                mdisk_name = mdisk_splited[0].strip()
                mdisk_drives = mdisk_splited[3].strip().lower()
                if not self._configure_disks.has_key(mdisk_name):
                    self._configure_disks[mdisk_name] = {}
                _drives = mdisk_drives.split('disks-')[1]
                configured_drives = _drives.split('-')
                self.drives_mdisks += configured_drives
                self._configure_disks[mdisk_name] = configured_drives
        self.logger.info('FINISHED - Get the disks from the configuration file in order to compare it to the drive on the storage')
        
    def disk_validation(self, validation_mode='init'):
        ''' Validate the file configuration against the physical drives on the storage '''
        self.candidate = []
        mode_drive_use = 'candidate'
        self.logger.info('START - Validate the file configuration against the physical drives on the storage')
        if validation_mode == 'inprogress':
            mode_drive_use = 'member'
        drives_ids_from_storage = self.drive_info.keys()
        drives_ids_from_config_file = self.drives_mdisks
        for drive_id in drives_ids_from_config_file:
            if drive_id in drives_ids_from_storage:
                dinfo = self.drive_info[drive_id]
                if dinfo['drive_type'] == 'sas_hdd' and not dinfo['drive_use'] == 'spare':
                    if not dinfo['drive_use'] == mode_drive_use:
                         raise Exception ('Drive id "%s" is should be on "%s" state' % (drive_id, mode_drive_use))
            else:
                raise Exception ('Drive id "%s" from config file is not exist on the storage' % drive_id) 
        self.logger.info('FINISHED - Validate the file configuration against the physical drives on the storage')
        
    def mapping(self):
        ''' map hosts to volume '''
        self.logger.info('START - mapping hosts to volume')
        self.host_mapping = {}
        for key, value in self._config.iteritems():
            if not key.startswith('host_key'):
                continue
            mounts = [m.strip() for m in value.split(',') if m.strip() ]
        self.logger.info('FINISHED - mapping hosts to volume')
            
class host_mapping(ibm_sizing):
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(host_mapping, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
   
    def __call__(self, *args, **kwargs):
        self.host_ds()
        self.create_host()
    
    def host_ds(self):
        ''' Retrive host info '''
        self.host_info = {}
        self.remote_nportid = []
        self.connect()
        cmd = 'lsfabric'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
             if not line.startswith('remote_wwpn'):
                line = line.strip().split()
                remote_wwpn = line[0].strip()
                remote_nportid = line[1].strip()
                type = line[8].strip()
                if not self.host_info.has_key(remote_wwpn):
                    self.host_info[remote_wwpn] = {}
                self.host_info[remote_wwpn]['remote_wwpn'] = remote_wwpn
                self.host_info[remote_wwpn]['remote_nportid'] = remote_nportid
                self.host_info[remote_wwpn]['type'] = type
                self.remote_nportid.append(remote_nportid)
        self.logger.info('FINISHED - retrieving host info from storewize')
        
        
    def create_host(self):
            ''' Create the host on the storage '''
            x = 'null'
            self.connect()
            cmd = 'lshost'
            self.exec_cmd(cmd)
            for i in range(6):
                dir_name = '/sys/class/fc_host/host%s' % i
                if (os.path.exists(dir_name)):
                    port_id_file = open(dir_name + '/port_id', 'r')
                    _port_id_file = port_id_file.readline().strip().upper()
                    self.remote_nportid = list(set(self.remote_nportid))
                    for r_id in self.remote_nportid:
                        if r_id in _port_id_file:
                            for remote_wwpn in self.host_info:
                                if self.host_info[remote_wwpn]['remote_nportid'] == r_id and self.host_info[remote_wwpn]['type'] == 'unknown':
                                    self.logger.info('The server name is: %s and the remote_wwpn ID is: %s' % (self._config['server_key'],remote_wwpn))
                                    cmd = 'svctask mkhost -name %s -fcwwpn %s -force -type generic' % (self._config['server_key'],remote_wwpn)
                                    if x not in remote_wwpn:
                                        self.exec_cmd(cmd)
                                        x = remote_wwpn
                                        time.sleep(2)
                                    
class mapping(ibm_sizing):

    ''' This class configure the storewize storage according configuration file '''
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(mapping, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):

        self.alias_ds()
        self.conf_multipath()
        self.build_mdisk_ds()
        self.mapping_ds()
        self.create_mapping()

    def alias_ds(self):
        ''' Create alias for multipath.conf file '''
        self.logger.info('START - Creating alias for multipath.conf file')
        self.alias_info = {}
        self.connect()
        cmd = 'svcinfo lsvdisk'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
             if not line.startswith('id'):
                line = line.strip().split()
                slot_id = line[0].strip()
                drive_mdisk_grp_name = line[6].strip()
                drive_vdisk_UID = line[9].lower().strip()
                if not self.alias_info.has_key(slot_id):
                    self.alias_info[slot_id] = {}
                self.alias_info[slot_id]['drive_mdisk_grp_name'] = drive_mdisk_grp_name
                self.alias_info[slot_id]['drive_vdisk_UID'] = '3'+drive_vdisk_UID
        self.logger.info('FINISHED - Creating alias for multipath.conf file')

    def conf_multipath(self):
        self.logger.info('Adding multipathd to startup')
        iCommander = ['chkconfig multipathd on']
        multipath_path = '/etc/multipath.conf'
        multipath_file = open(multipath_path,'w')
        multipath_conf = ''
        multipath_template = '''### MIH multipath for IBM storewize 3700 ###


###
###
## Defaults
defaults {
     polling_interval    30
     failback            immediate
     no_path_retry       5
     rr_min_io           100
     path_checker        tur
     user_friendly_names yes
}
## blacklist
blacklist {
    devnode "^(ram|raw|loop|fd|md|dm-|sr|scd|st)[0-9]*"
        devnode "^hd[a-z]"
        devnode "^cciss!c[0-9]d[0-9]*"
}

## devices
devices {
    device {
          vendor  "IBM"
          product  "2145"
          path_grouping_policy group_by_prio
         }
    }  
## multipathes
     multipaths { '''

        multipath_conf += multipath_template
        for id,alias in self.alias_info.iteritems():
            mutipath_alias_template  = '''         
            multipath {
                no_path_retry           fail
                wwid                    %s
                alias                   %s
                    } ''' % (alias['drive_vdisk_UID'],alias['drive_mdisk_grp_name'])

            multipath_conf += mutipath_alias_template
        multipath_conf += '\n\t\t}'
        multipath_file.write(multipath_conf)
        multipath_file.close()
        self.logger.info('Configured /etc/multipath.conf file')

    def mapping_ds(self):
        ''' Mapping the volumes to the hosts '''
        self.logger.info('START - Retrieving host id from storage')
        self.mapping_ds = {}
        cmd = 'lshost'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
            if not line.startswith('id'):
                line = line.strip().split()
                host_id = line[0].strip()
                name = line[1].strip()
                mapped_host_id = '%s:%s' % (name, host_id) 
                if not self.mapping_ds.has_key(mapped_host_id):
                    self.mapping_ds[mapped_host_id] = []
                    self.logger.info('START - Drive id from storage')
                    cmd = 'svcinfo lsvdisk'
                    self.exec_cmd(cmd)
                    for line in self.stdout.read().splitlines():
                        if not line.startswith('id'):
                            line = line.strip().split()
                            drive_id = line[0]
                            self.mapping_ds[mapped_host_id].append(drive_id)
        self.logger.info('FINISHED - building mapping data structure')

    def create_mapping(self):
        self.connect()
        self.logger.info('Retrieving the mdisk info from the storage')
        self.logger.info('START - Creating mapping drive to host')
        for host_key in self.mapping_ds:
            host_id = host_key.split(":")[1]
            host_name = host_key.split(":")[0]
            if host_name == self._config['server_key']:
                for drive in self.mapping_ds[host_key]:
                    cmd = 'svctask mkvdiskhostmap -force -host %s %s' % (host_id,drive)
                    self.exec_cmd(cmd)
        self.disconnect()
        self.trigger_fc()
        self.logger.info('FINISHED - Creating mapping drive to host')

    def trigger_fc(self):
        for i in range(6):
            dir_name = '/sys/class/fc_host/host%s' % i
            self.logger.info('START - Triggering FC hosts')
            if (os.path.exists(dir_name)):
                subprocess.call('echo "1" >' + dir_name + '/issue_lip', shell=True)
                self.logger.info('Trigger FC with %s' % dir_name)
            self.logger.info('Folder %s not exist' % dir_name)
        self.logger.info('stop/start Multipathd')
        subprocess.call('service multipathd stop', shell = True)
        time.sleep(10)
        subprocess.call('service multipathd start', shell = True)

    def clean_host(self):
        ''' Clean the host from the storage '''
        self.logger.info('START - Cleaning hosts from the storage')
        self.host_id = {}
        self.connect()
        self.logger.info('Retrieving host id from storage')
        cmd = 'lshost'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
            if not line.startswith('id'):
                line = line.strip().split()
                _host_id = line[0].strip()
                _host_name = line[1].strip()
                self.logger.info('delete running hostname: %s ...' % _host_id)
                cmd = 'svctask rmhost -force %s' % _host_id
                self.exec_cmd(cmd)
        self.logger.info('Flush (from memory) Multipath Configuration')
        subprocess.call('multipath -F', shell=True)
        self.logger.info('FINISHED - Cleaning hosts from the storage')

class mdisk_validation(ibm_sizing):
    ''' This class compare between the storage mdisks to system.ini '''
       
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(mdisk_validation, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

    def __call__(self, *args, **kwargs):
        self.drive_ds()
        self.get_configure_disks()
        self.build_mdisk_ds()
        self.validate()
     
    def validate(self):
        self.disk_validation(validation_mode='inprogress')
        self.connect()
        self.logger.info('Retrieving the mdisk info from the storage')
        storage_mdisk = []
        cmd = 'lsmdiskgrp'
        self.exec_cmd(cmd)
        for line in self.stdout.read().splitlines():
            if not line.startswith('id'):
                line = line.strip().split()
                mdisk_grp_name = line[1]
                storage_mdisk.append(mdisk_grp_name)
        mdisk_from_config_file = self.mdisks.keys()
        for name in mdisk_from_config_file:
            if name not in storage_mdisk:
                count = 1
                total_retries = self._config.get('validate_retries', 2)
                time_to_sleep = self._config.get('validate_sleep_time', 3)
                self.logger.info('attempting to validate mdisk accroding to configuration: %s from %s' % (count, total_retries))
                for c in range(1, total_retries):
                    time.sleep(time_to_sleep)
                    for i in mdisk_from_config_file:
                        if i not in storage_mdisk:
                            count += 1
                            break;
                if count == total_retries:
                    raise Exception ('check the configuration file: The mdisk %s not exist on Storage' % i)
