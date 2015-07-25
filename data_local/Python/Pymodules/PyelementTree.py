try:
    # Supporting ElementTree 1.3.x
    import xml.etree.ElementTree as ElementTree
except:
    # Supporting ElementTree 1.2.x
    import elementtree.ElementTree as ElementTree
import re, os

__all__ = ["ElementTree",]


class docinfo:
    pass

def update_docinfo(source, header='<?xml version="1.0" encoding="UTF-8"?>', def_version ="1.0", def_encoding='UTF-8'):
    _header = source.readline()
    _doctype = source.readline()
    _header = _header.strip()
    _doctype = _doctype.strip()

    doctype_lines = []
    xml_version = def_version
    encoding = def_encoding

    # take from header the version and encoding and update
    if re.match('<\?xml .*\?>', _header):
        version_reg = 'version=[\'|\"](?P<version>.*?)[\'|\"][\s|\?]'
        encoding_reg = 'encoding=[\'|\"](?P<encoding>.*?)[\'|\"][\s|\?]'
        if re.search(version_reg, _header):
            xml_version = re.search(version_reg, _header).group('version')
        if re.search(encoding_reg, _header):
            encoding = re.search(encoding_reg, _header).group('encoding')
        header = '%s' % _header
            
    # Add doc type: <!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"...
    if _doctype.startswith('<!DOCTYPE'):
        doctype_lines.append(_doctype)
        if not _doctype.endswith('>'):
            for line in source.readlines():
                if not line.strip().endswith('>'):
                    doctype_lines.append(line)
                else:
                    doctype_lines.append(line)
                    break

    # Add attribute to docinfo.
    _docinfo = docinfo()
    _docinfo.header = header
    _docinfo.xml_version = xml_version
    _docinfo.encoding = encoding
    _docinfo.doctype = doctype_lines
    if hasattr(source, 'name'):
        _docinfo.filename = source.name
    else:
        _docinfo.filename = 'cStringIO.StringO'
    
    return _docinfo       

def open_xfile(source, header = '<?xml version="1.0" encoding="UTF-8"?>',defualt_version ="1.0", defualt_encoding='UTF-8'):
    if not hasattr(source, "read"):
        source = open(source, "rb")

    docinfo = update_docinfo(source)
    source.seek(0)
    xfile = ElementTree.parse(source)
    xfile.docinfo = docinfo
    source.close()

    return xfile

ElementTree.open_xfile = open_xfile
  
def check_xpath(xpath):
    if not re.match('[^[\s\t]*\/?[\w|\.//?|\*]+', xpath):
        raise Exception, "illegal tag name: %s" % xpath
ElementTree.check_xpath = check_xpath
        
def check_identifier_block(id):
    regex = '(?P<block>\[)[\s\t]*(?P<key>[@|$][\w|\.//?\{?\*]+\S*?)((?P<type>[=|~])(?P<delimiter>[\'|\"])(?P<value>.*?)(?(delimiter)\\5))?(?(block)[\s\t]*\])'
    regex = re.compile(regex)
    reGex = regex.match(id)
    if not reGex:
        raise Exception, "illegal xpath identifier block format: %s" % id
    return reGex
ElementTree.check_identifier_block = check_identifier_block  
          
def get_xpath_identifier(id, xp):
    if re.match('(\[-?\d*:?-?\d*\])', id) and re.match('\[.*?\d+.*?\]', id):
        xp['element_filter'] = re.match('(\[-?\d*:?-?\d*\])', id).group(0)
        id = id[len(xp['element_filter']):].lstrip() 
        if id.startswith('['):
            return get_xpath_identifier(id, xp)
        return id, xp     
    _id = check_identifier_block(id)
    id_hash = xp['children_id']
    if _id.group("key").startswith("@"):
        id_hash = xp['xattr']
    if _id.group("type"):
        id_hash[_id.group("key")[1:]] = _id.group("value")
        if _id.group("type") == "~":
            id_hash[_id.group("key")[1:]] = re.compile(_id.group("value"))
    else:
        id_hash[_id.group("key")[1:]] = False
    if id[_id.end():].lstrip().startswith('['):
        return get_xpath_identifier(id[_id.end():].lstrip(), xp)         
    return id[_id.end():], xp
