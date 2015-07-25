#!/usr/bin/env python

###############################
#   Date: 10/03/2015          #
#   FileName: installer.py    #
#   Written By: Nati Malka    #
###############################

import sys, os, re
from Pyrunner import *
from pdb import set_trace as st
from glob import glob
from section import *
from Pyrcommander import remote_commander 
from Pymodule import Pylogger
import traceback
from Pytraceback import tb_frame_locals
from copy import deepcopy
from plogin import get_login_info
from section import *
from dist_config import STATUS_CMD_FILE
DEBUG = False

def get_logger(config):
    if config['EnableRotateLog'] == '1':
        logger = Pylogger(logFile=config['LogFile'],
            logLevel=config['LogLevel'],
            rotate=config['EnableRotateLog'],
            maxBytes=int(config['MaxKBytes'])*1024,
            backupCount=int(config['BackupCounts']),
            loggerName=''
            )

        logger.error("\n\n################## Installer Script ###############\n")
        logger.error("LogFile will rotate each %s[Kbytes], with maximum of %s files" % \
            (config['MaxKBytes'], config['BackupCounts']))
    else:
        logger = Pylogger(logFile=config['LogFile'],
            logLevel=config['LogLevel'],
            rotate=config['EnableRotateLog'],
            loggerName=''
            )
    return logger
    
def priority_sort(x, y):
    _x = x['pr']
    _y = y['pr']
    iX = int(_x)
    iY = int(_y)
    return cmp(iX, iY)

def set_global_config(config):
    config['set_all_option'] = False
    config['database_file'] = '/data_local/Python/Installer/RunnerDb.sqlite'
    config['buffer_file'] = '/data_local/Python/.installer_buff'
    config['status_file'] = '/data_local/Python/Installer/.status_file_buff'
    config['install_types'] = ['-install', '-upgrade',]
    config['install_script_options'] = { '--mount' : 'False', '--rpm_pre_install' : 'False', '--rpm_post_install' : 'False', '--pre_runners' :'False' , '--post_runners' :'False' }
    config['upgrade_script_options'] = {'--mount' : 'False' ,  '--rpm_upgrade' : 'False' , '--pre_runners' : 'False', '--post_runners' : 'False' }
    config['modes'] = ['upgrade', 'install', 'server_utils']
    config['exection_order'] = {'install': ['mount', 'rpm_pre_install', 'pre_runners', 'rpm_post_install', 'post_runners' ],
                                'upgrade': ['mount', 'rpm_upgrade', 'pre_runners' , 'post_runners'] }
    config['lock_file_dir'] = os.path.join(os.path.realpath(os.path.dirname(sys.argv[0])), '.runner')
    if not os.path.isdir(config['lock_file_dir']): os.mkdir(config['lock_file_dir'], 0750)
    config['lock_file'] = os.path.join(config['lock_file_dir'], '%s_installer.pid' % os.getpid())
    config['script_name'] =  os.path.basename(sys.argv[0])
    config['section'] = Section
    config['LogFile'] = config.get('LogFile', '/data_local/Python/Installer/installer.log')
    config['installer'] = True
    config['installer_output'] = True
#    config['RemotePrintToScreen'] = True



    install_mapping = {}
    install_mapping['distribute'] = ['']
    config['install_mapping'] = install_mapping
    return config    

def init_config(config={}, script_arg=[]):

    # init default configguration
    config = set_global_config(config)
    for a in script_arg:
        arg = a.strip()          
        if re.match('--config_file', arg):
            config_file = arg.split('=')[1]
            config['config_file'] = config_file
        elif re.match('--all', arg): 
            config['set_all_option'] = True 
        elif re.match('-\w', arg):
            config['selected_install_type'] = [arg, ]
        elif re.match('--\w', arg):
            if a.__contains__('='):
                _arg = a.split('=')
                arg = _arg[0].strip()
                if not _arg[1].strip():
                    _force = 'False'
                elif _arg[1].strip().lower() == 'force':
                    _force = 'True'
            else:
                _force = 'False'

            if not config.has_key('selected_options'):
                config['selected_options'] = { arg :  _force }
            else:
                config['selected_options'][arg] = _force 
  
    return config 

