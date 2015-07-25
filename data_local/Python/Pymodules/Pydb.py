
####################################
#   By: Yaron Cohen                #
#   Mail: yaron.cohen@comverse.com #
#   Ver: 4.8                       #
#   Date: 23/09/09                 #
#   ModuleNmae: Pydb.py            #
####################################

import os
import sys, string, datetime
import re
import cx_Oracle
from Pymodule import *
from Pyfiledit import builder
from Pyfiledit import filesToBakup
import pwd
from Pyfunc import *
from Pyconf import HashParser
from commands import getstatusoutput as getstatus

class dict(object):
    def GetHash(self,file,reg):
        hash = {}
        for line in open(file):
            if not line.startswith('#'):
                if line.strip():
                    line = line.strip()
                    line = re.sub(r',[\s\t]*$', '', line)
                    hash[re.split(r'[\s\t]?%s[\s\t]?'%reg,
                    line, 1)[0]] = re.split(r'[\s\t]?%s[\s\t]?'%reg, line,1)[1].strip()
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


    def ManipulationValue(self,value):
        for type in self.type.values():
            counter=0
            bingo=value.count(type)
            while counter < bingo:
                value1=re.search('(\s*)(.*)(%s)(.*)'%type,value ).group(2)             
                value=value1 +"'"+self.functions_and_text[re.search('(\s*)(.*)(%s\d+)(.*)'%type,value )\
                   .group(3)]+"'" + re.search('(\s*)(.*)(%s\d+)(.*)'%type,value ).group(4)
                counter=counter+1 
        self.logger.error('[I] Going to execute --> %s' % value)
        return value

class oracle(builder, dict):

    def __init__(self, config, Argv, componentID, loggerName = '', *args, **kwargs):
        super(oracle, self).__init__(config=config, Argv=Argv, componentID=componentID, \
                             loggerName=loggerName, *args, **kwargs)
        os.chmod(self.config['LogFile'],0666)
        self.Argv = Argv
        self.user_name = self.config['User']
        self.sql_password,self.sql_user,self.AS,self.sid = self.GetSqlParam(self.Argv)     
        self.HashParser = HashParser()
        self.type = self.HashParser.BuildDict(startwith='Type_',hash=self.config,hashFiles1={}) 
        self.functions_and_text = self.GetFunctionsAndTextParams(type=self.type)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text)
        self.cursor = self.HashParser.BuildDict(startwith='Cursor_',hash=self.config,hashFiles1={})
         
    def __call__(self, *args, **kwargs):
        self.uid = self.GetUid(self.user_name)
        self.uid = self.SetUid(self.uid)
        self.Export_SID(self.sid) 
        self.sysdba_handle = self.ConnectToDB(self.sql_user, self.sql_password, self.sid, self.AS)
        self.CallToCurserMethod(cursor_values=self.cursor.values,sysdba_handle=self.sysdba_handle)
        self.sysdba_handle.commit()

    def CallToCurserMethod(self,cursor_values,sysdba_handle):
        for value in cursor_values():
            value=self.ManipulationValue(value)
            self.Curser(sysdba_handle=sysdba_handle,value=value)

    def GetFunctionsAndTextParams(self,type,functions_and_text = {}):
        for type in type.values():
            functions_and_text = self.HashParser.BuildDict(startwith=type,hash=self.config,\
                                      hashFiles1=functions_and_text)
        return functions_and_text

    def GetSqlParam(self,Argv):
        try:
            self.sql_user = re.search('(\s*)(.*)(/)(.*)',Argv[0] ).group(2)
            self.AS = ""
            try:
                self.sid = re.search('(\s*)(.*)(@)(.*)',Argv[0] ).group(4)
                self.sql_password = re.search('(\s*)(.*)(/)(.*)(@)',Argv[0] ).group(4)
            except:
                self.sid = self.config['Sid']
                self.sql_password = re.search('(\s*)(.*)(/)(.*)',Argv[0] ).group(4)
            self.logger.error('[I] run as %s/%s@%s' %(self.sql_user,self.sql_password,self.sid)) 
        except :
            self.sid = self.config['Sid']
            self.sql_password = self.config['Sql_P'] 
            self.sql_user = self.config['Sql_N']
            self.AS = ''
            if self.sql_user == self.config.get('oracle_admin_user', 'sys'):
                self.AS = cx_Oracle.SYSDBA# | cx_Oracle.PRELIM_AUTH
                self.logger.error('run as sys dba')
        return self.sql_password,self.sql_user,self.AS,self.sid 

    def GetUid(self,user_name):
        self.configuration = self.GetHash(file='/etc/nsswitch.conf',reg=':')
        if self.configuration['passwd'] == 'files sss':
            self.logger.debug('/etc/nsswitch.conf = files sss')
            uid=pwd.getpwnam(user_name).pw_uid
            self.logger.error('Getting Id for user %s --> %s' %(self.user_name,uid))
        else:
           self.logger.error('The application not supporting get user ID from %s'%self.config['passwd'])
           raise Exception, 'Failed to get user_id of %s' %self.config['passwd']
        return uid

    def SetUid(self,uid=0):
        try:
            os.setuid(uid)
            self.logger.error('Change User Id to %s' %uid)
        except:
            raise Exception, 'Failed to change to user_id %s' %uid

    def ConnectToDB(self,sql_user,sql_password,sid,AS):
        if not AS:
            try:
                sysdba_handle=cx_Oracle.connect(sql_user,sql_password,sid)
                self.logger.error('Connecting to Oracle with %s/%s@%s ' % (sql_user,sql_password, sid))
            except:
                self.logger.error('Failed to Connect Oracle with: %s/%s@%s ' % (sql_user,sql_password, sid))
                raise         
        else:
            try:
                sysdba_handle=cx_Oracle.connect(sql_user,sql_password,sid,AS)
                self.logger.error('Connecting to %s/%s@%s AS=%s' % (sql_user,sql_password, sid, AS))
            except:
                self.logger.error('Failed to Connect Oracle with: %s/%s@%s AS=%s' % (sql_user,sql_password, sid, AS))
                raise
        return sysdba_handle

    def Export_SID(self,sid):
        if sid is not 'APPDB':
           os.environ['ORACLE_SID'] = sid 
           self.logger.debug('[I] export ORACLE_SID -- > %s'%sid)

    def Curser(self,value,sysdba_handle):
        cursor = sysdba_handle.cursor()
        cursor.execute(value)
        if re.match(r'^[\s\t]*%s$' %str(self.config['Debug']).upper(), 'TRUE'):
            self.Debug(rowcount=cursor.rowcount, value=value)


    def Debug(self, rowcount, value):
        if not rowcount > 0 :
            self.logger.error('[E] in %s' %value)
            raise Exception, 'Error: %s' %value

