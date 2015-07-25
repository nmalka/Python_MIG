from Pymodule import Pylogger
from os.path import expanduser, dirname, basename, join as pJoin
from os import remove, system, rename, path
from paramiko import Transport, SFTPClient, DSSKey, SSHClient, AutoAddPolicy, rsakey, agent, util
from socket import socket
from re import search
from glob import glob
from time import strftime
from zipfile import ZipFile, is_zipfile
from tarfile import open as tOpen
from pdb import set_trace as st
from commands import getstatusoutput
from datetime import datetime, timedelta
import pickle
import sys, time

class mySSHClient(SSHClient): 
## overload the exec_command method 
    def exec_command(self, command, bufsize=-1, timeout=None): 
        chan = self._transport.open_session() 
        chan.settimeout(timeout) 
        chan.exec_command(command) 
        stdin = chan.makefile('wb', bufsize) 
        stdout = chan.makefile('rb', bufsize) 
        stderr = chan.makefile_stderr('rb', bufsize) 
        return stdin, stdout, stderr 


class Transporter(object):
    def __init__(self, \
                 timeout, \
                 remoteMachine, \
                 port, \
                 username, \
                 password, \
                 loggerName, \
                 pk, \
                 bufsize = 8192):
                 

        import logging
        self.logger = logging.getLogger(loggerName)
        
        self.timeout = timeout
        self.remoteMachine = remoteMachine
        self.port = port
        self.username = username
        self.password = password
        self.bufsize = bufsize
        self.pk = DSSKey.from_private_key_file(expanduser(pk))
        self.logger.info('Object succesfully created')
        self.logger.debug ('timeout = %s, remoteMachine = %s, port = %s, username = %s'%(self.timeout, self.remoteMachine, self.port, self.username))
        #util.log_to_file('paramiko.log')
        

    def Link(self,\
            sftp=None,\
            ssh=True):
        self.sock = socket()
        self.sock.settimeout(self.timeout)
        self.Errors = []
        self.protocol = []
        self.logger.info('Trying to start link using parameters [SSH=%s,SFTP=%s]'%(ssh,sftp))
        try:
            self.sock.connect((self.remoteMachine, self.port))

        except:
            self.Unlink()
            self.logger.error('Link: Could not open a socket [remoteMachine = %s, port = %s]' % (self.remoteMachine, self.port))
            

        self.transport = Transport(self.sock)

        try:
            if not self.password:
                self.transport.connect(username = self.username, pkey = self.pk)
                self.logger.info('Trying to connect using private key..')
            else:
                self.transport.connect(username = self.username, password = self.password)
                self.logger.info('Trying to connect using password..')

        except:
            if not self.password:
                self.logger.error('Private Key not installed and no password specified!')
                
            self.Unlink()
            self.logger.error('Could not connect using SFTP [remoteMachine = %s, Username = %s, port = %s]' %(self.remoteMachine, self.username, self.port))
            
            sftp=None

            
        if ssh:
            try:
                self.protocol.append(mySSHClient())
                self.ssh = self.protocol[-1]
                self.ssh.set_missing_host_key_policy(AutoAddPolicy())
                self.ssh.connect(self.remoteMachine, port = self.port, username = self.username, password = self.password)
                self.logger.info ('ssh connection created..')
            except:
                self.logger.error('Could not connect using SSH [remoteMachine = %s, Username = %s, port = %s]'%(self.remoteMachine, self.username, self.port))

        if sftp:
            try:
                if ssh == None:
                    self.logger.error ('SSH must be enabled in order to connect with SFTP')
                    
                
                self.protocol.append(SFTPClient.from_transport(self.transport))
                self.sftp = self.protocol[-1]
                self.client = self.sftp
                self.logger.info('sftp connection created..')
            except:
                self.logger.error ('Could not bring up SFTP connection')
                
                self.sftp=None
    
        return ssh, sftp
    
    def RemoteCommand (self, command, check_exit=True, OSD=None):
        try:
            if not self.ssh:
                raise Exception, 'SSH must be enabled on remote machine in order to run commands.'
            remoteHost = self.ssh
            if not command is 'close_connection':
                self.command = command
                stdin, self.output, stderr = remoteHost.exec_command(self.command, timeout=40)
                output_lines = self.output.readlines()
                fprint=''.join(output_lines)
                if OSD:
                    print fprint #On Screen Display formatted output
                self.logger.debug('output of remote command `%s` on [%s]: %s' %(self.command,\
                        self.remoteMachine,\
                        fprint))
                if check_exit:
                    errorList = stderr.readlines()
                    if len(errorList) !=0:
                        self.logger.error(errorList)
                        raise Exception, 'Failed to execute command %s on [%s]' %(self.command, \
                                self.remoteMachine)
                    else:
                        self.logger.info('Command `%s` on [%s] completed successfuly'%(self.command,\
                                self.remoteMachine))

            else:
                try:
                    self.logger.info ('Trying to close connections..')
                    self.Unlink()
                    self.logger.info ('Connections closed succesfully..')
                except:
                    self.logger.error('Could not close connections! ' )
                    
            return output_lines

        except:
             raise Exception, 'Could not complete the command %s'%(self.command)
             #raise
        
            


    def CopyToRemote(self, \
            localFolder, \
            remoteFolder, \
            fileName, \
            copyProtocol='scp', \
            scpCommand='scp -o ConnectTimeout=30 -p -P', \
            response = True):
        '''
        Gets: localFolder, remoteFolder, fileName
        Returns: Response.
        '''
        localFilePath = pJoin(localFolder, fileName)
        remoteFilePath = pJoin(remoteFolder, fileName)
        if copyProtocol == 'sftp':
            try:
                self.sftp.put(localFilePath, remoteFilePath)
                self.logger.info ('Copied file %s to %s:%s'%(localFilePath, self.remoteMachine, remoteFilePath))
        
            except AttributeError:
                self.logger.error('SFTP connection is not open')
                
                response = False
            except:
                raise Exception, 'Could not connect using SFTP'
                
               
            return response
        
        elif copyProtocol == 'scp':
            try:
                scpCopy=getstatusoutput('%s %s %s %s@%s:%s '%(self.scpCommand, self.port, localFilePath, self.username, \
                        self.remoteMachine, remoteFilePath))
                if scpCopy[0] != 0:
                    self.logger.error (scpCopy[1])
                    self.logger.error('Error %s: %s'%(scpCopy[0],self.Errors))
                    response = False
                else:
                    self.logger.info('Copied file from "%s" to "%s:%s" successfuly' % (localFilePath, \
                            self.remoteMachine, remoteFilePath))
            except:
                self.logger.error('Could not transfer file %s to [%s] using SCP'%(remoteFilePath,self.remoteMachine))
                
                response = False

        else:
            raise Exception, 'Unknown copy protocol "%s", scp and sftp support only'%copyProtocol
            response = False
        return response
            
  
    def RenameLocalFile (self, localFolder, OrigFileName, NewFileName):
        
        self.logger.info ('Renaming %s to %s'%(OrigFileName, NewFileName))
        localFilePath = pJoin(localFolder, OrigFileName)
        renamedFilePath = pJoin(localFolder, NewFileName)
        try:
            rename (localFilePath, renamedFilePath) 
        except:
            raise Exception, 'Could not rename file %s to %s'%(localFilePath, renamedFilePath)
             


    def Unlink(self):
        try:
            self.ssh.close()
        except:
            self.logger.error('No SSH client to close...')
        try:
            self.sftp.close()
        except:
            self.logger.error('No SFTP client to close...')
        try:
            self.transport.close()
        except:
            self.logger.error('No transport to close...')
        try:
            self.sock.close()
        except:
            self.logger('No socket to close...')

    def dotTmp(self, \
               localFileFolder, \
               localFileName, \
               remoteFileFolder, \
               remoteFileName, \
               index, \
               runType = 'put'):
        '''
        Gets: localFileFolder, localFileName,
              remoteFileFolder, remoteFileName,
              index, runType.
 
        Returns: True
        '''

        self.Errors = []
        response = True
        localFilePath = pJoin(localFileFolder, localFileName)
        remoteTempFilePath = pJoin(remoteFileFolder, '%s.%s.tmp' % (remoteFileName, index))
        remoteFilePath = pJoin(remoteFileFolder, '%s.%s' % (remoteFileName, index))

        try:
            if runType == 'put':
                self.client.put(localFilePath, remoteTempFilePath)
            elif runType == 'open':
                self._WriteLocalDataToRemoteFile(localFilePath, remoteTempFilePath)
        except:
            self.logger.error('Failed creating "%s" on the remote server "%s"' % (remoteFilePath, self.remoteMachine))
            response = False

        try:
            self.client.remove(remoteFilePath)
        except:
            pass

        try:
            self.client.rename(remoteTempFilePath, remoteFilePath)
        except:
            self.logger.error('Failed moving "%s" to "%s" on the remote server "%s"' % (remoteTempFilePath, remoteFilePath, self.remoteMachine))
            response = False

        if len(self.Errors) != 0:
            self.logger.error(self.Errors)
        return response


    def MD5Compare (self,
                    MD5File,
                    localFolder,
                    DPIFileType,
                    DateTimeFormat='%Y%m%d%H%M%S',
                    Collect=True,
                    Rename=True,
                    PRX_MD5Command = 'list-files',
                    copyProtocol='scp'):
        