def update_config(config):
    _config = {} 
    # update from config file
    _config['iso_path'] = config.get('iso_path', '/var/tmp')
    _config['remote_file'] = config.get('remote_file', '')
    _config['iso_extract_path'] = config.get('iso_extract_path', '/var/RPMs/%s')
    _config['iso_mount'] = config.get('iso_mount', '/tmp/Installer')
    _config['iso_regex'] = config.get('iso_regex', '^(PATCH|SW)_(%s|MIH|LOADER).+\.iso')
    _config['mih_iso_regex'] = '^SW_MIH-([0-9]\.[0-9]\.[0-9])-STF([0-9]+).([0-9]+).iso'
    _config['iso_wildcard'] = config.get('iso_wildcard', '*.iso')
    # Remote commnader parametres
    _config['execution_mode'] = config.get('execution_mode', 'section_by_section')
    _config['RemotePrintToScreen'] = config.get('RemotePrintToScreen',False)
    _config['printSummaries'] = config.get('printSummaries',False)
    _config['deploy_invoke_order'] = config.get('deploy_invoke_order', ['execute',])
    # logger params
    _config['LogLevel'] = config.get('LogLevel', '0') 
    _config['EnableRotateLog'] = config.get('EnableRotateLog', '1') 
    _config['MaxKBytes'] = config.get('MaxKBytes', '20000') 
    _config['BackupCounts'] = config.get('BackupCounts', '5') 
    
    config.update(_config)

    return config

def get_iso_info(config):
    mih_iso =  [ iso for iso in glob(os.path.join(config['iso_path'], config['iso_wildcard'])) if os.path.isfile(iso) and re.search(config['iso_regex'], os.path.basename(iso))]
    
    if len(mih_iso) > 1:
        raise Exception, 'Only one iso can be under %s folder for %s.\nCurrent ISO\'s:%s' % (config['iso_path'],config['selected_install_type'],mih_iso ) 

    elif len(mih_iso):
        mih_reg_obj = re.search(config['mih_iso_regex'], os.path.basename(mih_iso[0]))
        if mih_reg_obj != None:
            config['mih_iso']  = { 'full_path' : mih_iso[0] ,'name' : os.path.basename(mih_iso[0]), 'ISO' : 'MIH'}
            config['mih_iso']['version'] = mih_reg_obj.group(1)
            config['mih_iso']['stf'] = mih_reg_obj.group(2)
            config['mih_iso']['sub_version'] = mih_reg_obj.group(3)
            config['iso_extract_path'] = config['iso_extract_path'] % '%s-%s-%s' % ( config['mih_iso']['ISO'], config['mih_iso']['version'], 'STF%s' % config['mih_iso']['stf'])
            config['remote_file'] = config['mih_iso']['full_path']
        else:
            raise Exception, 'Regex doesn\'t match, couln\'t found MIH ISO under %s.' % config['iso_path']
    elif len(mih_iso) <= 0:
        raise Exception, 'Couln\'t found MIH ISO under %s.' % config['iso_path']
    

def validate_script_options(config):
    if config.has_key('config_file'):
        try:
            if config['config_file'].endswith('.py'):
                if not os.path.isfile(config['config_file']):
                    raise Exception, 'No such file: \"%s\"' % config['config_file']
            _config = {}
            execfile(config['config_file'], {}, _config)
            config.update(_config)
            config = update_config(config)
        except:
            RemovePidLockFile(config['lock_file'])
            print >> sys.stderr,"Failed to load installer configuration file: %s" % (config['config_file'])
            raise
    else:
        config = update_config(config)
    if len(config['selected_install_type']) > 1:
        print 'Installation Type Error: Only ONE install type should be given. %s\nPlease select only ONE fron the valid install types: %s.' % \
               (config['selected_install_type'],config['install_types'])
        sys.exit(111)
    if config['selected_install_type'][0] not in config['install_types']:
        print 'Invalid Installation Type Error: %s install type is not valid.\nValid install types are:%s' % (config['selected_install_type'], config['install_types'])
        sys.exit(111)  
   
    config['selected_install_type'] = config['selected_install_type'][0].split('-')[1]
    install_type = config['selected_install_type']
    if config['set_all_option']:
        config['selected_options'] =  config['%s_script_options' % install_type]

    selected_options = config['selected_options'].keys()
    scripts_options = config['%s_script_options' % install_type].keys()
    for i_option in selected_options:
        if i_option not in scripts_options:
             print 'Invalid %s Option Error: %s option is not valid.\n%s Valid options are:%s' % (install_type.title(), i_option, install_type.title() ,scripts_options)
             sys.exit(111)

    return config 


        