class oracle_start(oracle):
    
    def __call__(self, *args, **kwargs):
        uid = self.GetUid(self.user_name)
        uid = self.SetUid(uid)
        self.Export_SID(self.sid)
        self.ListenerStart()
        self.AS = cx_Oracle.SYSDBA | cx_Oracle.PRELIM_AUTH
        sysdba_handle = self.ConnectToDB(self.sql_user, self.sql_password, self.sid, self.AS)
        self.StartUpDB(sysdba_handle)

    def StartUpDB(self,sysdba_handle):
        try:
            sysdba_handle.startup()      
            sysdba_handle = self.ConnectToDB(self.sql_user, self.sql_password, self.sid, AS=cx_Oracle.SYSDBA)
            cursor = sysdba_handle.cursor()
            cursor.execute('alter database mount')
            self.logger.debug("alter database mount")
            cursor.execute('alter database OPEN ')
            self.logger.debug("alter database OPEN")
            self.logger.error('[I] %s is StartUp '%self.sid)
        except cx_Oracle.DatabaseError,ex:
            if not re.split(r'[\s\t]*:[\s\t]*',str(ex),1)[0] == 'ORA-01081':
                self.logger.debug('[E] %s'%str(ex))
                raise Exception, 'Error: %s'%str(ex)
            else:
                self.logger.error('[W] %s'%str(ex)) 

    def ListenerStart(self):
        os.system("lsnrctl start %s" % self.log) 

   

class oracle_stop(oracle):
    def __call__(self, *args, **kwargs):
        uid = self.GetUid(self.user_name)
        uid = self.SetUid(uid)
        self.Export_SID(self.sid)
        sysdba_handle = self.ConnectToDB(self.sql_user, self.sql_password, self.sid, self.AS)
        self.ShutdownDB()
        self.ListenerStop()

    def ShutdownDB(self,mode=cx_Oracle.DBSHUTDOWN_ABORT):
        try:
            sysdba_handle = self.ConnectToDB(self.sql_user, self.sql_password, self.sid, AS=cx_Oracle.SYSDBA)
            sysdba_handle.shutdown(mode = mode)
            self.logger.error('[I] %s is ShutDown '%self.sid)
        except cx_Oracle.DatabaseError,ex:
            self.logger.debug('[E] %s'%str(ex))
            raise Exception, 'Error: %s'%str(ex)    

    def ListenerStop(self):
        os.system("lsnrctl stop %s" %self.log)


class bring_interface_online(oracle):
    def __call__(self, *args, **kwargs):
        self.interface=self.build_dict(startwith='Interface_',hash=self.config)
        self.functions_and_text = self.GetFunctionsAndTextParams(type=self.type)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text)
        for k,v in  self.interface.iteritems():
            self.InterfaceExist(interface=k,ip=self.functions_and_text[v['ip']],\
                                mask=self.functions_and_text[v['mask']])  


    def build_dict(self, startwith, hash, hashFiles1={}, reg=r'[\s\t]*=[\s\t]*'):
        for k,v in hash.iteritems():
            if re.split(reg, k, 1)[0].startswith(startwith) :
                try:    
                    hashFiles1[re.split(reg, v, 1)[0]]
                    hashFiles1[re.split(reg, v, 1)[0]][re.split(reg, re.split(reg, v, 1)[1], 1)[0]]=\
                            re.split(reg, re.split(reg, v, 1)[1], 1)[1]
                except:
                    hashFiles1[re.split(reg, v, 1)[0]]={re.split(reg, re.split(reg, v, 1)[1], 1)[0]\
                                :re.split(reg, re.split(reg, v, 1)[1], 1)[1]}     
        return hashFiles1

    def InterfaceExist(self,interface,ip,mask):
        try:
            int = os.popen('ifconfig %s ' % interface )
            net = int.readlines()
            int.close()
            re.search('addr:',str(net)).group()
            self.logger.error('[W] The interface %s already Up' %interface)
        except:
            self.AssignIpAdress(interface,ip,mask)

    def AssignIpAdress(self,interface,ip,mask):
        self.logger.debug("ifconfig %s %s netmask %s %s" %(interface,ip,mask,self.log))
        status=getstatus("ifconfig %s %s netmask %s %s" %(interface,ip,mask,self.log))
        if status[0] is 0:
            self.logger.error("[I] bring online %s with IP %s and mask %s" %(interface,ip,mask))
        else:
            self.logger.error("[E] Can't bring online %s with IP %s and mask %s" %(interface,ip,mask))
            raise Exception, 'Error: %s' % status[1]
