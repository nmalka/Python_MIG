# Default admin network
ADMIN_NETWORK = 'EDN'

# Default wireless network
WIRELESS_NETWORK = 'WDN' 

# Default V6 network
V6_NETWORK = 'V6WDN'

# used for execfile.
COREPY_PATH = '/data_local/Python/corePy'
#APP CONFIG section
NET_SUPPORT_SECTIONS = ['APP_CONFIG','GENERAL','SNMP']
# host_key_detect delimiter.
HOST_DELIMITER = '|'

# Default setup for pre-define sections:
# Data: DEFAULTS_APPS = {'SECTION' : ['app1', app2'],}
DEFAULT_APPS = {}

# Additional app list that will be added automatic for each application installrd on server.
CORE_APPS = {'spm' : ['java','tomcat', 'jboss', 'oracle_client', 'oracle'],
            'mpm_schema' : ['oracle_server', 'oracle','onguard'],
            'cognos' : ['epr', 'cogapi', ],
            'weblinksdb' : ['oracle_server', 'oracle', 'onguard',],
            'db2' : ['epr', 'db2_schema'],
            'opm' : ['epr', 'opm_main', 'opm_master'],
            'documentation' : ['java','tomcat',],
            'dashboard' : ['java','tomcat',],
            'babysitter' : ['java','tomcat',],
            'sm' : ['oracle_client', 'oracle'],
            'oracle_client' : ['oracle'],
            'oracle_server' : ['oracle'],
            'rhel' : ['system_monitor'],
            'mgmd' : ['mysql'],
            'ndbd' : ['mysql'],
            'cdc' : ['oracle_server', 'oracle'],
            }

# Additional global app list that will be added automatic for each application depending on global app on the systrem.
GLOBAL_CORE_APPS = {'epr' : [{'required_by' : 'mpm_schema', 
                             'required' : ['subinfo_to_epr',]
                             }, 
                             {'required_by' : 'spm',
                              'required' : ['spm_to_epr']
                             },
                             {'required_by' : 'cdrmgr',
                              'required' : ['cdr_to_epr']
                             },
                             {'required_by' : 'dpi',
                              'required' : ['dpi_to_epr'],
                              },
                             {'required_by' : 'weblinks',
                              'required' : ['cognos_link'],
                              },
                             {'required_by' : 'edr',
                              'required' : ['edr_to_epr'],
                              },
                             {'required_by' : 'sm',
                              'required' : ['sdr'],
                              },
                             {'required_by' : 'sdr',
                              'required' : ['sdr_to_epr'],
                              },
                             {'required_by' : 'nag',
                              'required' : ['nag_to_epr'],
                              },
                             {'required_by' : 'dashboard_offline',
                              'required' : ['dash_to_epr'],
                              },
                            ],
                    'edrmng' : [ {'required_by' : 'edr',
                                 'required' : ['edr_to_edrmng',]
                                 },
                                 ],
                    'cdr_push' : [ {'required_by' : 'management',
                                 'required' : ['cdr_push_monitor',]
                                 },
                                 ],
                    'cogapi_push' : [ {'required_by' : 'management',
                                 'required' : ['cogapi_push_monitor',]
                                 },
                                 ],
                    'edr_push' : [ {'required_by' : 'edrmng',
                                 'required' : ['edr_push_monitor',]
                                 },
                                 ],
                    'cdrmgr' : [ {'required_by' : 'management',
                                 'required' : ['cdrmgr_monitor',]
                                 },
                               ], 
                    'edr' : [ {'required_by' : 'etl',
                                 'required' : ['edr_zip_unzip',]
                                 },
                                 ],

    }

# Required apps for application. will raise exception if omitted.
INCLUDED_APPS = {'dpi' : ['spm',],
                 'subinfo_to_epr' : ['mpm_schema',],
                 'spm_to_epr' : ['spm',],
                 'cdr_to_epr' : ['cdrmgr'],
                 'dash_to_epr' : ['dashboard'],
                 'squid' : ['gw',],
                 'gwsec' : ['gw',],
                 'iusi' : ['sm',],
                 }

# Additional app list that will be added automatic for all servers within all server sections.
UI_LIST = []
MIH_LIST = ['mih_python_lib', 'runner_confpy', 'mih_python_scripts']

UI_APPS = {'MNGS' : UI_LIST + MIH_LIST,
           'GLOBAL' : UI_LIST + MIH_LIST,
           'MDSUAPP' : UI_LIST + MIH_LIST,
           'MDSU' : UI_LIST + MIH_LIST,
           'RAC' : UI_LIST + MIH_LIST,
           'MWAS' : UI_LIST + MIH_LIST,
           'PCRF' : UI_LIST + MIH_LIST,
           'XIM' : UI_LIST + MIH_LIST,
           'PRE' : UI_LIST + MIH_LIST,
           'CDRC' : UI_LIST + MIH_LIST,
           'TM' : UI_LIST + MIH_LIST,
           'EPR' : UI_LIST + MIH_LIST,
           'PPG' : UI_LIST + MIH_LIST,
           'UAPROF' : UI_LIST + MIH_LIST,
           'CANFS' : UI_LIST,
           'CALOG' : UI_LIST,
           'CAPROXY' : UI_LIST,
           'CAREPORTS' : UI_LIST,
           'BACKUP' : UI_LIST,
           'DPI' : [],
           'MOBIXELL' : [],
           'COMMANDER' : UI_LIST,
           'VSIX' : UI_LIST,
           'WEB' : UI_LIST,
           'ATL' : UI_LIST,
           'LOAD' : UI_LIST,
           'SPYDER' : UI_LIST,
           }