def get_runners_from_db(config):
    import sqlite3 as lite
    RunnerInvokers= {}
    con = lite.connect(config['database_file'])
    cur = con.cursor()
    cur.execute("SELECT r.id, r.priority, r.exit_status, r.time_out, r.ignore_timeout, r.cmd_wrapper, r.name, r.cmd_output_regex_id AS runner_name, app.mode  AS app_name, m.name AS mod_name, r.cmd, r.type, reg.regex AS regex FROM runner_runnerinvoke r , runner_runnerinvoke_apps rapp, runner_runnerinvoke_modes rmod, runner_runnerregex reg JOIN runner_packagemode app ON (rapp.runnerinvoke_id = r.id and rapp.packagemode_id = app.id) JOIN runner_runnermode m ON (rmod.runnerinvoke_id = r.id and rmod.runnermode_id = m.id) where r.cmd_output_regex_id = reg.id and  r.active = 1")
    rows = cur.fetchall()
    #count = 0
    runner_invke_ids = {}
    for row in rows:
        mod = row[9]
        
        if mod in config['modes']:
            if mod not in RunnerInvokers.keys():
                RunnerInvokers[mod] = {}
            if mod not in runner_invke_ids.keys():
                runner_invke_ids[mod] = []
            if row[11]:
                if row[11] not in RunnerInvokers[mod].keys():
                    RunnerInvokers[mod][row[11]] = []
                if row[0] not in runner_invke_ids[mod]:
                    #runner = {'id' : row[0] , 'pr' : row[1], 'exit_status' : row[2],  'time_out' : row[3], 'ignore_timeout' : row[4], 'cmd_wrapper' : row[5], 'cmd_output_regex_id' : row[6],  'runner_name' :  row[7], 'app' : row[8], 'mod' : row[9],  'cmd' :  row[10], 'type' : row[11], 'cmd_output_regex' : ''}
                    runner = {'id' : row[0] , 'pr' : row[1], 'exit_status' : row[2],  'time_out' : row[3], 'ignore_timeout' : row[4], 'cmd_wrapper' : row[5], 'runner_name' :  row[6], 'cmd_regex_id' : row[7], 'app' : row[8], 'mod' : row[9],  'cmd' :  row[10], 'type' : row[11], 'cmd_output_regex' : ''}
                    if row[7]:
                        runner['cmd_output_regex'] =  row[12]
                    RunnerInvokers[mod][row[11]].append(runner)
                #count = count + 1
                if row[0] not in runner_invke_ids[mod]:
                    runner_invke_ids[mod].append(row[0])
    for install_type, runners_list in RunnerInvokers.iteritems():
        for t, rlist in runners_list.iteritems():
            rlist.sort(priority_sort) 

    return RunnerInvokers


def init_last_exection_from_buffer_file(config):
    fileCorrupted = False
    buffer = {}
    buffer_file = config['buffer_file']
    f = os.path.expanduser(buffer_file)
    if os.path.isfile(f):
        try:
            mylogger(config).debug('Reading buffer params from %s file.' % f)
            execfile(f, {}, buffer)
            if buffer.has_key('buffer'):
                config['already_executed'] = buffer['buffer']
        except:
            fileCorrupted = True
            mylogger(config).error('The %s buffer is corrupted, Build buffer file from scratch.' % f)
    if fileCorrupted or not os.path.isfile(f):
        config['already_executed'] =  {'install': [], 'upgrade': [] }
    return config

