
# Author: Dan A.
# Dan.Avrukin@comverse.com
# Modified: 16.11.2009
# Purpose: Automatic ntpd configuration.
# Notes: Commited to the SVN.

from Pyfiledit import builder
from Pyconf import HashParser
from Pyfunc import Red, Ylw, Grn, Blu, ConstDict, DigHostsIP
from os.path import join, exists
from os import remove, system
from re import search, match
from commands import getoutput as go

class ntp_config(builder, HashParser):
    def __init__(self, config, componentID, loggerName = '', *args, **kwargs):
        '''
        Initializes the ntp_config class.
        Creates dictionaries of key:value configurations, which are taken
        from the config dictionary.
        Passed to this class from runner.py.
        '''

        super(ntp_config, self).__init__(config, componentID, loggerName = '', *args, **kwargs)

        self.Zone = ConstDict(config, 'Zone')
        self.Ntp = ConstDict(config, 'Ntp_')
        self.Runlevels = ConstDict(config, 'Runlevels')
        self.OnBoot = ConstDict(config, 'OnBoot')
        self.NtpdRestart = ConstDict(config, 'NtpdRestart')
        self.Template = ConstDict(config, 'Template_')
        self.Role = ConstDict(config, 'Role')
        self.Net = ConstDict(config, 'Net_')
        self.Interface = ConstDict(config, 'Interface')

    def __call__(self, editFiles):
        '''
        Main call function.
        '''
        self.NtpAdjuster(editFiles)

    def NtpAdjuster(self, editFiles):
        '''
        Runs functions related to the automatic configuration
        of ntpd.
        Gets: editFiles (list).
        Returns: N/A
        '''
        self.logger.error('[%s] Starting ntp configuration...' % Grn('i'))

        try:
            zone = self.Zone['Zone']
        except:
            zone = ''

        try:
            runlevels = self.Runlevels['Runlevels']
            onBoot = self.OnBoot['OnBoot'].lower()
            restart = self.NtpdRestart['NtpdRestart'].lower()
            role = self.Role['Role'].lower()
        except KeyError:
            runlevels, onBoot, restart, role = '', '', '', ''

        Files = self.ConstFilesDict(editFiles)
        if runlevels == '' and onBoot == '' and restart == '' and role == '':
            Appendix = {}
            Appendix['clk'] = 'ZONE="%s"\nUTC=false\nARC=false\n' % zone
        else:
            Templates = self.ConstTemplateDict(self.Template)
            Appendix = self.ConstAppendixDict(zone, Templates, role)
            Servers = self.ConstServersList(Appendix)

        if zone != '':
            self.ChangeEtcLocalTime(zone, Files)
            self.RewriteClock(Files, Appendix)

        if len(self.Ntp) != 0:
            system('systemctl stop chronyd')
            system('systemctl disable chronyd')
            self.AppendToNtpConf(Files, Appendix)
            self.SetOnBoot(runlevels, onBoot)
            NtpKeys = self.Ntp.keys()
            self.RestartService(restart, self.Ntp[NtpKeys[0]])

            self.logger.error(\
            '[%s] Ntp configured. Servers: %s, OnBoot: "%s", Runlevels: "%s", NtpdRestarted: "%s"' \
            % (Grn('i'), Servers, onBoot, runlevels, restart))
        elif zone != '':
            self.logger.error(\
            '[%s] Time zone configured. Zone: "%s"' \
            % (Grn('i'), zone))
        elif zone == '' and len(self.Ntp) == 0 and role == 'server':
            system('systemctl stop chronyd')
            system('systemctl disable chronyd')
            self.AppendToNtpConf(Files, Appendix)
            self.SetOnBoot(runlevels, onBoot)
            NtpKeys = self.Ntp.keys()
            if len(NtpKeys) != 0:
                self.RestartService(restart, self.Ntp[NtpKeys[0]])
            else:
                self.RestartService(restart)

        elif zone != '' and len(self.Ntp) != 0:
            raise Exception, '[%s] Mixed configuration of ntpd and time zone is not possible, please check the config file.' % Red('e')

        
    def FileReader(self, fileName):
        '''
        Read lines from a given file and return them.
        '''

        self.logger.debug('[%s] Accessing FileReader()' % Blu('i'))

        if exists(fileName):
            fh = open(fileName, 'r')
            Lines = fh.readlines()
            fh.close()
            return Lines

    def ConstFilesDict(self, EditFiles, Files = {}):
        '''
        Creates a dictionary of files and keys for calling those files.
        Gets: EditFiles (list)
        Returns: Files (dict)
        '''
        for editFile in EditFiles:
            if 'ntp.conf' in editFile:
                Files['ntp'] = editFile
            elif 'localtime' in editFile:
                Files['lt'] = editFile
            elif 'clock' in editFile:
                Files['clk'] = editFile
        Files['clk'] = '/etc/sysconfig/clock'
        self.logger.debug('[%s] Compiled Files dictionary: %s' % (Blu('i'), Files))
        return Files

    def ConstTemplateDict(self, Tmpl, Templates = {}):
        '''
        Creates a dictionary of template lines and keys for calling them.
        Gets: Tmpl (list)
        Returns: Templates (dict)
        '''
        rst_cli, rst_srv, srv = 0, 0, 0
        for tmpl in Tmpl:
            if 'restrict' in Tmpl[tmpl] and 'nomodify' in Tmpl[tmpl] and 'noquery' not in Tmpl[tmpl]:
                Templates['rst_srv'] = Tmpl[tmpl].strip('"') + '\n'
                rst_srv += 1
            elif 'restrict' in Tmpl[tmpl] and 'nomodify' in Tmpl[tmpl] and 'noquery' in Tmpl[tmpl]:
                Templates['rst_cli'] = Tmpl[tmpl].strip('"') + '\n'
                rst_cli += 1
            elif 'server' in Tmpl[tmpl]:
                Templates['srv'] = Tmpl[tmpl].strip('"') + '\n'
                srv += 1
            if rst_cli + rst_srv + srv == len(Tmpl):
                break
        return Templates

    def ConstAppendixDict(self, zone, Templates, role, Appendix = {}):
        '''
        Creates a dictionary of appendix lines and keys for calling those lines.
        Gets: zone (str)
        Returns: Appendix (dict)
        '''
        Appendix['clk'] = 'ZONE="%s"\nUTC=false\nARC=false\n' % zone
        if len(self.Interface) > 0:
            interface = self.Interface[self.Interface.keys()[0]]
        else:
            interface = 'bond0'
        subnet, netmask = self.GetNet(interface)
        if role == 'server':
            i = 0
            if len(self.Ntp.keys()) != 0:
                for key in self.Ntp.keys():
                    try:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % eval(self.Ntp[key])
                    except TypeError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % eval(self.Ntp[key])
                    except SyntaxError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % self.Ntp[key]
                    except NameError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % self.Ntp[key]
                    try:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % eval(self.Ntp[key])
                    except SyntaxError:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % self.Ntp[key]
                    except NameError:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % self.Ntp[key]
                    Appendix['rst_%s' % str(i + 2)] = Templates['rst_srv'] % (subnet, netmask)
                    i += 1
            else:
                if zone == '':
                    self.logger.error('[%s] No ntp servers given, synchronizing locally...' % Grn('i'))
                Appendix['rst_%s' % str(i + 1)] = Templates['rst_srv'] % (subnet, netmask)
            for key in self.Net.keys():
                i += 1
                subnet, netmask = self.Net[key].split()[0], self.Net[key].split()[1]
                if subnet.endswith('.0'):
                    Appendix['rst_%s' % str(i + 1)] = Templates['rst_srv'] % (subnet, netmask)
                else:
                    subnet, netmask = self.GetNet('', subnet, netmask)
                    Appendix['rst_%s' % str(i + 1)] = Templates['rst_srv'] % (subnet, netmask)
        if role == 'client':
            i = 0
            if len(self.Ntp.keys()) != 0:    
                for key in self.Ntp.keys():
                    try:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % eval(self.Ntp[key])
                    except TypeError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % (eval(self.Ntp[key]), netmask)
                    except SyntaxError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % self.Ntp[key]
                    except NameError:
                        Appendix['rst_%s' % str(i + 1)] = Templates['rst_cli'] % self.Ntp[key]
                    try:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % eval(self.Ntp[key])
                    except SyntaxError:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % self.Ntp[key]
                    except NameError:
                        Appendix['srv_%s' % str(i + 1)] = Templates['srv'] % self.Ntp[key]
                    i += 1
            else:
                raise Exception, '[%s] Cannot configure ntp client without ntp servers, exiting...' % Red('e')
        self.logger.debug('[%s] Compiled Appendix dictionary: %s' % (Blu('i'), Appendix))
        return Appendix

    def ConstServersList(self, Appendix):
        '''
        Creates a list of servers.
        Gets: Appendix (dict)
        Returns: Servers (list)
        '''
        Servers = []
        for value in Appendix.values():
            if 'server' in value:
                try:
                    Servers.append(search('(server )(.*)(\n)', value).group(2))
                except AttributeError:
                    pass
        return Servers

    def AppendToNtpConf(self, Files, Appendix):
        '''
        Modifies ntp.conf.
        Gets: Files (dict), Appendix (dict).
        Returns: N/A
        '''
        if exists(Files['ntp']):
            Lines = self.FileReader(Files['ntp'])
        
            fh = open(Files['ntp'], 'w')
            for line in Lines:
                if (line.startswith('server') or line.startswith('restrict')) \
                and '127.127.1.0' not in line and 'default' not in line \
                and '127.0.0.1' not in line and '-6 ::1' not in line \
                and line not in Appendix.values():
                    self.logger.debug('[%s] Found colliding line, commenting out: %s' % (Blu('i'), line))
                    fh.write('#%s' % line)
                elif match('(server[\t\s]+127.127.1.0)|(fudge[\t\s]+127.127.1.0)', line) and \
                        (len(self.Ntp.keys()) > 0 or self.Role == 'client'):
                    self.logger.error('[%s] Found local NTP line, commenting out: %s' % (Blu('i'), line))
                    fh.write('#%s' % line)
                else:
                    fh.write(line)
            fh.close()

            fh = open(Files['ntp'], 'a')
            for key in ConstDict(Appendix, 'srv'):
                if Appendix[key] not in Lines:
                    fh.write(Appendix[key])
                    self.logger.error('[%s] Writing to %s: %s' % (Grn('i'), Files['ntp'], Appendix[key]))
            for key in ConstDict(Appendix, 'rst'):
                if Appendix[key] not in Lines:
                    fh.write(Appendix[key])
                    self.logger.error('[%s] Writing to %s: %s' % (Grn('i'), Files['ntp'], Appendix[key]))
            fh.close()
        else:
            raise Exception, '[%s] File not found: %s' % (Red('e'), Files['lt'])

    def ChangeEtcLocalTime(self, zone, Files):
        '''
        Replaces the localtime.
        Gets: zone (str), Files (dict)
        Returns: N/A
        '''
        if exists(Files['lt']):
            remove(Files['lt'])
            self.logger.debug('[%s] Removing file: %s' % (Grn('i'), Files['lt']))
        else:
            raise Exception, '[%s] File not found: %s' % (Red('e'), Files['lt'])

        self.logger.debug('[%s] Copying new zone file: %s' % (Grn('i'), Files['lt']))
        system('cp -pr %s %s' % (join('/usr/share/zoneinfo', zone), Files['lt']))
        system('timedatectl set-timezone  %s' % zone)

    def RewriteClock(self, Files, Appendix):
        '''
        Modifies the clock file.
        Gets: Files (dict), Appendix (dict).
        Returns: N/A
        '''
        if 'clk' in Files.keys():
            self.logger.debug('[%s] Writing to %s: %s' % (Grn('i'), Files['clk'], Appendix['clk']))
            fh = open(Files['clk'], 'w')
            fh.write(Appendix['clk'])
            fh.close()
        else:
            raise Exception, '[%s] File not found: %s' % (Red('e'), Files['lt'])

    def SetOnBoot(self, runlevels, onBoot):
        '''
        Sets or unsets ntpd to start on boot for required runlevels.
        Gets: runlevels (str), onBoot (str).
        Returns: N/A
        '''
        if onBoot.startswith('ena'):
            self.logger.debug('[%s] Setting ntpd to start on runlevels %s' % (Blu('i'), runlevels))
            system('chkconfig --level %s ntpd on' % runlevels)
        elif onBoot.startswith('dis'):
            self.logger.debug('[%s] Setting ntpd not to start on runlevels %s' % (Blu('i'), runlevels))
            system('chkconfig --level %s ntpd off' % runlevels)

    def RestartService(self, restart, server = ''):
        '''
        Restarts the ntpd service if requested in ntp_adj.conf.
        Gets: restart (str)
        Returns: N/A
        '''
        if restart.startswith('y'):
            self.logger.debug('[%s] Restarting ntpd...' % Blu('i'))
            #output = go('/etc/init.d/ntpd stop')
            #self.logger.error('[%s] %s' % (Grn('i'), output))
            system('systemctl stop ntpd')
            
            if server != '':
                try:
                    server = eval(server)
                except NameError:
                    pass
                except SyntaxError:
                    pass
                except TypeError:
                    pass
                output = go('/usr/sbin/ntpdate %s' % server)
                self.logger.error('[%s] %s' % (Grn('i'), output))
            else:
                self.logger.debug('[%s] Skipping ntpdate for local syncs' % Blu('i'))
            #output = go('/etc/init.d/ntpd start')
            system('systemctl enable ntpd')
            system('systemctl start ntpd')
            system('timedatectl set-ntp yes')
            #self.logger.error('[%s] %s' % (Grn('i'), output))
        elif restart.startswith('n'):
            self.logger.debug('[%s] Skipping ntpd restart...' % Blu('i'))
     
    def GetNet(self, eth = 'bond0', ip = '', netmask = ''):
        '''
        Finds the subnet and netmask of an ethernet device or, if given, finds a subnet
            and netmask of an ip and netmask couple.
        Gets: eth (optional str), ip (optional str), netmask (optional netmask)
        Returns: subnet, netmask (str, str)
        '''
        try:
            if ip == '':
                output = go('ifconfig %s' % eth)
                ip = search('(inet .*)(netmask.*)(broadcast.*)', output).group(1).lstrip('inet').strip() 
                netmask = search('(inet .*)(netmask.*)(broadcast.*)', output).group(2).lstrip('netmask').strip()
                subnet = go('ipcalc -n %s %s' % (ip, netmask)).lstrip('NETWORK=')
            elif ip != '' and netmask != '':
                subnet = go('ipcalc -n %s %s' % (ip, netmask)).lstrip('NETWORK=')
        except AttributeError:
            raise Exception, '[%s] The interface "%s" is not configured...' % (Red('e'), eth)
        return subnet, netmask