#         '''
#         Gets: a file name made from  pickle.
#               a local folder where to files should be saved.
#         Returns: a list of changed files.
#         '''
        CurrentTimeDate=datetime.now().strftime(DateTimeFormat)
        listedFiles = self.GetMD5FromPrx(rqstType = DPIFileType, md5cmd = PRX_MD5Command)
        CurrentMD5Dict = {self.remoteMachine : listedFiles}
        
        if not path.exists(MD5File): # MD5File does not exist
            LastSavedDict = {}
        else:
            LastSavedDict = self._readMD5fromFile(MD5File)
            
        if LastSavedDict.get(self.remoteMachine, 0) == 0: # Machine not found in MD5File (First time accessing)
            LocalSavedDict = {}
            for ftype in DPIFileType:
                LocalSavedDict[ftype] = {}
        else:
            LocalSavedDict = LastSavedDict[self.remoteMachine]
            
        DPIMD5Dict = CurrentMD5Dict[self.remoteMachine]
        self.logger.debug ('Local Saved Files before copy = %s'%LocalSavedDict)
        
        if LocalSavedDict == DPIMD5Dict: ## If there was not change in files. 
            self.logger.info('All files are up to date. No files copied')
        else:
            changedFiles = []
            for ftype in DPIFileType:
                for fileName, md5 in DPIMD5Dict.get(ftype, {}).iteritems():
                    if md5 != LocalSavedDict.get(ftype, {}).get(fileName, ''):
                    #if LocalSavedDict.get(ftype, {}).get(md5, None):
                        if Collect:
                            self.Collector(localFolder=localFolder, remoteFolder=ftype, copyProtocol=copyProtocol,collectedFileName=fileName,collectedSuffix='',\
                                                       getLatestOnly = False, removeRemoteFiles = False)
                        if Rename:
                            (name, ext) = path.splitext(fileName)
                            self.RenameLocalFile(OrigFileName = fileName, NewFileName = name+'.'+self.remoteMachine+'.'+CurrentTimeDate+ext+'.report', \
                                                localFolder=localFolder)
                        if ftype not in LocalSavedDict: LocalSavedDict[ftype] = {}
                        LocalSavedDict[ftype][fileName] = md5
                        changedFiles.append(fileName)
            
            LastSavedDict[self.remoteMachine] = LocalSavedDict
            self.logger.debug('Local Saved Files after copy = %s'%LocalSavedDict)
            self._writeMD5toFile(MD5File,LastSavedDict)
            
    def CreatePrxStat(self,
                      remoteMachine,
                      localFolder,
                      DPI_Statistics,
                      filename,
                      Prefix,
                      Suffix,
                      cmdTimeout,
                      DateTimeFormat='%Y%m%d%H%M%S'):
        
        
        ''' Create statistic file from command (list-protocols --statistics) '''
        CurrentTimeDate=datetime.now().strftime(DateTimeFormat)
        command = self.RemoteCommand(DPI_Statistics, cmdTimeout)
        timestamp = int(time.time())
        
        try:
            f = '%s-%s.%s.%s%s' % (Prefix, filename, remoteMachine, CurrentTimeDate, Suffix)
            statfile = open(localFolder + f, 'w')
            #statfile.write('timestamp: ' + str(timestamp) + os.linesep)
            #statfile.write('system-id: ' + remoteMachine + os.linesep)
            statfile.write('timestamp: ' + str(timestamp) + '\n')
            statfile.write('system-id: ' + remoteMachine + '\n')
            for linestat in command:
                statfile.write(linestat)
            statfile.close()
        except:
            self.logger.error('Failed to Create %s file' % f)
            raise


    def dotDone(self, \
                localFileFolder, \
                localFileName, \
                remoteFileFolder, \
                remoteFileName, \
                doneFileFolder, \
                doneFileName, \
                doneFileSuffix, \
                index, \
                runType = 'put'):
        '''
        Gets: localFileFolder, localFileName,
              remoteFileFolder, remoteFileName,
              doneFileFolder, doneFileName,
              doneFileSuffix, index,
              runType.

        Returns: True
        '''

        self.Errors = []
        response = True
        localFilePath = pJoin(localFileFolder, localFileName)
        doneFilePath = pJoin(doneFileFolder, '%s.%s.%s' % (doneFileName, doneFileSuffix, index))
        remoteFilePath = pJoin(remoteFileFolder, '%s.%s' % (remoteFileName, index))
        remoteDoneFilePath = pJoin(doneFileFolder, '%s.delta.%s' % (remoteFileName, index))

        try:
            if runType == 'put':
                self.client.put(localFilePath, remoteFilePath)
                self.client.put(localFilePath, remoteDoneFilePath)
            elif runType == 'open':
                self._WriteLocalDataToRemoteFile(localFilePath, remoteFilePath)
                self._WriteLocalDataToRemoteFile(localFilePath, remoteDoneFilePath)
        except:
            self.logger.error('Failed creating "%s" on the remote server "%s"' % (remoteFilePath, self.remoteMachine))
            response = False

        try:
            self.client.open(doneFilePath, 'w').close()
        except:
            self.logger.error('Failed creating done file "%s" on the remote server "%s"' % (doneFilePath, self.remoteMachine))
            response = False

        if len(self.Errors) != 0:
            self.logger.error(self.Errors)

        return response

    
    def Collector(self, \
                  localFolder, \
                  remoteFolder, \
                  copyProtocol = 'sftp', \
                  collectedFileName = '', \
                  collectedSuffix = '', \
                  getLatestOnly = True, \
                  removeRemoteFiles = True):
        '''
        Gets: localFolder, remoteFolder,
              collectedFileName, collectedSuffix,
              getLatestOnly, removeRemoteFiles.
        Returns: True
        '''

        self.Errors = []
        response = True
        CollectedFiles = []
        RemoteFilesDict = {}
        if copyProtocol == 'sftp':
            if collectedFileName != '' and collectedSuffix == '':
                CollectedFiles.append(collectedFileName)
                remoteFilePath = pJoin(remoteFolder, collectedFileName)
                try:
                    RemoteFilesDict[0] = self.client.stat(remoteFilePath)
                    self.logger.debug ('Collected file name: %s'%(collectedFileName))
                except:
                    self.logger.error ('Could not get file stat for %s'%(collectedFileName))
                    

            elif collectedSuffix != '' and collectedFileName == '':
                RemoteFiles = self.client.listdir(remoteFolder)
                self.logger.debug ('Files in remote dir: %s'%(RemoteFiles))
                try:
                    suffix = search('(.*)(\.)(.*)', collectedSuffix).group(3)
                    self.logger.debug ('Filtered Suffix: %s'%(suffix))
                except:
                    self.logger.error('Invalid files suffix given: %s' % collectedSuffix)
                    
                    response = False

                for remoteFile in RemoteFiles:
                    try:
                        search('\.%s$' % suffix, remoteFile).group()
                        CollectedFiles.append(remoteFile)
                        remoteFilePath = pJoin(remoteFolder, remoteFile)
                        RemoteFilesDict[remoteFile] = self.client.stat(remoteFilePath)
                    except:
                        pass
                    #if remoteFile.endswith(collectedSuffix):
                    #    CollectedFiles.append(remoteFile)
                    #    remoteFilePath = pJoin(remoteFolder, remoteFile)
                    #    RemoteFilesDict[remoteFile] = self.client.stat(remoteFilePath)
                self.logger.debug ('Remote Files Dic: %s'%RemoteFilesDict)
            else:
                raise Exception, 'No remote file name or suffix specified'
                response = False
        
            if getLatestOnly == True and len(RemoteFilesDict) != 0:
                latestRemoteFile = self._GetLatestFile(RemoteFilesDict)
                self._GetRemoteFile(localFolder, remoteFolder, latestRemoteFile, copyProtocol)
                if removeRemoteFiles == True:
                    self._RemoveRemoteFile(remoteFolder, latestRemoteFile)
            elif getLatestOnly == False and len(RemoteFilesDict) != 0:
                for collectedFile in CollectedFiles:
                    try:
                        self._GetRemoteFile(localFolder, remoteFolder, collectedFile, copyProtocol=copyProtocol)
                        
                    except:
                        self.logger.error('Failed getting "%s" from remote host "%s" to local folder "%s"' \
                                       % (pJoin(remoteFolder, collectedFile), self.remoteMachine, localFolder))
                        
                        response = False
                    if removeRemoteFiles == True:
                        self._RemoveRemoteFile(remoteFolder, collectedFile)
            else:
                response = False
                self.logger.debug ('%s'%(len(RemoteFilesDict)))
            return response

        elif copyProtocol == 'scp':
            if getLatestOnly == True:
                self.logger.error ('Get latest only is not supported when using scp')
                getLatestOnly == False
            if removeRemoteFiles == True:
                self.logger.error ('Remote file removal is not supported when using scp')
                removeRemoteFiles == False
            try:
                self._GetRemoteFile(localFolder, remoteFolder, collectedFileName, copyProtocol=copyProtocol)
            except:
                response = False
                raise Exception, ('Could not get file %s from %s to %s'%(collectedFileName, remoteFolder, localFolder))
                
            return response
                
    
    def _writeMD5toFile(self, MD5File, dictionary={}):
        ## Write MD5 dictionary to file
        try:
            MD5ToSave = open (MD5File, 'wb')
            pickle.dump(dictionary, MD5ToSave)
            MD5ToSave.close()
            return MD5ToSave
        except:
            self.logger.error ('could not write MD5 file:\n%s:%s'%(sys.exc_info()[0],sys.exc_info()[1]))
    
    def _readMD5fromFile (self, MD5File):
        ## Read last saved MD5 dictionary from file. 
        LastSavedFile = open (MD5File,'rb')
        SavedMD5Dict = pickle.load(LastSavedFile)
        LastSavedFile.close()
        return SavedMD5Dict
    
                    
    def _WriteLocalDataToRemoteFile(self, localFilePath, remoteFilePath):
        '''
        Gets: localFilePath, remoteFilePath.
        Returns: N/A
        '''

        fh = open(localFilePath, 'r')
        Lines = fh.readlines()
        fh.close()

        rfh = self.client.open(filename = remoteFilePath, mode = 'w', bufsize = self.bufsize)
        for line in Lines:
            rfh.write(line)
        rfh.close()

    def _GetRemoteFile(self, localFolder, remoteFolder, collectedFileName, copyProtocol):
        '''
        Gets: localFolder, remoteFolder, collectedFileName.
        Returns: N/A
        '''
        remoteFilePath = pJoin(remoteFolder, collectedFileName)
        localFilePath = pJoin(localFolder, collectedFileName)
        if copyProtocol == 'sftp':
            try:
                self.client.get(remoteFilePath, localFilePath)
                self.logger.info('Copied file from "%s:%s" to "%s" successfuly' % (self.remoteMachine, remoteFilePath,\
                        localFilePath))
            except:
                self.logger.error('Could not get file %s from [%s] using SFTP'%(remoteFilePath,self.remoteMachine))
                
        
        elif copyProtocol == 'scp':
            scpCopy=getstatusoutput('scp -o ConnectTimeout=5 -p -P %s %s@%s:%s %s'%(self.port, self.username, self.remoteMachine, \
                    remoteFilePath, localFilePath))
            if scpCopy[0] != 0:
                self.logger.error (scpCopy[1])
                self.logger.error('Could not get file %s from [%s] using SCP'%(remoteFilePath,self.remoteMachine))
                self.logger.error(self.Errors)
                print ('%s'%self.Errors[0])

            else:
                self.logger.info('Copied file from "%s:%s" to "%s" successfuly' % (self.remoteMachine, \
                        remoteFilePath, localFilePath))
        else:
            self.logger.error('Unknown copy protocol %s, scp and sftp support only'%copyProtocol)


    def GetMD5FromPrx (self, rqstType, md5cmd='list-files'):
        try:
            fileType = {}
            for r in rqstType:
                fileType[r] = {}
            command = self.RemoteCommand(md5cmd)              
            found = False
            ignoreFileType = True
            for line in command:
                lineList = line.split()
                for fType in fileType: #.keys():
                    if fType == line[1:].strip()[:-1]:
                        if fType not in rqstType:
                            ignoreFileType = True
                        else:
                            ignoreFileType = False
                        type = fType
                        found = True
                        break
                    else:
                        found = False
                if found: continue
                if lineList and not ignoreFileType:
                    try:
                        #fileType[type].update({lineList[-2] : lineList[-1]}) ## {md5:file}
                        fileType[type].update({lineList[-1] : lineList[-2]})  ## {file:md5}
                    except IndexError:
                        ignoreFileType = True
            self.logger.debug ('File Dictionary on PRX %s'%fileType) 
            return fileType
        except:
            self.logger.error ('Could not get md5cmd from PRX: %s:%s'%(sys.exc_info()[0],sys.exc_info()[1]))

        
    def _GetLatestFile(self, SftpClientFilesDict):
        '''
        Gets: SftpClientFilesDict.
        Returns: latestFileName.
        '''
        latest = 0
        for sftpClientFile in SftpClientFilesDict.iterkeys():
            if SftpClientFilesDict[sftpClientFile].st_mtime > latest:
                latestFileName = sftpClientFile
                latest = SftpClientFilesDict[sftpClientFile].st_mtime
        return latestFileName


    def _RemoveRemoteFile(self, remoteFileFolder, remoteFile):
        '''
        Gets: remoteFileFolder, remoteFile.
        Returns: N/A.
        '''
        remoteFilePath = pJoin(remoteFileFolder, remoteFile)
        try:
            self.client.remove(remoteFilePath)
            self.logger.info('Removing remote file "%s"' % remoteFilePath)
        except:
            raise Exception, 'Failed removing remote file "%s"...' % remoteFilePath