def init_cmd_status_file(config):
    fileCorrupted = False
    status = {}
    buffer_file = config['status_file']
    f = os.path.expanduser(buffer_file)
    if os.path.isfile(f):
        try:
            mylogger(config).debug('Reading buffer params from %s file.' % f)
            execfile(f, {}, status)
            if status.has_key('status'):
                config['commands_status'] = status['status']
        except:
            fileCorrupted = True
            mylogger(config).error('The %s buffer is corrupted, Build buffer file from scratch.' % f)
    if fileCorrupted or not os.path.isfile(f):
        config['commands_status'] =  {}
    return config

def update_status_cmd(config):
    status = {}
    buffer_file = STATUS_CMD_FILE
    f = os.path.expanduser(buffer_file)
    if os.path.isfile(f):
        try:
            mylogger(config).debug('Reading buffer params from %s file.' % f)
            execfile(f, {}, status)
            if status.has_key('status'):
                config['commands_status'].update(status['status'])
        except:
            fileCorrupted = True
            mylogger(config).error('The current execution %s buffer is corrupted, Build buffer file from scratch.' % f)
            write_cmd_status_to_files(config['commands_status'])
        write_cmd_status_to_files(config['commands_status']) 
       
    return config

def write_cmd_status_to_files(commands):
    try:
        f = open(config['status_file'] , 'w')
        f.write("status = %s" % commands)
        f.close()
    except:
        raise Exception, 'Couln\'t write status cmd to buffer file.'


def get_my_applist(app_type='--'):
    my_applist = _(Section, 'my_applist')
    if app_type == '--':
        my_applist = ' --'.join(my_applist)
        my_applist = '--%s' % my_applist
    return my_applist

def build_runners_list(config):
    exection_runners = []
    #exection_order_runners = config['exection_order']
    selected_install_type = config['selected_install_type']
    runners = config['runner_invokers'][selected_install_type]
    already_executed = config['already_executed']
    selected_options = config['selected_options']
   
    
    _force = False
    if '--mount' in selected_options.keys():
        if '--mount' in already_executed[selected_install_type]:
            if selected_options['--mount'] == 'False':
                print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'mount')
            else:
                _force = True
        if '--mount' not in already_executed[selected_install_type] or _force:
            runners['mount'][0]['cmd'] = runners['mount'][0]['cmd'] % { 'mount_dst' : config['iso_mount'] , 'iso_extract_dst' : config['iso_extract_path'],
                                         'remote_file'  :  config['remote_file'] }
            exection_runners.append(runners['mount'][0])
            _force = False

    back_pre_rpm_cmd_for_post =  deepcopy(runners['pre'][0])
    if selected_install_type == 'install':
        if '--rpm_pre_install' in selected_options.keys():
            if '--rpm_pre_install' in already_executed[selected_install_type]:
                if selected_options['--rpm_pre_install'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'rpm_pre_install')
                else:
                    _force = True
            if '--rpm_pre_install' not in already_executed[selected_install_type] or _force:
                runners['pre'][0]['cmd'] = runners['pre'][0]['cmd'] % ( config['iso_extract_path'] ,get_my_applist())
                exection_runners.append(runners['pre'][0])
                _force = False
        if '--pre_runners' in selected_options.keys(): 
            if '--pre_runners' in already_executed[selected_install_type]:
                if selected_options['--pre_runners'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'pre_runners')
                else:
                    _force = True
            if '--pre_runners' not in already_executed[selected_install_type] or _force:
                for i in range(1, len(runners['pre'])):
                    exection_runners.append(runners['pre'][i])

                _force = False
        if '--rpm_post_install' in selected_options.keys():
            if '--rpm_post_install' in already_executed[selected_install_type]:
                if selected_options['--rpm_post_install'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'rpm_post_install')
                else:
                    _force = True
            if '--rpm_post_install' not in already_executed[selected_install_type] or _force:
                back_pre_rpm_cmd_for_post['cmd'] =  back_pre_rpm_cmd_for_post['cmd'] + ' %s'
                back_pre_rpm_cmd_for_post['cmd'] = back_pre_rpm_cmd_for_post['cmd'] % ( config['iso_extract_path'], '-post' ,get_my_applist())
                back_pre_rpm_cmd_for_post['runner_name'] = 'post_rpm_install'
                exection_runners.append(back_pre_rpm_cmd_for_post)
                _force = False
        if '--post_runners' in selected_options.keys():     
            if '--post_runners' in already_executed[selected_install_type]:
                if selected_options['--post_runners'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'post_runners')
                else:
                    _force = True
            if '--post_runners' not in already_executed[selected_install_type] or _force:
                for i in range(1, len(runners['post'])):
                    exection_runners.append(runners['post'][i])
                for run in runners['post']:
                    exection_runners.append(run)

                _force = False

    elif selected_install_type == 'upgrade':
        if '--rpm_upgrade' in selected_options.keys():
            if '--rpm_upgrade' in already_executed[selected_install_type]:
                if selected_options['--rpm_upgrade'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'rpm_upgrade')
                else:
                    _force = True
            if '--rpm_upgrade' not in already_executed[selected_install_type] or _force:
                runners['pre'][0]['cmd'] = runners['pre'][0]['cmd'] % ( config['iso_extract_path'] ,get_my_applist())
                exection_runners.append(runners['pre'][0])
                _force = False
        if '--pre_runners' in selected_options.keys():     
            if '--pre_runners' in already_executed[selected_install_type]:
                if selected_options['--pre_runners'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'pre_runners')
                else:
                    _force = True
            if '--pre_runners' not in already_executed[selected_install_type] or _force:
                for i in range(1, len(runners['pre'])):
                    exection_runners.append(runners['pre'][i])
                _force = False
        
        if '--post_runners' in selected_options.keys(): 
            if '--post_runners' in already_executed[selected_install_type]:
                if selected_options['--post_runners'] == 'False':
                    print '%s execution, %s already executed successully, Skipping!!' % (selected_install_type.title(),'post_runners')
                else:
                    _force = True
            if '--post_runners' not in already_executed[selected_install_type] or _force:
                for run in runners['post']:
                     exection_runners.append(run)

                _force = False

        
    config['exection_runners'] = exection_runners
    return config
    
     