ElementTree.get_xpath_identifier = get_xpath_identifier

def _list_xpath(lxp, xp ,_xpath):
    lxp.append(xp)
    if _xpath:
        lxp.extend(list_xpath(_xpath))
    return lxp

def xpath_delimiter_priority(delimiter):
    delimiter['clean_string'] = -1
    first_delimiter = 'clean_string'
    for d, t in delimiter.iteritems():
        for _d, _t in delimiter.iteritems():
            if d == _d: continue
            elif t == _t == -1: continue
            elif t > -1 and _t > -1:
                if t < _t and (delimiter[first_delimiter] == -1 \
                   or delimiter[first_delimiter] > t):
                    first_delimiter = d
                elif delimiter[first_delimiter] == -1 \
                     or delimiter[first_delimiter] > _t: first_delimiter = _d
            elif t > -1 and t == -1 and (delimiter[first_delimiter] == -1 \
                 or delimiter[first_delimiter] > t): first_delimiter = d
            elif _t > -1 and t == -1 and (delimiter[first_delimiter] == -1 \
                 or delimiter[first_delimiter] > _t): first_delimiter = _d
    return first_delimiter
     
def list_xpath(xpath):
    lxp = []
    xp = {'children_id' : {},
          'xattr' : {}, 
          'deep' : False,
          'element_filter' : False, 
          'regex' : False, 
          'wildcard' : False}

    if xpath.startswith('//'):
        xp['deep'] = True          
    xpath = xpath.strip('/')
    block = xpath.find('[')
    regex_open = xpath.find('{')
    wildcard = xpath.find('*')
    slash = xpath.find('/')
    deep_slash = xpath.find('//')
    # Covers "//" spliter for each element - a//b/c
    if xpath_delimiter_priority({'wildcard' : wildcard, 
                                 'regex' : regex_open, 
                                 'block' : block, 
                                 'deep_slash' : deep_slash}) == 'deep_slash':
        xp['xpath'] = xpath[:slash]
        _xpath = xpath[slash:]
        return _list_xpath(lxp, xp ,_xpath)
    # Covers "//" spliter for each element - a//b/, //a/c/b or a/c//d
    elif xpath_delimiter_priority({'wildcard' : wildcard, 
                                 'regex' : regex_open, 
                                 'block' : block, 
                                 'slash' : slash}) == 'slash' and (xp['deep'] \
                                  or xpath_delimiter_priority({'wildcard' : wildcard, 
                                                'regex' : regex_open, 
                                                'block' : block, 
                                                'deep_slash' : xpath[:slash].find('//')}) == 'deep_slash'):
        xp['xpath'] = xpath[:slash]
        _xpath = xpath[slash:]
        return _list_xpath(lxp, xp ,_xpath)             
    # Covers Regex type a/{b}/c
    elif xpath_delimiter_priority({'wildcard' : wildcard, 
                                   'regex' : regex_open, 
                                   'block' : block}) == 'regex':
        regex_close = xpath.find('}', regex_open)
        if regex_close == -1 or (regex_open > 0 and xpath_delimiter_priority({'slash' : slash, 'regex' : regex_open}) != 'slash'):
            raise Exception, "illegal xpath tag regex format: %s" % xpath
        if regex_open > 0:
            xp['xpath'] = xpath[:xpath.rfind('/',0,regex_open)]
            _xpath = xpath[slash:]
            return _list_xpath(lxp, xp ,_xpath)
        block = xpath.find('[', regex_close)
        slash = xpath.find('/', regex_close)
        xp['regex'] = xpath[regex_open+1:regex_close]
        xp['xpath'] = '.'
        _xpath = xpath[regex_close+1:]       
        if xpath_delimiter_priority({'block' : block, 
                                     'slash' : slash}) == 'slash':
            block = xpath.find('[',0,slash)
            return _list_xpath(lxp, xp ,_xpath)
        xpath = '.' + xpath[regex_close+1:]  
    # Covers Wildcard a/b*/c
    elif xpath_delimiter_priority({'wildcard' : wildcard, 
                                   'regex' : regex_open, 
                                   'block' : block}) == 'wildcard':
        post_slash = xpath.find('/', wildcard)
        pre_slash = xpath.rfind('/', 0, wildcard)
        if pre_slash > -1:
            xp['xpath'] = xpath[:pre_slash]
            _xpath = xpath[pre_slash:]
            return _list_xpath(lxp, xp ,_xpath)
        block = xpath.find('[', wildcard)
        slash = xpath.find('/', wildcard)
        xp['xpath'] = '.'
        if xpath_delimiter_priority({'block' : block, 
                                     'slash' : slash}) == 'slash':
            block = xpath.find('[',0,slash)
            _xpath = xpath[slash:]
            xp['wildcard'] = xpath[:slash].replace('*', '.*')
            return _list_xpath(lxp, xp ,_xpath)                     
        elif xpath_delimiter_priority({'block' : block, 
                                       'slash' : slash}) == 'block':
            xp['wildcard'] = xpath[:block].replace('*', '.*')
            xpath = '.' + xpath[block:]
        else:
            xp['wildcard'] = xpath.replace('*', '.*')
            xpath = '.'
    # Support any type that has identifier a[0], a[$name="moco"], {a}[$name="moco"] ...
    if block > -1:
        xp['xpath'] = xpath[:xpath.find('[')].strip('/')
        _xpath = xpath[xpath.find('['):].strip()
        _xpath, xp = get_xpath_identifier(_xpath, xp)
        return _list_xpath(lxp, xp ,_xpath)
    # plain text with our regex. wildcard, identifier and recursive a/b
    else:
        check_xpath(xpath)
        xp['xpath'] = xpath
        lxp.append(xp)
    return lxp         
