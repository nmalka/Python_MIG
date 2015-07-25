from Pyfiledit import builder
from PyelementTree import ElementTree
import os

class xml_config2(builder, ElementTree.ElementTreeUtils):

    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        self.tname = ''
        super(xml_config2, self).__init__(config, componentID, loggerName='', *args, **kwargs)
        if type(self.config.get('Files', '')) == str or type(self.config.get('Files', '')) == unicode:
            editFiles = [ f.strip() for f in self.config.get('Files', '').split(',') if f.strip()]
        else:
            editFiles = [ f.strip() for f in self.config.get('Files', '') if f.strip()]
        self._ = self.config['_']
        self.__ = self.config['__']
        self.sysConfig = self.config['sysConfig']
        self.Section = self.config['Section']
        self.exec_order = {'modify' : self.modify_elements, 
                           'delete' : self.delete_elements, 
                           'append': self.append_element, 
                           'clone' : self.clone_element
                          }

        self.logger.debug("The Original iRules Data Structure:")
        self.logger.debug("*"*20)
        self.logger.debug(self.config['iRules'])
        self.logger.debug("*"*20)
        self.logger.debug('')
        
        self.iRules = self.build_iRules(self.config.get('Xml2Files', editFiles))
        self.logger.debug(u"The Modified iRules Data Structure:")
        for i in self.iRules:
            self.logger.debug(u"<>"*20)
            for k,v in i.iteritems():
                self.logger.debug(u'%s : %s' % (k, v))
            self.logger.debug('')
            
    def __call__(self, editFiles=[], *args, **kwargs):
        if not self.iRules:
            self.logger.error(u"iRules list is empty, Nothing to do here...")
            return
        self.xml_update(self.iRules)
        
    def build_iRules(self, Files):
        iRules = []
        for f in Files:
            for iRule in self.config.get('iRules', []):
                if iRule['file'] == f or iRule['file'] == os.path.basename(f):
                    if f in [r['file'] for r in iRules]:
                        self.logger.debug(u"%s File is allready in iRules -------------> OLD" % f)
                        for _iRule in iRules:
                            if f == _iRule.get('file', False):
                                for rule in iRule.get('rules', []):
                                    _iRule['actions'][rule['action']] = _iRule['actions'].get(rule['action'], []) \
                                            + self.get_default_rule_data(rule, _iRule)
                    else:
                        self.logger.debug(u"%s File Doesn't Exists in iRules --------------> NEW" % f)
                        _iRule = {}
                        _iRule['file'] = f
                        _iRule['output'] = u''
                        _iRule['actions'] = {}
                        _iRule['exec_order'] = self.config.get('ExecOrder',['delete', 'append', 'clone', 'modify'])
                        _iRule['xfile'] = ElementTree.open_xfile(_iRule['file'])
                        _iRule['root'] = _iRule['xfile'].getroot_extend()
                        for rule in iRule.get('rules', []):
                            _iRule['actions'][rule['action']] = _iRule['actions'].get(rule['action'], []) \
                                    + self.get_default_rule_data(rule, _iRule)
                        if [ True for i in _iRule.get('actions', {}).values() if i]:
                            iRules.append(_iRule)
        return iRules       