def pprint_runners_from_db(config):
    selected = config['runner_invokers']
    for k, v in selected.iteritems():
        print '######### %s ######### \n' % k.upper()
        for key, val in v.iteritems():
            print '    ######### %s ##########\n' % key.upper()
            for _v in val:
                print '    pr: %s, app: %s, cmd: %s' %(_v['pr'], _v['app'], _v['cmd'])
            print "\n"
        
def pprint_selected_runners(config):
    section = config['section']
    selected = config['iRemoteCommander'][0][section] 
    for k, v in selected.iteritems():
        print '\n######### Going to execute on [%s]  ######### \n' % k.upper()
        commands = v['commands']
        for cmd in commands:
            print '[%s] -  %s' % (cmd['name'] , cmd['cmd'])
            mylogger(config).info('[%s] -  %s\n' % (cmd['name'] , cmd['cmd'])) 
        


def get_my_ip(config):
    MYADMIN_NETWORK = _D(Section,server_key,'%s_network' % ADMIN_NETWORK ,ADMIN_NETWORK)
    EDN_LocalIP = _(Section,server_key,Key=MYADMIN_NETWORK)
    return EDN_LocalIP

def build_deploy_exection(config):
    iRemoteCommander = []
    section = config['section']
    ip = get_my_ip(config)
    config['iData'] = get_login_info(iData)
    config.update(config['iData'])
    title = { section : {} }
    title[section][ip] = {'ip' : ip }
    my_applist = get_my_applist(app_type='')
    commands = []
    template_command = { 'name' : '', 'cmd' : '', 'save_cmd_status' : True, 'exit_status': [0], 'cmd_output_regex': '', 'ignore_timeout': False, 'cmd_regex': [], 'time_out': 0, 'printToScreen' : True }
    for cmd in config['exection_runners']:
        if cmd['runner_name'] in config['commands_status'].keys():
            mylogger(config).error('Skipping the follow command execution, due previously successfully execution')
            mylogger(config).error('Skipping command "%s".' %  config['commands_status'][cmd['runner_name']])
            continue
        if cmd['app'] not in my_applist:
            continue
        if cmd['cmd_wrapper'] and not cmd['cmd'].startswith(cmd['cmd_wrapper']):
            cmd['cmd'] = '%s "%s"' % (cmd['cmd_wrapper'], cmd['cmd'])
        cmd_to_add = deepcopy(template_command)
        cmd_to_add['name'] = cmd['runner_name'] 
        cmd_to_add['cmd'] = cmd['cmd'] 
        cmd_to_add['exit_status'] = cmd['exit_status'] 
        cmd_to_add['cmd_output_regex'] = cmd['cmd_output_regex'] 
        cmd_to_add['ignore_timeout'] = cmd['ignore_timeout'] 
        cmd_to_add['time_out'] = cmd['time_out'] 
        cmd_to_add['cmd_wrapper'] = cmd['cmd_wrapper'] 
        commands.append(cmd_to_add)
        print cmd_to_add

    if not len(commands):
        mylogger(config).error("The list of commands to execute is empty, due previously successfully execution.")
        print "The list of commands to execute is empty, due previously successfully execution.\nPlease see the installer log file %s for more details." % config['LogFile']
        print "In order to force and rerun again, please delete the %s file." %  config['status_file']
        sys.exit(0)
        
    #print '########################################################################\n\n\n'
    title[section][ip]['commands'] = commands
    iRemoteCommander.append(title)
    config['iRemoteCommander'] = iRemoteCommander
    return config