ElementTree.list_xpath = list_xpath 
        
def dig_xpath(e, xpath):
    found = []
    template_xpath = {'global_or' : False, 
                      'children_id_or' : False, 
                      'attrib_or' : False}
    if xpath['xpath'] == '':
        xpath['xpath'] = '.'
    if xpath['wildcard'] or xpath['regex']:
        elements = []
        if xpath['deep']:
            getchildren = [ i for i in e.iter()]
        else:
            getchildren = e.getchildren()
        for _e in getchildren:
            if (xpath['wildcard'] \
               and re.match(xpath['wildcard'], _e.tag.strip())) or \
               (xpath['regex'] and re.search(xpath['regex'], _e.tag.strip())):
                elements.append(_e)
    else:
        if xpath['deep']:
            if xpath['xpath'] == '..':
                elements = [ i.parent for i in e.iter() ]    
            else:
                elements = [ i for i in e.iter() if i.tag.strip() == xpath['xpath']]
        else:
            elements = e.findall_extend(xpath['xpath'])
    for _e in elements:
        attrib = 0
        children_id = 0
        for child, val in xpath.get('children_id', {}).iteritems():
            for __e in _e.xpath_query(child):
                if val == False:
                    children_id += 1
                elif getattr(val, 'search', False) and val.search(__e.text.strip()):
                    children_id += 1    
                elif val == __e.text.strip():
                    children_id += 1
        for attr,val in xpath.get('xattr', {}).iteritems():
            if _e.attrib.has_key(attr):
                if val == False:
                    attrib += 1
                elif getattr(val, 'search', False) and val.search(_e.attrib[attr].strip()):
                    attrib += 1
                elif _e.attrib[attr].strip() == val:
                    attrib += 1
        if not xpath.get('children_id', None) and not xpath.get('xattr', None):
            if _e not in found: 
                found.append(_e)
                continue 
        if len(xpath.get('children_id', {}).keys()) <= children_id and \
           len(xpath.get('xattr', {}).keys()) == attrib and _e not in found:
            found.append(_e)
    return found
ElementTree.dig_xpath = dig_xpath 

def rooted_elementtree(elements):
    _elements = []
    _elements.extend(elements)
    for e in elements:
        for _e in e.iter():
            if _e in _elements:
                _elements.remove(_e)
    return _elements
ElementTree.root_elementtree = rooted_elementtree

