
'''
Authors: Dan Avrukin.
Contact: dan.avrukin@comverse.com
UpdateBy: Itzik Ben-Itzhak
Date: 06.06.2010
Module Name: Pymultiplier.py
Purpose: Preparation of configuration files for multiplied
         identifier and sm services.
'''

from string import lower, replace
from glob import glob
from re import search, sub, split
from shutil import copy2, copytree, move, rmtree
from os import system, remove
from os.path import exists, join as pJoin
from sys import exc_info
from Pyfiledit import builder, CopyUtils
from Pyconf import HashParser
from elementtree.ElementTree import Element, ElementTree, dump, parse as eparse

class tmedge(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(tmedge, self).__init__(config, componentID, loggerName='', *args, **kwargs)
        self.backupPath = self.__BuildConfigDict(config, 'BackupPath').get('BackupPath')
        self.instances = int(self.__BuildConfigDict(config, 'Instances').get('Instances')) -1
        self.defaultIncomingPort = self.__BuildConfigDict(config, 'DefaultIncomingPort').get('DefaultIncomingPort')
        self.defaultOutgoingPort = self.__BuildConfigDict(config, 'DefaultOutgoingPort').get('DefaultOutgoingPort')
        self.defaultRadiusPort = self.__BuildConfigDict(config, 'DefaultRadiusPort').get('DefaultRadiusPort')
        try: self.counterStartsFrom = int(self.__BuildConfigDict(config, 'CounterStartsFrom').get('CounterStartsFrom'))
        except: pass
        self.portIncrement = int(self.__BuildConfigDict(config, 'PortIncrement').get('PortIncrement'))
        self.targetsXmlFolder = self.__BuildConfigDict(config, 'TargetsXmlFolder').get('TargetsXmlFolder')
        self.targetsXmlFile = self.__BuildConfigDict(config, 'TargetsXmlFile').get('TargetsXmlFile')
        self.radiusXmlFolder = self.__BuildConfigDict(config, 'RadiusXmlFolder').get('RadiusXmlFolder')
        self.radiusXmlFile = self.__BuildConfigDict(config, 'RadiusXmlFile').get('RadiusXmlFile')
        self.clearBeforeRun = lower(self.__BuildConfigDict(config, 'ClearBeforeRun').get('ClearBeforeRun'))

        self.GwXmls = self.__CollectConfigVariables(config, 'conf.Gw.xml.1')
        self.RadiusXmls = self.__CollectConfigVariables(config, 'conf.RadiusMng.xml.1')

    def __call__(self, editFiles):
        '''
        tmedge class __call__ function.
        '''
        __name__ = 'tmedge __call__()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        self.logger.error('[%s] Working on file: %s' % (self.__Grn('i'), self.targetsXmlFile))

        if self.clearBeforeRun == 'yes':
            if self.GwXmls:
                for gwXml, path in self.GwXmls.iteritems():
                    treeRoot = self.__ClearExcessiveElements(gwXml, path, 'outboundPort')
            if self.RadiusXmls:
                for radiusXml, path in self.RadiusXmls.iteritems():
                    treeRoot = self.__ClearExcessiveElements(radiusXml, path, 'OutboundPort')

        if self.GwXmls:
            for gwXml, path in self.GwXmls.iteritems():
                xmlFile = self.__MultiplyRequiredElement(gwXml, path)

            self.logger.error('[%s] Finished working on %s\n' % (self.__Grn('*'), xmlFile))

        if self.RadiusXmls:
            for radiusXml, path in self.RadiusXmls.iteritems():
                xmlFile = self.__MultiplyRequiredElement(radiusXml, path)

            self.logger.error('[%s] Finished working on %s\n' % (self.__Grn('*'), xmlFile))

    def __ClearExcessiveElements(self, xmlFile, xmlTreePath, aimedText):
        '''
        Removes irrelevant xml elements that don't have
        the value of aimedText variable in one of their
        sub-elements.
        '''
        __name__ = '__ClearExcessiveElements()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        if 'Gw' in xmlFile:
            xmlFile = pJoin(self.targetsXmlFolder, search('(^conf\..*)(_\d+)', xmlFile).group(1))
        elif 'Radius' in xmlFile:
            xmlFile = pJoin(self.radiusXmlFolder, search('(^conf\..*)(_\d+)', xmlFile).group(1))
        Mapper, InPathNodes, tree, treeRoot = self.__ObtainRequiredVariables(xmlFile, xmlTreePath)
        for inPathNode in InPathNodes:
            if 'Gw' in xmlFile and inPathNode.find(aimedText).text != self.defaultOutgoingPort:
                self.logger.debug('[%s] Removing element "%s" with value "%s"' % (self.__Blu('i'), xmlTreePath, inPathNode.find(aimedText).text))
                Mapper[inPathNode].remove(inPathNode)
            elif 'Radius' in xmlFile and inPathNode.find(aimedText).text != self.defaultRadiusPort:
                self.logger.debug('[%s] Removing element "%s" with value "%s"' % (self.__Blu('i'), xmlTreePath, inPathNode.find(aimedText).text))
                Mapper[inPathNode].remove(inPathNode)
        self.__ReformatXmlTree(treeRoot, 0)
        self.__WriteXmlTree(tree, xmlFile)

    def __MultiplyRequiredElement(self, xmlFile, xmlTreePath):
        '''
        Multiplies the last element of the value of xmlTreePath
        as many times as predefined number of self.instances.
        '''
        __name__ = '__MultiplyRequiredElement()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        if 'Gw' in xmlFile:
            xmlFile = pJoin(self.targetsXmlFolder, search('(^conf\..*)(_\d+)', xmlFile).group(1))
        elif 'Radius' in xmlFile:
            xmlFile = pJoin(self.radiusXmlFolder, search('(^conf\..*)(_\d+)', xmlFile).group(1))
        Mapper, InPathNodes, tree, treeRoot = self.__ObtainRequiredVariables(xmlFile, xmlTreePath)
        for inPathNode in InPathNodes:
            for counter in range(self.counterStartsFrom, self.instances + 2):
                if 'Gw' in xmlFile:
                    clonedChild = Element(inPathNode.tag)
                    for inPathNodeChild in inPathNode:
                        if inPathNodeChild.tag == 'outboundPort':
                            clonedChildChild = Element(inPathNodeChild.tag)
                            clonedChild.append(clonedChildChild)
                            clonedChildChild.text = str(int(self.defaultOutgoingPort) + self.portIncrement * (counter - 1))
                        elif inPathNodeChild.tag == 'inboundPort':
                            clonedChildChild = Element(inPathNodeChild.tag)
                            clonedChild.append(clonedChildChild)
                            clonedChildChild.text = str(int(self.defaultIncomingPort) + self.portIncrement * (counter - 1))
                        else:
                            clonedChild.append(inPathNodeChild)
                    Mapper[inPathNode].append(clonedChild)
                elif 'Radius' in xmlFile:
                    clonedChild = Element(inPathNode.tag)
                    for inPathNodeChild in inPathNode:
                        if inPathNodeChild.tag == 'OutboundPort':
                            clonedChildChild = Element(inPathNodeChild.tag)
                            clonedChild.append(clonedChildChild)
                            clonedChildChild.text = str(int(self.defaultRadiusPort) + self.portIncrement * (counter - 1))
                        else:
                            clonedChild.append(inPathNodeChild)
                    Mapper[inPathNode].append(clonedChild)

        self.__ReformatXmlTree(treeRoot, 0)
        self.__WriteXmlTree(tree, xmlFile)

        return xmlFile
                
    def __ObtainRequiredVariables(self, xmlFile, xmlTreePath):
        '''
        Gets and returns the Mapper, InPathNodes, tree and treeRoot
        from the given xml file's xmlTreePath.
        '''
        __name__ = '__ObtainRequiredVariables()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        tree, treeRoot = self.__ParseXmlFile(xmlFile)
        Mapper = self.__MapXmlTree(treeRoot)
        Path = self.__PathAssembler(xmlTreePath)
        searchPath = self.__SetSearchString(Path)
        lastChild = Path[-1:][0]
        InPathNodes = treeRoot.findall(searchPath + lastChild)

        return Mapper, InPathNodes, tree, treeRoot

    def __ReformatXmlTree(self, elem, level=0):
        '''
        Reformating the XML for human consumption.
        Gets: (elem) root element as xml node,
              (level) starting identation level.
        Returns: N/A
        '''
        __name__ = '__ReformatXmlTree()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.__ReformatXmlTree(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def __CollectConfigVariables(self, config, pattern):
        '''
        Prepares a dictionary from key=value pairs
        located in a given configuration file.
        Returns a dictionary.
        '''
        __name__ = '__CollectConfigVariables()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))
    
        Configurations = {}
        for key, value in config.iteritems():
            if key.startswith(pattern):
                Configurations[key] = value
        return Configurations

    def __ParseXmlFile(self, fileName):
        '''
        Parses a given file and returns the tree and it's root.
        Gets: (editFile) path to the file to parse, as string.
        Returns: (tree) element tree instance, (treeRoot) root as
                 xml node.
        '''
        __name__ = '__ParseXmlFile()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        tree = eparse(fileName)
        treeRoot = tree.getroot()
        return tree, treeRoot 

    def __MapXmlTree(self, treeRoot):
        '''
        Creates a key:value dictionary of children and their owning parents.
        Gets: (treeRoot) root of the xml tree, as xml node.
        Returns: (Mapper) as dictionary.
        '''
        __name__ = 'MapXmlTree()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        self.treeRoot = treeRoot
        Mapper = dict( [ (child, parent) \
            for parent in treeRoot.getiterator() \
            for child in parent ] )
        return Mapper

    def __WriteXmlTree(self, tree, fileName):
        '''
        Writes an xml tree to file.
        Gets: (tree) an element tree instance, (fileName) as string.
        Returns: N/A.
        '''
        __name__ = '__WriteXmlTree()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        tree.write(fileName)

    def __SetSearchString(self, Path):
        '''
        Creates a search string up to a level above the target node.
        Gets: (Path) split path to the last element, as list.
        Returns: (searchPath) search path as string.
        '''
        __name__ = '__SetSearchString()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        self.Path = Path[1:]
        i, searchPath = 0, ''
        while i < len(self.Path) - 1:
            searchPath = searchPath + self.Path[i] + '/'
            searchPath = searchPath.lstrip('/')
            i += 1

        return searchPath

    def __PathAssembler(self, path):
        '''
        Splits the path string into a list
        and returns it.
        '''
        __name__ = '__PathAssembler()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        Path = split('\.', path)

        return Path

    def __BuildConfigDict(self, config, pattern, name='BuildConfigDict function'):
        '''
        Prepares a dictionary from key/value pairs
        located in a given configuration file.
        Returns a dictionary.
        '''
        __name__ = '__BuildConfigDict()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        Configurations = {}
        for key, value in config.iteritems():
            if key.startswith(pattern):
                Configurations[key] = value
        return Configurations

    def __ReadLines(self, filePath):
        '''
        Reading lines from file and
        returns them.
        '''
        __name__ = '__ReadLines()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))
        fh = open(filePath, 'r')
        Lines = fh.readlines()
        fh.close()
        return Lines

    def __GetFileBlockIndexes(self, firstLine, lastLine, Lines):
        '''
        Gets the indexes of first line and last line patterns,
        in given file lines.
        '''
        __name__ = '__GetFileBlockIndexes()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        firstLineIndex = None
        lastLineIndex = None
        counter = 0
        for line in Lines:
            if firstLine in line:
                try:
                    search('^\s*%s.*\n' % firstLine, line).group()
                    firstLineIndex = counter
                except: pass
            if lastLine in line and firstLineIndex:
                try:
                    if lastLine == ')':
                        search('^\s*\%s.*\n' % lastLine, line).group()
                    else:
                        search('^\s*%s.*\n' % lastLine, line).group()
                    lastLineIndex = counter
                except: pass
            if firstLineIndex and lastLineIndex:
                break
            counter += 1

        return firstLineIndex, lastLineIndex

    def __GetIndexedLines(self, firstIndex, lastIndex, Lines):
        '''
        Gets the lines of specific indexes and the lines
        between them, combining lines list.
        '''
        __name__ = '__GetIndexedLines()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        Block = []
        for index in range(firstIndex, lastIndex + 1):
            Block.append(Lines[index])

        return Block

    def __ClearExcessiveTrailings(self, line):
        '''
        Clears excessive trailing backslashes from
        a given line.
        '''
        __name__ = '__ClearExcessiveTrailings()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        if '\\t' in line or '\\n' in line:
            line = replace(replace(line, '\\t', '\t'), '\\n', '\n')

        return line

    def __Red(self, text):
        return "\033[31m%s\033[0m" % (text)
    def __Grn(self, text):
        return "\033[32m%s\033[0m" % (text)
    def __Ylw(self, text):
        return "\033[33m%s\033[0m" % (text)
    def __Blu(self, text):
        return "\033[34m%s\033[0m" % (text)


class mwasedge(builder):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        super(mwasedge, self).__init__(config, componentID, loggerName='', *args, **kwargs)

        self.backupPath = self.__BuildConfigDict(config, 'BackupPath').get('BackupPath')
        self.instances = int(self.__BuildConfigDict(config, 'Instances').get('Instances')) -1
        self.target = self.__BuildConfigDict(config, 'Target').get('Target')
        self.targetIdTag = self.__BuildConfigDict(config, 'TargetIdTag').get('TargetIdTag')
        self.targetApplicationTag = self.__BuildConfigDict(config, 'TargetApplicationTag').get('TargetApplicationTag')
        self.targetParentFolder = self.__BuildConfigDict(config, 'TargetParentFolder').get('TargetParentFolder')
        self.targetConfigFile = self.__BuildConfigDict(config, 'TargetConfigFile').get('TargetConfigFile')
        self.defaultIncomingPort = self.__BuildConfigDict(config, 'DefaultIncomingPort').get('DefaultIncomingPort')
        self.defaultRadiusPort = self.__BuildConfigDict(config, 'DefaultRadiusPort').get('DefaultRadiusPort')
        try: self.counterStartsFrom = int(self.__BuildConfigDict(config, 'CounterStartsFrom').get('CounterStartsFrom'))
        except: pass
        self.portIncrement = int(self.__BuildConfigDict(config, 'PortIncrement').get('PortIncrement'))
        try: self.folderIncrement = int(self.__BuildConfigDict(config, 'FolderIncrement').get('FolderIncrement'))
        except: pass
        self.clearBeforeRun = lower(self.__BuildConfigDict(config, 'ClearBeforeRun').get('ClearBeforeRun'))
        self.binariesOnly = lower(self.__BuildConfigDict(config, 'BinariesOnly').get('BinariesOnly'))
        if ( lower(self.target) == 'sm' or lower(self.target) == 'submng' ) \
        and not exists(pJoin(self.targetParentFolder, self.target)):
            self.target = 'subMng'
        self.targetOrigFolder = pJoin(self.targetParentFolder, '%s1' % self.target)
        self.targetNewFolder = pJoin(self.targetParentFolder, '%s' % self.target + '%s')
        self.targetPrevBinaryFile = pJoin(self.targetParentFolder, '%s' % self.target + '%s/bin' + '/%s1' % self.target)
        self.targetNewBinaryFile = pJoin(self.targetParentFolder, '%s' % self.target + '%s/bin' + '/%s' % self.target + '%s')
        self.targetConfigFolder = pJoin(self.targetParentFolder, '%s' % self.target + '%s/conf')

        if lower(self.target) == 'sm' or lower(self.target) == 'submng':
            self.target = 'sm'

    def __call__(self, editFiles):
        '''
        mwasedge class __call__ function.
        '''
        __name__ = 'mwasedge __call__()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        Methods = {self.targetConfigFile: '_mwasedge__ModifyTargetConfigFiles'}

        if self.clearBeforeRun == 'yes':
            self._MwasCleaner()
        if self.instances > 0:
            TargetConfigFiles = self.__MwasMultiplier()
            targetConfigFiles = ', '.join(TargetConfigFiles)
            CopyUtilsHandler = CopyUtils(Files = targetConfigFiles, Path = self.backupPath)
            CopyUtilsHandler.Backup()
            self.counter = self.counterStartsFrom
            try: builder.__call__(self, editFiles = TargetConfigFiles, methodDict = Methods)
            except:
                CopyUtilsHandler.RollBack()
                raise Exception, '%s detected: %s' % (exc_info()[0], exc_info()[1])

    def __MwasMultiplier(self):
        '''
        Handling the multiplication of target folders
        on Mwas.
        '''
        __name__ = '_MwasMultiplier()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))
        if self.instances != None and self.instances != 0:

            TargetConfigFiles = []

            for counter in range(self.counterStartsFrom, self.instances + 2):
                if self.binariesOnly == 'yes':
                    self.__CopyTargetBinariesOnly(counter)
                elif self.binariesOnly == 'no':
                    self.__CopyAndMoveTargetObjects(counter)
                TargetConfigFiles.append('%s/%s' % (self.targetConfigFolder % counter, self.targetConfigFile))

            return TargetConfigFiles

    def _MwasCleaner(self):
        '''
        Handling cleanups of multiplied targets,
        leaving only the original instance.
        '''
        __name__ = '_MwasCleaner()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))
    
        Instances = []
        TargetFolders = []
        if not exists(pJoin(self.targetParentFolder, '%s1' % self.target)) \
        and lower(self.target) == 'sm':
            self.logger.debug('[%s] Setting the target %s to be \'subMng\'' % (self.__Blu('i'), self.target))
            self.target = 'subMng'
        self.logger.debug('[%s] Collecting instances: %s...' % (self.__Blu('i'), \
                          pJoin(self.targetParentFolder, '%s*' % self.target)))
        for targetFolder in glob(pJoin(self.targetParentFolder, '%s*' % self.target)):
            try:
                Instances.append(search('(%s)(\d+)(.*)' % self.target, targetFolder).group(2))
                TargetFolders.append(targetFolder)
            except:
                pass

        if Instances:
            lastInstance = int(sorted(Instances)[-1:][0])
            self.logger.debug('[%s] Last instance: %s' % (self.__Blu('i'), lastInstance))
        else:
            lastInstance = None
            self.logger.debug('[%s] Last instance: None' % self.__Blu('i'))
    
        for targetFolder in TargetFolders:
            if lastInstance != None and str(lastInstance) in targetFolder:
                self.logger.debug('[%s] Last target folder instance: %s' % (self.__Blu('i'), targetFolder))
                lastTargetFolder = targetFolder
                break
    
        if lastInstance and self.binariesOnly == 'no':
            for instance in range(self.counterStartsFrom, lastInstance + 1):
                self.__RemoveEntireTree(instance)
        elif lastInstance and self.binariesOnly == 'yes':
            for instance in range(2, lastInstance + 1):
                self.__RemoveBinariesOnly(instance)

    def __RemoveBinariesOnly(self, instance):
        '''
        Removing the binaries of the target.
        '''
        __name__ = '__RemoveBinariesOnly()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        try:
            self.logger.debug('[%s] Removing file: %s/%s%s/bin/%s%s' % (self.__Blu('i'), \
                              self.targetParentFolder, self.target, instance, self.target, instance))
            remove('%s/%s%s/bin/%s%s' % (self.targetParentFolder, self.target, instance, self.target, instance))
        except:
            raise Exception, '%s detected: %s' % (exc_info()[0], exc_info()[1])

    def __RemoveEntireTree(self, instance):
        '''
        Removing the binaries of the target.
        '''
        __name__ = '__RemoveEntireTree()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        try:
            self.logger.debug('[%s] Removing tree: %s%s' % (self.__Blu('i'), self.target, instance))
            rmtree(pJoin(self.targetParentFolder, '%s%s' % (self.target, instance)))
        except:
            raise Exception, '%s detected: %s' % (exc_info()[0], exc_info()[1])

    def __CopyTargetBinariesOnly(self, counter):
        '''
        Handling the copying of targets binaries.
        '''
        __name__ = '__CopyTargetBinariesOnly()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        try:
            self.logger.debug('[%s] Trying to copy %s to %s' % (self.__Blu('i'), \
                              self.targetPrevBinaryFile % '1', \
                              self.targetNewBinaryFile % (counter, counter)))
            #copy2(self.targetPrevBinaryFile % '1', self.targetNewBinaryFile % (counter, counter))
            system('/bin/cp -a %s %s' % (self.targetPrevBinaryFile % '1', self.targetNewBinaryFile % (counter, counter)))
        except:
            self.logger.debug('[%s] Removing %s' % (self.__Blu('i'), \
                              self.targetNewBinaryFile % (counter, counter)))
            remove(self.targetNewBinaryFile % (counter, counter))
            self.logger.debug('[%s] Copying %s to %s' % (self.__Blu('i'), \
                              self.targetPrevBinaryFile % '1', \
                              self.targetNewBinaryFile % (counter, counter)))
            copy2(self.targetPrevBinaryFile % '1', self.targetNewBinaryFile % (counter, counter))
            system('/bin/cp -a %s %s' % (self.targetPrevBinaryFile % '1', self.targetNewBinaryFile % (counter, counter)))

    def __CopyAndMoveTargetObjects(self, counter):
        '''
        Handling the copying and moving of the target
        files and folders.
        '''
        __name__ = '__CopyAndMoveTargetObjects()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        try:
            self.logger.debug('[%s] Trying to copy %s to %s' % (self.__Blu('i'), \
                              self.targetOrigFolder, self.targetNewFolder % counter))
            #copytree(self.targetOrigFolder, self.targetNewFolder % counter)
            system('/bin/cp -a %s %s' % (self.targetOrigFolder, self.targetNewFolder % counter))
        except:
            self.logger.debug('[%s] Removing %s' % (self.__Blu('i'), self.targetNewFolder % counter))
            rmtree(self.targetNewFolder % counter)
            self.logger.debug('[%s] Copying %s to %s' % (self.__Blu('i'), \
                              self.targetOrigFolder, self.targetNewFolder % counter))
            #copytree(self.targetOrigFolder, self.targetNewFolder % counter)
            system('/bin/cp -a %s %s' % (self.targetOrigFolder, self.targetNewFolder % counter))
        try:
            self.logger.debug('[%s] Trying to move %s to %s' % (self.__Blu('i'), \
                              self.targetPrevBinaryFile % counter, \
                              self.targetNewBinaryFile % (counter, counter)))
            #move(self.targetPrevBinaryFile % counter, self.targetNewBinaryFile % (counter, counter))
            system('/bin/mv %s %s' % (self.targetPrevBinaryFile % counter, self.targetNewBinaryFile % (counter, counter)))
        except:
            self.logger.debug('[%s] Removing %s' % (self.__Blu('i'), \
                              self.targetNewBinaryFile % (counter, counter)))
            remove(self.targetNewBinaryFile % (counter, counter))
            self.logger.debug('[%s] Moving %s to %s' % (self.__Blu('i'), \
                              self.targetPrevBinaryFile % counter, \
                              self.targetNewBinaryFile % (counter, counter)))
            #move(self.targetPrevBinaryFile % counter, self.targetNewBinaryFile % (counter, counter))
            system('/bin/mv %s %s' % (self.targetPrevBinaryFile % counter, self.targetNewBinaryFile % (counter, counter)))

    def __ModifyTargetConfigFiles(self):
        '''
        Handling the modification of the target's
        configurations file.
        '''
        __name__ = '__ModifyTargetConfigFiles()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        for line in self.linesRef:
            if 'InboundPort' in line and '%s' % self.defaultIncomingPort in line:
                newIncomingPort = str(int(self.defaultIncomingPort) + self.portIncrement * (self.counter - 1))
                line = sub(self.defaultIncomingPort, newIncomingPort, line)
                self.logger.error('[%s] Identifier port "%s" was modified to "%s"' \
                               % (self.__Blu('i'), self.defaultIncomingPort, newIncomingPort))
            elif 'ListeningPort' in line and self.defaultRadiusPort in line:
                newRadiusPort = str(int(self.defaultRadiusPort) + self.portIncrement * (self.counter - 1))
                line = sub(self.defaultRadiusPort, newRadiusPort, line)
                self.logger.error('[%s] Identifier radius port "%s" was modified to "%s"' \
                               % (self.__Blu('i'), self.defaultRadiusPort, newRadiusPort))
            elif 'ProcessName' in line and self.targetIdTag in line:
                line = sub('%s1' % self.targetIdTag, '%s%s' % (self.targetIdTag, self.counter), line)
                self.logger.error('[%s] Identifier ProcessName tag value "%s1" was modified to "%s%s"' \
                               % (self.__Blu('i'), self.targetIdTag, self.targetIdTag, self.counter))
            elif 'ApplicationName' in line and self.targetApplicationTag in line:
                line = sub('%s\d*' % self.targetApplicationTag, '%s%s' % (self.targetApplicationTag, self.counter), line)
                self.logger.error('[%s] Identifier ApplicationName tag value "%s1" was modified to "%s%s"' \
                               % (self.__Blu('i'), self.targetApplicationTag, self.targetApplicationTag, self.counter))
            self.file.write(line)

        self.counter += 1

    def __BuildConfigDict(self, config, pattern, name='BuildConfigDict function'):
        '''
        Prepares a dictionary from key/value pairs
        located in a given configuration file.
        Returns a dictionary.
        '''
        __name__ = '__BuildConfigDict()'
        self.logger.debug('[%s] Accessing %s...' % (self.__Blu('i'), __name__))

        Configurations = {}
        for key, value in config.iteritems():
            if key.startswith(pattern):
                Configurations[key] = value
        return Configurations

    def __Red(self, text):
        return "\033[31m%s\033[0m" % (text)
    def __Grn(self, text):
        return "\033[32m%s\033[0m" % (text)
    def __Ylw(self, text):
        return "\033[33m%s\033[0m" % (text)
    def __Blu(self, text):
        return "\033[34m%s\033[0m" % (text)
