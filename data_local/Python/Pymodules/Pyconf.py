
####################################
#   By: Yaron Cohen                #
#   Mail: yaron.cohen@comverse.com #
#   Ver: 4.8                       #
#   Date: 24/06/09                 #
#   ModuleNmae: Pyconf.py          #
####################################

from Pyfiledit import builder
from Pyfunc import *
from Pydecorators import *
import os, time, re ,sys
import traceback

class HashParser(object):

    def BuildDict(self, startwith, hash, hashFiles1={}, reg=r'[\s\t]*=[\s\t]*'):
        """
        funtion descriptions -> get dict and return dict of specific kind(depending on startwith variable)
        inputs:
        hash -> @type:dict @para:dict that incloude everything(from conf file) .
        startwith -> @type:string @para:what we want to seclude(kind of...)
        reg -> @type:string @para:regular expression
        outputs:
        hashFiles1  -> @type:dict @para:return dict from dict
        """
        for k,v in hash.iteritems():
            if re.split(reg, k, 1)[0].startswith(startwith):
                hashFiles1[re.split(reg, k, 1)[0]]=v
        return hashFiles1    

    def methodDictBuild(self, files, method='KeyVal'):
        """
        funtion descriptions -> get list of file and method ,return dict of files name(key) method(value)
        inputs:
        files -> @type:array @para:array of files that will manipulate .
        method -> @type:string @para:file type
        outputs:
        hash -> @type:dict @para:return dict with key:file, value:method
        """
        hash = {}
        for file in files:
            if os.path.basename(file) == 'resolv.conf':
                hash[file] = 'Resolv'
            else:
                hash[file] = method
        return hash

    def GetValueFromFunctionToDict(self, hash, startwith='Function_'):
        """
            funtion descriptions -> return dict of function value 
            inputs:
            hash -> @type:dict @para:dict from conf file
            startwith -> @type:string @para:from hash get key starts with Function_
            outputs:
            hash -> @type:dict @para:return dict with key:Functions index, value:output of the functions
        """
        self.logger.debug('Getting values for all functions under %s file'%file)
        self.logger.debug('hash=%s' % hash)
        for k,v in hash.iteritems():
            if k.startswith(startwith):
                self.logger.debug('eval=%s' % v)
                try:
                    re.search('^[a-zA-Z0-9_]+\(.*\)$', v).group()
                    try:
                        hash[k] = eval(v)
                    except:
                        self.logger.error(traceback.format_exc())
                        raise Exception, 'Failed to execute %s' % v
                except AttributeError:
                    self.logger.debug('[W] %s' % sys.exc_info()[1])
        return hash