def reformat_xml_tree(elem, level=0):
    '''
    Reformating the XML for human consumption.
    Gets: (elem) root element as xml node,
          (level) starting identation level.
    Returns: N/A
    ** Please note this function can be call on root element only once!!!
    '''
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            reformat_xml_tree(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
ElementTree.reformat_xml_tree = reformat_xml_tree

def element_filter(elements, element_filter):
    try:
        e = elements[0]
        exec('elements = elements%s' % element_filter)
        if type(elements) == type(e):
            elements = [elements]
    except:
        pass
    return elements
ElementTree.element_filter = element_filter
        
class _ElementInterfaceExtend(ElementTree._ElementInterface):

    def get_full_xpath(self, path=''):
        path = os.path.join(self.tag.strip(), path)
        if self.parent is not None:
            path = self.parent.get_full_xpath(path)
        return '/%s' % path.strip('/')
        
    def _iter_extend(self):
        # Due to deprication getiterator
        if not hasattr(self, "iter"):
            self.iter = self.getiterator
            
    def xpath_query(self, xpath, remove_self=False, force_deep=False):
        self._iter_extend()
        if xpath.startswith('//') or force_deep:
            xpath = '//' + xpath.strip('/') 
        elif remove_self:
            if xpath.strip('/') == self.tag:
                xpath = '.'
            else:
                xpath = xpath.strip('/').lstrip('%s/' % self.tag)
        elements = [self]
        for e in list_xpath(xpath):
            _elements = []
            for _e in elements:
                for __e in dig_xpath(_e,e):
                    if __e not in _elements:
                        _elements.append(__e)
            if e['element_filter'] and _elements:
                _elements = element_filter(_elements,e['element_filter'])   
            elements = _elements   
            if not elements:
                break
        return elements

    def findall_extend(self, xpath):
        if xpath.find('..') > -1:
            xpath = [ xp.strip('/') for xp in xpath.strip('/').split('/') if xp]
            elements = [self]
            for _xpath in xpath:
                _elements = []
                if _xpath == '..':
                    for p in [p.parent for p in elements]:
                        if p not in _elements:
                            _elements.append(p)
                else:
                    for e in elements: 
                        for _e in [__e for __e in e.findall(_xpath)]:
                            if _e not in _elements:
                                _elements.append(_e)
                elements = _elements
        else:
            elements = self.findall(xpath)
        return elements
ElementTree._ElementInterface = ElementTree.Element = _ElementInterfaceExtend

class ElementTreeExtend(ElementTree.ElementTree):

    def write2file(self, source=None, pretty_print=True, close_file=True):
        
        if not source:
            source = open(self.docinfo.filename, "w")
        elif not hasattr(source, "write"):
            source = open(source, "w")
  
        source.write(u'%s\n' % self.docinfo.header)
        for line in self.docinfo.doctype:
            source.write(u'%s\n' % line)

        if pretty_print:
            if not getattr(self._root, 'reformat_xml_tree', False):
                reformat_xml_tree(self._root)
                self._root.reformat_xml_tree = True
        self.write(source, encoding=self.docinfo.encoding.lower())
        if close_file:
            source.close()
        else:
            source.seek(0)
        return self.docinfo.filename
            
    def getroot_extend(self, build_parent_map = True):
        root = self.getroot()
        root._iter_extend()
        root.parent = None
        if build_parent_map:
            self.build_parent_map(root)
            # parent_map is not in use for now...
            #root.parent_map = dict((c, p) for p in root.iter() for c in p)
            #root.parent_map[root] = None
        root.reformat_xml_tree = False
        return root
        
    def build_parent_map(self, e):
        for _e in e.getchildren():
            _e.parent = e
            self.build_parent_map(_e)
ElementTree.ElementTree = ElementTreeExtend



class ElementTreeUtils:
       
    def xml_update(self, iRules, logger=True, force_save=True):
        for file_rules in iRules:
            logger and self.logger.error(u"")
            logger and self.logger.error(u"Starting to parse %s file...." % file_rules['file'])
            logger and self.logger.error(u"")
            for action in file_rules['exec_order']:
                if file_rules['actions'].get(action, []):
                    logger and self.logger.error(u"-------------- %s ---------------" % action.upper())
                    file_rules['output'] += u"-------------- %s ---------------\n" % action.upper()
                for rule in file_rules['actions'].get(action, []):
                    rule = self.get_rule_elements(rule)
                    logger and self.logger.info(u"rule:\n%s" % rule)
                    self.exec_order[action](rule)
                    if rule['output']:
                        logger and self.log_output(rule['output'])
                        file_rules['output'] += rule['output']
                    else:
                        self.logger.error(u"No %s were performed" % action.upper())
                        file_rules['output'] += u"No %s were performed\n" % action.upper()
                if file_rules['actions'].get(action, []):
                    logger and self.logger.error(u"-------------------------------------")
                    file_rules['output'] += u"-------------------------------------\n"
            if file_rules['output'] and force_save:
                file_rules['xfile'].write2file()
            elif file_rules['output']:
                logger and self.logger.error('File was modified but not saved.')
            else:
                logger and self.logger.error('File was NOT updated')
                file_rules['output'] += u"File was NOT updated.\n"
            #print file_rules['output']

        
    def get_default_rule_data(self, rule, _iRule):
        _rule = {'ref_file_name' : '',
                 'ref_elements' : [],
                 'ref_elements_function' : False,
                 'remove_tag_name' : False,
                 'ref_remove_tag_name' : False,
                 'elements_function' : False,
                 'import' : [],
                 'elements' : [],
                 'required' : True,
                 'output' : u'',
                 'force_append' : False,
                 'force_clone' : False,
                }
        if not rule.has_key('required') and rule['action'] == 'delete':
            rule['required'] = False
        _rule.update(rule)
        _rule['root'] = _iRule['root']
        if _iRule.get('file',False):
            _rule['file'] = _iRule['file']
        if _iRule.get('xfile',False):
            _rule['xfile'] = _iRule['xfile']
        if _iRule.get('ref_file_name',False):
            _rule['ref_xfile'] = _iRule['ref_file_name']['ref_xfile']
            _rule['ref_root'] = _iRule['ref_file_name']['ref_root']
        return [_rule]
    
    def get_rule_elements(self, rule):
        ref_elements = False
        for i in rule['import']:
            exec(i)
        if rule['elements']:
            pass # aleady contain elements...
        elif rule['elements_function']:
            exec('rule["elements"] = %s' % rule['elements_function'])
        else:
            rule['elements'] = rule['root'].xpath_query(rule['xpath'], rule['remove_tag_name'])
        if rule.get('ref_file_name', False):
            ref_elements = True
            if not rule.has_key('ref_xfile'):
                rule['ref_xfile']=ElementTree.open_xfile(rule['ref_file_name'])
                rule['ref_root']=rule['ref_xfile'].getroot_extend()
        if rule['ref_elements']:
            ref_elements = True
            # Nothing to do here
        elif rule.get('ref_elements_function', False):
            ref_elements = True
            exec('rule["ref_elements"] = %s' % rule['ref_elements_function'])
        elif rule.has_key('ref_xpath'):
            rule['ref_elements'] = rule['ref_root'].xpath_query(rule['ref_xpath'], rule['ref_remove_tag_name'])
        if rule['required'] and not rule['elements']:
            raise Exception, u"No elements were found for:\n%s " % rule
        if rule['required'] and ref_elements and not rule['ref_elements']:
            raise Exception, u"No ref_elements were found for:\n%s" % rule
        if ref_elements and len(rule['ref_elements']) != 1:
            raise Exception, u"ref_elements must contain single element in action %s, rule:\n%s" % \
                (rule['action'],rule)
        elif ref_elements and not rule['ref_xpath']:
            raise Exception, u"ref_xpath is required when ref_elements exists !! \n%s" % rule
        elif ref_elements and rule['action'] == 'clone' and not rule.get('pre_clone_id_xpath', False) \
                and not rule.get('post_clone_id_xpath', False):
            raise Exception, u"both pre/post clone_id_xpath must exists !! \n%s" % rule
        elif ref_elements and len(rule['elements']) > 1:
            raise Exception, u"%s operation are limited to single element only !! \n%s" % (rule['action'], rule)
        return rule
    
    def log_output(self, output):
        for o in [i for i in output.split('\n') if i]:
            self.logger.error(o)
        return

    def _modify_element(self, element, value):
        output = u''
        if value.has_key('tag'):
            old_element_tag = element.get_full_xpath()
            element.tag = value['tag']
            output += "element %s has been rename to %s\n" % (old_element_tag, element.get_full_xpath())
        if value.has_key('text'):
            element.text = value['text']
            output += "%s element's text has been changed to \"%s\"\n" % (element.get_full_xpath(), value['text'])
        if value.has_key('modify_attr') and not value.has_key('force_attr'):
            element.attrib.update(value['modify_attr'])
            for k,v in value['modify_attr'].iteritems():
                output += "%s = \"%s\" attribute of element %s has been set \n" % (k, v, element.get_full_xpath())
        if value.has_key('delete_attr') and not value.has_key('force_attr'):
            for del_attr in value['delete_attr']:
                if element.attrib.has_key(del_attr):
                    v = element.attrib.pop(del_attr)
                    output += "%s = \"%s\" attribute has been removed from %s tag\n" % (del_attr, v, element.get_full_xpath())
        if value.has_key('force_attr'):
            element.attrib = value['force_attr']
            for k,v in value['force_attr'].iteritems():
                output += "%s = \"%s\" attribute has been forced into %s element" % (k, v, element.get_full_xpath())
        return output

    def modify_elements(self, rule):
        for element in rule['elements']:
            rule['output'] += self._modify_element(element, rule['values'])
            

    def _append_element(self, element, ref_element):
        ref_element.parent = element
        element.append(ref_element)
        return u"<%s> element has been appened as a child to %s element\n" % (ref_element.tag, element.get_full_xpath())

    def append_element(self, rule):
        chk_element = [ e for e in rule['root'].xpath_query(rule['ref_xpath'], rule['remove_tag_name']) \
                       if e.parent == rule['elements'][0] ]
        if len(chk_element) > 1:
            raise Exception, u"ref_xpath (%s) query on root element has returned more then 1 element" % \
                rule['ref_xpath']
        elif len(chk_element) == 1 and rule['force_append']:
            rule['output'] += self._delete_element(chk_element[0])
        elif len(chk_element) == 1 and not rule['force_append']:
            rule['output'] += u"%s element exists in xpath %s query, skip appending..." % \
                (chk_element[0].get_full_xpath(), rule['ref_xpath'])
            return
        rule['output'] += self._append_element(rule['elements'][0],rule['ref_elements'][0])

    def _delete_element(self, element):
        parent = element.parent
        parent.remove(element)
        return u"<%s> element has been removed from %s element\n" % (element.tag, parent.get_full_xpath())
    
    def delete_elements(self, rule):
        if not rule['elements']:
            rule['output'] += 'xpath: %s - Nothing to delete' % rule['xpath']
            return
        for element in rule['elements']:
            rule['output'] += self._delete_element(element)

    def clone_element(self, rule):
        parent = rule['elements'][0]
        clone_element = rule['ref_elements'][0]
        chk_element = parent.xpath_query('%s/%s' % (clone_element.tag, rule['post_clone_id_xpath']))
        
        if len(chk_element) > 1:
            raise Exception, u"post_clone_id_xpath (%s) query on %s element has returned more then 1 element" % \
                (rule['post_clone_id_xpath'], parent.get_full_xpath())
        elif len(chk_element) == 1 and rule['force_clone']:
             rule['output'] += self._delete_element(chk_element[0])
        elif len(chk_element) == 1 and not rule['force_clone']:
            rule['output'] += u"clone element %s exists under %s parent element..skip cloning !!" % \
                (chk_element[0], parent.get_full_xpath())
            return
        
        clone_id = rule['ref_elements'][0].xpath_query(rule['pre_clone_id_xpath'])
        if not clone_id:
            raise Exception, u"could not found identifier %s element under %s" % \
                (rule['pre_clone_id_xpath'], rule['ref_elements'][0])
        elif len(clone_id) > 1:
            raise Exception, u"pre_clone_id_xpath (%s) query on %s element has returned more then 1 element" % \
                (rule['pre_clone_id_xpath'], rule['ref_elements'][0].get_full_xpath())

        rule['output'] += self._modify_element(clone_id[0], rule['values'])
        rule['output'] += self._append_element(rule['elements'][0], rule['ref_elements'][0])
ElementTree.ElementTreeUtils = ElementTreeUtils