PyPath = ['/data_local/Python/Pymodules','/data_local/Python/funcPy']
for path in PyPath:
    if path not in sys.path:
        sys.path.append(path)


def mylogger(config):
    return config['log']

def execute_runners(config):
    
    componentID = config['section']
    #print dir(get_logger(config))
    try:
        instance = remote_commander(config=config, loggerName=mylogger(config).name, componentID=componentID, Args=[])
        #instance = locals()['remote_commander'](config=config, componentID=componentID, Argv=Argv)
        instance()
    except:
        update_status_cmd(config)
        #mylogger(config).debug(tb_frame_locals(DEBUG))
        mylogger(config).error(traceback.format_exc())
        mylogger(config).error('Installer script  was failed. Bye Bye!')
        #print tb_frame_locals(DEBUG)
        print traceback.format_exc()
        RemovePidLockFile(config['lock_file'])
        sys.exit(111) 
        #print traceback.format_exc()
        #print tb_frame_locals(DEBUG)
        #print sys.exc_info()[0], sys.exc_info()[1]
        #if config.get('i_output', ''):
        #print config['i_output']

######### MAIN ########
try:
    install_option = sys.argv[1]
    script_option = sys.argv[2]
    script = os.path.basename(sys.argv[0])
except:
    print >> sys.stderr,"Usage: %s <-installation type mode> <--option> ....\n<-installation type mode> Only one install type reqiured, <--option> At least one option reqiured." % (os.path.basename(sys.argv[0]))
    sys.exit(111)

config = init_config(config={}, script_arg=sys.argv)
config = validate_script_options(config)
my_logger = get_logger(config)
config['log'] = my_logger

# Lock installer script
RunnerPidCheck(config['lock_file_dir'], config['script_name'])
lfh = open(config['lock_file'], 'w')
lfh.close()

config['runner_invokers'] = get_runners_from_db(config)
config = init_last_exection_from_buffer_file(config)
config = init_cmd_status_file(config)
#pprint_runners_from_db(config)
get_iso_info(config)
config = build_runners_list(config)
config = build_deploy_exection(config)
execute_runners(config)
update_status_cmd(config)
pprint_selected_runners(config)
mylogger(config).error("#####  Script ended successfully.  #####\n")
print "\n\t\t#####  Script ended successfully.  #####\n"

RemovePidLockFile(config['lock_file'])
