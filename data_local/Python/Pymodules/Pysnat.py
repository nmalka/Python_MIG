from Pyfiledit import builder
import os, time, re ,sys
from glob import glob


class snat(builder):
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(snat, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)

    def __call__(self, editFiles):
        self.init_snat_config()

    def init_snat_config(self):
        self.snat_rules = self.config['SnatRules']
        self.snat_cleanup()
        if self.snat_rules:
            self.config_rt_tables()
            self.config_bond()
            self.config_route()
            self.config_rule()
            self.delete_gw()
        else:
            print "\nNo SNAT rules were configured, clean all old snat rules."
        

    def config_rt_tables(self):
        self.logger.error("Configure %s" % self.config['rt_file_name'])
        rt_table = ''
        for set_bond in self.snat_rules:
            for bond, rules in set_bond.iteritems():
                rt_table += '%s\t%s\n' % (rules['priority'], rules['table_name'])

        try:
            rt_file = open(self.config['rt_file_name'], 'r+')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['rt_file_name']

        lines = rt_file.readlines()
        rt_file.seek(0)
        lines2write = ''
        for line in lines:
            if line.strip().endswith('unspec'):
                lines2write += rt_table
                lines2write += line
            else:
                lines2write += line

        try:
            rt_file.write(lines2write)
            self.logger.error("Write route entry to %s file" % (self.config['rt_file_name']))
            self.logger.debug("write lines %s to file %s" % (lines2write, self.config['rt_file_name']))
        except:
            rt_file.close()
            raise Exception, 'Could\'nt write data to %s file.' % self.config['rt_file_name']
        rt_file.close()
         
    def config_route(self):

        self.logger.error("Configure %s" % self.config['route_file_name'])
        route_template = 'default via %s\n' % self.config['DG']
        self.logger.debug("The DG ip is %s and add it to %s" % (self.config['DG'], self.config['route_file_name']))
        for bond_hash in self.snat_rules:
            for bond_name, bond_hash_properties in bond_hash.iteritems():
                route_template += 'default via %s table %s\n' % (bond_hash_properties['next_hop'],bond_hash_properties['table_name'])
        try:
            new_file = open(self.config['route_file_name'],'w')
        except:
            raise Exception, 'Could\'nt create %s file.' % self.config['route_file_name']
        try:
            new_file.write(route_template)
        except:     
            new_file.close()
            raise Exception, 'Could\'nt write data to %s file.' % self.config['route_file_name']
        new_file.close()
                        
    def config_rule(self):
        self.logger.error("Configure %s" % self.config['rule_file_name'])
        rule_template = ''
        counter = 30000
        for bond_hash in self.snat_rules:
            for bond_name, bond_hash_properties in bond_hash.iteritems():
                rule_template += 'from %s table %s priority %d\n' % (bond_hash_properties['ip'],bond_hash_properties['table_name'],counter)
                counter -= 1
        try:
            new_file = open(self.config['rule_file_name'],'w')
        except:
            raise Exception, 'Could\'nt create %s file.' % self.config['rule_file_name']
        try:
            new_file.write(rule_template)
            self.logger.debug("write lines %s to file %s" % (rule_template, self.config['rule_file_name']))
        except:     
            new_file.close()
            raise Exception, 'Could\'nt write data to %s file.' % self.config['rule_file_name']
        new_file.close()
        
    def config_bond(self):
        self.logger.error("Configure the virtual bond interface") 
        for bond_hash in self.snat_rules:
            for bond_name, bond_hash_properties in bond_hash.iteritems(): 
                orig_bond_name = bond_hash_properties['bond_file'].split(':')[0]
                try:
                    orig_bond_file = open(orig_bond_name ,'r')
                except:
                    raise Exception, 'Could\'nt open %s file.' % orig_bond_name

                lines = orig_bond_file.readlines()
                orig_bond_file.close()

                try:
                    new_file = open(bond_hash_properties['bond_file'] ,'w')
                except:
                    raise Exception, 'Could\'nt create %s file.' % bond_hash_properties['bond_file']

                lines2write = ''
                for line in lines:
                    if line.strip().startswith("DEVICE"):
                        lines2write += 'DEVICE=%s\n' % bond_name
                    elif line.strip().startswith("IPADDR"):
                        lines2write += 'IPADDR=%s\n' % bond_hash_properties['ip']
                    elif line.strip().startswith("BONDING_OPTS"):
                        continue
                    else:
                        lines2write += line
                        
               
                try:
                    new_file.write(lines2write)
                    self.logger.debug("Configure the %s file with the following:\n%s " % (bond_hash_properties['bond_file'], lines2write))
                except:     
                    new_file.close()
                    raise Exception, 'Could\'nt write data to %s file.' % bond_hash_properties['bond_file']
                new_file.close()
                 
    def delete_gw(self):
        self.logger.error("delete GATEWAY from %s" % self.config['network_file'])
        try:
            gw_file = open(self.config['network_file'], 'r')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['network_file']
        lines = gw_file.readlines()
        lines2write = [line for line in lines if not line.strip().startswith('GATEWAY')]
        gw_file.close()
        
        try:
            gw_file = open(self.config['network_file'], 'w')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['network_file']
        try:
            gw_file.writelines(lines2write)
            self.logger.error("The DG ip is %s and remove it from %s" % (self.config['DG'], self.config['network_file']))
        except:
            raise Exception, 'Could\'nt write data to %s file.' % self.config['network_file']
        gw_file.close()
             
    def snat_cleanup(self):
        
        # This section delete the files I created in the installation
        self.logger.error("Running cleanup before installation")
        bond_file = [f for f in glob(os.path.join(self.config['bond_file_basedir'] + 'ifcfg-bond*')) \
                       if os.path.isfile(f) and ':' in os.path.basename(f)]
        
        route_file = [f for f in glob(os.path.join(self.config['bond_file_basedir'] + 'route-bond*')) \
                       if os.path.isfile(f)]
        
        rule_file = [f for f in glob(os.path.join(self.config['bond_file_basedir'] + 'rule-bond*')) \
                       if os.path.isfile(f)]
        delete_files =  route_file + rule_file +bond_file
                                   
        for file in delete_files:
            try:
                os.remove(file)
                self.logger.debug("Remove files: %s" % delete_files)
            except:
                pass

        # This section revert all the files entry to the original
        # network file revert
        gw2write = 'GATEWAY=%s\n' % self.config['DG']
        try:
            gw_file = open(self.config['network_file'], 'r+')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['network_file']
        
        lines = gw_file.readlines()
        gw_file.seek(0)
        lines2add = ''
        gw = False 
        for line in lines:
            if line.strip().startswith('GATEWAY'):
                gw = True
            else:
                lines2add += line
        if not gw:
            lines2add += gw2write
        try:
            gw_file.write(lines2add)
            self.logger.debug("Add back the GATEWAY ip %s to file: %s" % (self.config['DG'], self.config['network_file']))
        except:
            gw_file.close()
            raise Exception, 'Could\'nt write data to %s file.' % self.config['network_file']
        gw_file.close()

        # rt_tables file revert
        try:
            rt_file = open(self.config['rt_file_name'], 'r')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['rt_file_name']



        rt_lines = rt_file.readlines()
        lines2delete = ''
        for line in rt_lines:
            if line.find(self.config['snat_table_prefix']) > -1:
                continue;
            lines2delete += line
        rt_file.close()
        
        try:
            rt_file = open(self.config['rt_file_name'], 'w')
        except:
            raise Exception, 'Could\'nt open %s file.' % self.config['rt_file_name']
        try:
            rt_file.writelines(lines2delete)
            self.logger.debug("Remove snat tables from file: %s" % self.config['rt_file_name'])
        except:
            raise Exception, 'Could\'nt write data to %s file.' % self.config['rt_file_name']
        rt_file.close()