class Compressor(object):
        def __init__(self, \
                     localFolder, \
                     compressedFileFolder, \
                     compressedFileName, \
                     collectedFileName = '', \
                     collectedSuffix = '', \
                     removeCompressedFiles = True):

            self.localFolder = localFolder
            self.compressedFileFolder = compressedFileFolder
            self.compressedFileName = compressedFileName
            self.collectedFileName = collectedFileName
            self.collectedSuffix = collectedSuffix
            self.removeCompressedFiles = removeCompressedFiles
            self.compressedFilePath = pJoin(compressedFileFolder, compressedFileName)

        def _GetFilesToCompress(self):
            FilesToCompress = []

            if self.collectedFileName != '' and self.collectedSuffix == '':
                filePath = pJoin(self.localFolder, self.fileName)
                FilesToCompress.append(filePath)

            elif self.collectedFileName == '' and self.collectedSuffix != '':
                try:
                    search('(\*)(\.)(.+$)', self.collectedSuffix).group()
                except:
                    raise Exception, 'Incorrect suffix given: "%"' % self.collectedSuffix
                suffixedFilesPath = pJoin(self.localFolder, self.collectedSuffix)
                FilesToCompress = glob(suffixedFilesPath)
            return FilesToCompress

        def Zip(self):
            try:
                response = True
                FilesToCompress = self._GetFilesToCompress()

                zfh = ZipFile('%s.zip' % self.compressedFilePath, 'w')
                for fileToCompress in FilesToCompress:
                    zfh.write(str(fileToCompress))
                    if self.removeCompressedFiles == True:
                        remove(str(fileToCompress))
                zfh.close()
            except:
                response = False
            return response

        def Tgz(self):
            try:
                response = True
                FilesToCompress = self._GetFilesToCompress()

                tfh = tOpen('%s.tgz' % self.compressedFilePath, 'w:gz')
                for fileToCompress in FilesToCompress:
                    tfh.add(str(fileToCompress))
                    if self.removeCompressedFiles == True:
                        remove(str(fileToCompress))
                tfh.close()
            except:
                response = False
            return response