class conf_app(builder, HashParser):


    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        """
        funtion descriptions -> initialization of variables
        inputs:
        config -> @type:dict @para:dict from conf file
        componentID -> @type:variable @para:get the type of server from conf file 
        loggerName->@type:variable @para:get the logger file
        *args->@type:list @para:futures use
        **kwargs->@type:dict @para:futures use
        """
        super(conf_app, self).__init__(config=config, componentID=componentID, \
                loggerName=loggerName, *args, **kwargs)
        self.snmp = self.BuildDict(startwith='Snmp_',hash=self.config,hashFiles1={})
        self.snmp = self.GetValueFromFunctionToDict(hash=self.snmp,startwith='Snmp_')
        self.functions_and_text = self.BuildDict(startwith='Function_',hash=self.config,hashFiles1={})
        self.functions_and_text = self.BuildDict(startwith='Snmp_',hash=self.config,\
                                                 hashFiles1=self.functions_and_text)
        self.functions_and_text = self.BuildDict(startwith='Text_',hash=self.config,\
                                                hashFiles1=self.functions_and_text)
        self.functions_and_text = self.BuildDict(startwith='Snmp_',hash=self.config,\
                                  hashFiles1=self.functions_and_text)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text,\
                                  startwith='Snmp_')
        self.string_on_file = {}

    def AppendLines(self,lines,tmp,reg1=r'^[\s\t]*%s$'):
        """
        funtion descriptions -> append non exsit lines to specific file.
        inputs:
        lines -> @type:array @para:lines that no exsit in the file
        tmp -> @type:dict @para:dict from conf file that incloude lines that need to be modify or append.
        reg1->@type:variable @para:regular expression
        """
        flag = 1
        if re.match(reg1 %str(self.config['Append']).upper(), 'YES'):
             for v in tmp:
                 for val in v.values():
                     if val and self.functions_and_text[v.values()[0]] !='no append':
                         if flag == 1:
                             lines.append('\n# Runner add the following lines\n')
                             lines.append('%s' % '#' + '-'*32 + '\n')
                             flag = 0
                         self.logger.error('%s=%s will be append' %(v.keys()[0],\
                                 self.functions_and_text[v.values()[0]]))
                         lines.append('%s=%s\n' % (v.keys()[0], self.functions_and_text[v.values()[0]]))
        elif not re.match(reg1 %str(self.config['Append']).upper(), 'NO'):
            raise Exception, 'Value of Append is => %s'\
                    %str(self.config['Append']).upper()

    def KeyOfLine(self,linesRef,line_key = [], reg=r'[\s\t]*=[\s\t]*'):
        """
        funtion descriptions -> get array of lines and return array of, lines until "=".
        inputs:
        linesRef -> @type:array @para:array of lines from file(get it from builder class)
        outputs:
        line_key -> @type:array @para: array of,lines until '='
        """
        for line in linesRef:
            if not line.startswith('#') or not line.startswith(';'): line_key.append(re.split(reg, line, 1)[0])
        return line_key

    def DictOfSnmp(self,tmp,snmp_hash={}):
        """
        funtion descriptions -> get dict from conf file and  return dict of snmp type.
        inputs:
        tmp -> @type:dict @para:dict from conf file that incloude lines that need to be modify or append.
        outputs:
        snmp_hash -> @type:dict @para: dict of snmp type. 
        """
        for key in tmp:
            if not key.keys()[0] in self.line_key and key.values()[0].startswith('Snmp_'):
                snmp_hash[key.keys()[0]]=key.values()[0]
        self.logger.info('snmp_hash=>%s' % snmp_hash)
        return snmp_hash

    def ArrayOfSnmp(self,tmp,snmp_array=[]):
        """
        funtion descriptions -> get dict from conf file and  return array of snmp type.
        inputs:
        tmp -> @type:dict @para:dict from conf file that incloude lines that need to be modify.
        outputs:
        snmp_array -> @type:dict @para: array of snmp type. 
        """
        for key in tmp:
            if key.values()[0].startswith('Snmp_'):
                snmp_array.append(key.keys()[0])
        self.logger.info('snmp_array=>%s' % snmp_array)
        return snmp_array

    def __call__(self, editFiles): 
        """
        funtion descriptions -> create a dict with $file type (from conf file) and call to builder class.
        inputs:
        reg -> @type:string @para:regular expression
        editFiles -> @type:array @para: array of files (from conf file)
        """
        editFiles = self.config.get('KEYVAL_Files', editFiles)
        reg=r'[\s\t]*=[\s\t]*'
        methodDict = self.methodDictBuild(files=editFiles)
        self.logger.debug('dict_of_functions_and_text=%s' % self.functions_and_text)
        self.logger.info('methodDict = %s'%methodDict)
        self.logger.info('functions_and_text = %s'%self.functions_and_text)

        for file in editFiles:
            self.string_on_file[file] = self.BuildDict(startwith=os.path.basename(file), 
                    hash=self.config, hashFiles1={})
            tmp = []
            for k,v in self.string_on_file[file].iteritems():
                tmp.append({ re.split(reg, v, 1)[0] :  re.split(reg, v, 1)[1] })
            self.string_on_file[file] = tmp
        self.logger.debug('dict_of_string_on_file=%s' % self.string_on_file)
        super(conf_app, self).__call__(editFiles=editFiles, methodDict=methodDict)

    def KeyVal(self, reg=r'^[\s\t]*(?P<key>%s(?P<space>[\s\t]*)=[\s\t]*).*', reg1=r'^[\s\t]*%s$'):
        """
        funtion descriptions -> modify lines in each file that exist in editFiles array.
        inputs:
        reg -> @type:string @para:regular expression
        reg1 -> @type:string @para:regular expression
        """
        # Snmp  initialization
        self.line_key = self.KeyOfLine(linesRef=self.linesRef)
        self.snmp_hash = self.DictOfSnmp(tmp=self.string_on_file[self.file.name])
        self.snmp_array = self.ArrayOfSnmp(tmp=self.string_on_file[self.file.name])
        snmp_flag = 0

        lines = []
        tmp = self.string_on_file[self.file.name]
        self.logger.debug('tmp=>%s' % tmp)
        for line in self.linesRef:
            f = 0
	
            for v in tmp:
                key_value = v.keys()[0]
                if  v.values()[0]:
                    try:
                        new_value = self.functions_and_text[v.values()[0]] 
                        if re.match(reg % key_value, line) and not new_value :
                            #Flag 1 to delete the line flag 0 to leave the line
                            if re.match(reg1 %str(self.config['Delete']).upper(), 'YES'):
                                self.logger.error('%s will be deleted' % (line.strip()))
                                f = 1
				v[key_value] = None
                            elif re.match(reg1 %str(self.config['Delete']).upper(), 'NO'):
                                f = 0
                                space = re.match(reg % key_value, line).group('space')
                                line = '%s%s=%s%s\n' % (key_value, space, space, new_value)
                                self.logger.debug('%s --> \"%s\"'  %(line.strip(), new_value))
				v[key_value] = None
                            else:
                                raise Exception, 'Value of Delete is => %s'\
                                 %str(self.config['Delete']).upper() 
                        elif line.split('=')[0].strip() == key_value and not new_value :
                            if re.match(reg1 %str(self.config['Delete']).upper(), 'YES'):
                                self.logger.error('%s will be deleted' % (line.strip()))
                                f = 1
                                v[key_value] = None
                            elif re.match(reg1 %str(self.config['Delete']).upper(), 'NO'):
                                f = 0
                                try:
                                    Fspace = re.search('([\s\t]*)([\s\t])(=)', line).group(2)
                                except:
                                    Fspace = ''

                                try:
                                    Lspace = re.search('([\s\t]*)(=)([\s\t])', line).group(3)
                                except:
                                    Lspace = ''
                                line = '%s%s=%s%s\n' % (key_value, Fspace, Lspace, new_value)
                                self.logger.debug('%s --> \"%s\"'  %(line.strip(), new_value))
                                v[key_value] = None
                            else:
                                raise Exception, 'Value of Delete is => %s'\
                                %str(self.config['Delete']).upper()
                        elif re.match(reg % key_value, line) and new_value :
                            self.logger.error('%s --> \"%s\"'  %(line.strip(), new_value))
                            if v.values()[0].startswith('Snmp_')and line.split('=')[0] in self.snmp_array:
                                 snmp_flag = 1
                            #Replace the line 
                            space = re.match(reg % key_value, line).group('space')
                            line = '%s%s=%s%s\n' % (key_value, space, space, new_value)
                            v[key_value] = None
                        elif line.split('=')[0].strip() == key_value and new_value :
                            self.logger.error('%s --> \"%s\"'  %(line.strip(), new_value))
                            if v.values()[0].startswith('Snmp_')and line.split('=')[0] in self.snmp_array:
                                snmp_flag = 1 
                            try:
                                Fspace = re.search('([\s\t]*)([\s\t])(=)', line).group(2)
                            except:
                                Fspace = ''

                            try:
                                Lspace = re.search('([\s\t]*)(=)([\s\t])', line).group(3)
                            except:
                                Lspace = ''
                            line = '%s%s=%s%s\n' % (key_value, Fspace, Lspace, new_value)
                            v[key_value] = None 
                    except:
                        self.logger.error(traceback.format_exc())
                        raise Exception, 'Failed to get the valuse of %s' % v.values()[0]
                else:
                    if re.match(reg1 %str(self.config['Append']).upper(), 'YES') and \
                            self.snmp_hash and  line.split('=')[0] not in self.snmp_array and snmp_flag==1:
                                for k1,v1 in self.snmp_hash.iteritems():
                                    self.logger.error('%s=%s will be append to Snmp section'\
                                            %(k1 , self.functions_and_text[v1]))
                                    lines.append(k1+'='+self.functions_and_text[v1]+'\n')
                                for k1,v1 in self.snmp_hash.iteritems():
                                    self.functions_and_text[v1] = 'no append'
                                self.snmp_hash = None
                                snmp_flag = 0 
                    v[key_value] = None
            if f == 0 :
                lines.append(line)
                
        self.AppendLines(lines=lines,tmp = self.string_on_file[self.file.name])            
        #Send the lines to the builder method to save the file              
        self.file.writelines(lines)    

    def Resolv(self):
        from commands import getstatusoutput as getstatus
        lines = []
        status=getstatus("echo > /etc/resolv.conf")
        if status[0] is 0:
            self.logger.debug("[I] Flushing /etc/resolv.conf")
        else:
            raise Exception, 'Error: %s' % status[1]  

        for dns in self.string_on_file[self.file.name]:
            for k,v in dns.iteritems():
                self.logger.error('%s  %s will be append'\
                                            %(k , self.functions_and_text[v]))
                line = '%s %s\n' % (k, self.functions_and_text[v])
            lines.append(line)
        self.file.writelines(lines)
        
