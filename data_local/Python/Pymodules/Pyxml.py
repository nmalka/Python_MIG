
'''
Authors: Dan Avrukin.
Contact: dan.avrukin@comverse.com
Ver: 5.3.2
Date: 31.03.2010.001
Module Name: Pyxml.py
Purpose: Deletion, Modification, Appendix, Cloning of XML elements.
'''

from Pyfiledit import builder
from Pydecorators import *
from elementtree.ElementTree import Element, ElementTree, dump, parse as eparse
from Pyfunc import *
from Pyconf import HashParser
from os import getcwd
from os.path import join as pJoin, basename, dirname, exists
from string import lower
import os, time, re ,sys
import traceback

class xml_config(builder, HashParser):
    def __init__(self, config, componentID, loggerName='', *args, **kwargs):
        '''
        Initializes the xml_config class.
        Creates dictionaries of key:value configurations, which are taken
        from the config dictionary.
        Passed to this class from runner.py.
        '''
        super(xml_config, self).__init__(config, componentID, loggerName='', *args, **kwargs)
        self.className = 'xml_config()'
        try:
            self.forcedPush = lower(self.config['ForcedPush'])
        except:
            self.forcedPush = None
        Patterns = \
            {'txt':'Text_', \
             'snmp':'Snmp_', \
             'blkf':'BlockFile_', \
             'blk':'Block_', \
             'modtxt':'Modify_', \
             'modattr':'ModifyAttr_', \
             'del':'Delete_', \
             'dig':'DigHostIP_', \
             'apndTag':'AppendTag_', \
             'apndBlk':'AppendBlock_', \
             'func':'Function_', \
             'clone':'Clone_'}

        self.Function = self.BuildConfigDict(config, Patterns['func'])
        self.Snmp = self.BuildConfigDict(config, Patterns['snmp'])
        self.Text = self.BuildConfigDict(config, Patterns['txt'])
        self.BlockFile = self.BuildConfigDict(config, Patterns['blkf'])
        self.Block = self.BuildConfigDict(config, Patterns['blk'])
        self.ModText = self.BuildConfigDict(config, Patterns['modtxt'])
        self.ModAttr = self.BuildConfigDict(config, Patterns['modattr'])
        self.Delete = self.BuildConfigDict(config, Patterns['del'])
        self.DigHostIP = self.BuildConfigDict(config, Patterns['dig'])
        self.AppendTag = self.BuildConfigDict(config, Patterns['apndTag'])
        self.AppendBlock = self.BuildConfigDict(config, Patterns['apndBlk'])
        self.Clone = self.BuildConfigDict(config, Patterns['clone'])

    def __call__(self, editFiles):
        '''
        Makes calls to internal functions of the xml_config class.
        '''
    
        self.EditFiles = self.config.get('XML_Files', editFiles)

        Patterns = \
            {'txt':'Text_', \
             'snmp':'Snmp_', \
             'blkf':'BlockFile_', \
             'blk':'Block_', \
             'modtxt':'Modify_', \
             'modattr':'ModifyAttr_', \
             'del':'Delete_', \
             'dig':'DigHostIP_', \
             'apndTag':'AppendTag_', \
             'apndBlk':'AppendBlock_', \
             'func':'Function_', \
             'clone':'Clone_'}

        for editFile in self.EditFiles:
            PerFileDicts = []
            self.Function= self.BuildConfigDict(self.config, Patterns['func'])
            config = {}
            pattern = basename(editFile)
            self.PerFileDict = self.BuildConfigDict(self.config, pattern + '_')
            if self.PerFileDict:
                for key in self.PerFileDict:
                    PerFileDicts.append(self.PerFileDict[key])
            else:
                self.logger.error('[%s] Couldn\'t find any configurations for file %s, skipping' % (self.Ylw('w'), editFile))
                continue

            for perFileDict in PerFileDicts:
                config[re.split('=', perFileDict, 1)[0]] = re.split('=', perFileDict, 1)[1]

            self.ModText = self.BuildConfigDict(config, Patterns['modtxt'])
            self.ModAttr = self.BuildConfigDict(config, Patterns['modattr'])
            self.Delete = self.BuildConfigDict(config, Patterns['del'])
            self.DigHostIP = self.BuildConfigDict(config, Patterns['dig'])
            self.AppendTag = self.BuildConfigDict(config, Patterns['apndTag'])
            self.AppendBlock = self.BuildConfigDict(config, Patterns['apndBlk'])
            self.Clone = self.BuildConfigDict(config, Patterns['clone'])
        
            self.Function = self.GetValueFromFunctionToDict(self.Function)
            self.Snmp = self.GetValues(self.Snmp)
            self.Text = self.GetValues(self.Text)
            self.BlockFile = self.GetValues(self.BlockFile)
            self.ModText = self.GetValues(self.ModText)
            self.ModAttr = self.GetValues(self.ModAttr)
            self.AppendTag = self.GetValues(self.AppendTag)
            self.AppendBlock = self.GetValues(self.AppendBlock)
            self.Delete = self.GetValues(self.Delete)
            self.Clone = self.GetValues(self.Clone)
    
            self.logger.debug('[d] Snmp=%s' % self.Snmp)
            self.logger.debug('[d] Text=%s' % self.Text)
            self.logger.debug('[d] BlockFile=%s' % self.BlockFile)
            self.logger.debug('[d] Block=%s' % self.Block)
            self.logger.debug('[d] DigHostIP=%s' % self.DigHostIP)
            self.logger.debug('[d] ModText=%s' % self.ModText)
            self.logger.debug('[d] ModAttr=%s' % self.ModAttr)
            self.logger.debug('[d] AppendTag=%s' % self.AppendTag)
            self.logger.debug('[d] AppendBlock=%s' % self.AppendBlock)
            self.logger.debug('[d] Delete=%s' % self.Delete)
            self.logger.debug('[d] Clone=%s' % self.Clone)

            try:
                fh = open(editFile, 'r')
                line = fh.readline()
                fh.close()
                tree, treeRoot = self.ParseXmlFile(editFile)
                self.editFile = editFile
                self.logger.error('[%s] Parsing the file %s' % (self.Blu('*'), editFile))
            except:
                self.logger.error('Couldn\'t parse the file %s, incorrect syntax' % editFile)
                sys.exit(911)

            header = self.GetHeader(editFile)
    
            if len(self.Delete.keys()) > 0:
                role = 'Deletion'
                self.Deletion(treeRoot, role)
            if len(self.AppendBlock.keys()) > 0:
                role = 'Block'
                self.Appendix(treeRoot, role)
            if len(self.AppendTag.keys()) > 0:
                role = 'Tag'
                self.Appendix(treeRoot, role)
            if len(self.Clone.keys()) > 0:
                role = 'Cloning'
                self.Cloning(treeRoot, role)
            if len(self.ModText.keys()) > 0:
                role = 'ModText'
                self.Modification(treeRoot, role)
            if len(self.ModAttr.keys()) > 0:
                role = 'ModAttr'
                self.Modification(treeRoot, role)
    
            self.ReformatXmlTree(treeRoot, 0)
            self.WriteXmlTree(tree, editFile)
            self.logger.debug('[%s] Appending xml header to "%s"...' % (self.Blu('i'), editFile))
            self.AppendHeader(editFile, line)
            self.logger.error('[%s] Finished working on %s\n' % (self.Blu('*'), editFile))
        
    def ParseXmlFile(self, editFile):
        '''
        Parses a given file and returns the tree and it's root.
        Gets: (editFile) path to the file to parse, as string.
        Returns: (tree) element tree instance, (treeRoot) root as
                 xml node.
        '''

        methodName = 'ParseXmlFile()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.editFile = editFile
        tree = eparse(self.editFile)
        treeRoot = tree.getroot()
        return tree, treeRoot 

    def MapXmlTree(self, treeRoot):
        '''
        Creates a key:value dictionary of children and their owning parents.
        Gets: (treeRoot) root of the xml tree, as xml node.
        Returns: (Mapper) as dictionary.
        '''

        methodName = 'MapXmlTree()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.treeRoot = treeRoot
        Mapper = dict( [ (child, parent) \
            for parent in treeRoot.getiterator() \
            for child in parent ] )
        return Mapper

    def WriteXmlTree(self, tree, fileName):
        '''
        Writes an xml tree to file.
        Gets: (tree) an element tree instance, (fileName) as string.
        Returns: N/A.
        '''

        methodName = 'WriteXmlTree()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        tree.write(fileName)

    def Replacement(self, treeRoot, replaceBlkPath):
        '''
        Replaces a certain tag in the working-file with
        a tag named the same, from a defined block file.
        Gets: treeRoot, replaceBlkPath
        Returns: N/A
        '''

        path, Path = self.GetBlockPath(replaceBlkPath)
        wrkFileBaseName = basename(self.editFile)
        blkFile = pJoin('/data_local/Python/confPy/Blocks', wrkFileBaseName)
        if exists(blkFile):
            blkFileTree = eparse(blkFile)
            blkFileRoot = blkFileTree.getroot()

            searchPath = self.SetSearchString(Path)
            lastChild = Path[len(Path) - 1]

            ModInPathNodes = treeRoot.findall(searchPath + lastChild)
            if len(ModInPathNodes) > 1:
                self.logger.error('[%s] Found multiple targets, expected one, handling only the first...' % self.Ylw('w'))

            preModInPathNode = treeRoot.find(searchPath)
            modInPathNode = treeRoot.find(searchPath + lastChild)
            blkInPathNode = blkFileRoot.find(searchPath + lastChild)

            if modInPathNode == None and blkInPathNode != None:
                preModInPathNode.append(blkInPathNode)
                self.logger.error('[%s] Appended block "%s" to "%s"' \
                               % (self.Grn('i'), '.'.join(Path), self.editFile))
            elif modInPathNode != None and blkInPathNode != None and self.forcedPush != None:
                if 'f' in self.forcedPush:
                    self.logger.debug('[%s] ForcedPush is "%s"' \
                                   % (self.Blu('d'), self.forcedPush))
                    self.logger.error('[%s] Skipping "%s" - already exists in "%s"' \
                                   % (self.Ylw('w'), '.'.join(Path), self.editFile))
                elif 't' in self.forcedPush:
                    preModInPathNode.remove(modInPathNode)
                    preModInPathNode.append(blkInPathNode)
                    self.logger.debug('[%s] ForcedPush is "%s"' \
                                   % (self.Blu('d'), self.forcedPush))
                    self.logger.error('[%s] Updated block "%s" in "%s"' \
                                   % (self.Grn('i'), '.'.join(Path), self.editFile))
            elif modInPathNode != None and blkInPathNode != None and self.forcedPush == None:
                    self.logger.debug('[%s] ForcedPush doesn\'t exist, defaulting to "False"' \
                                   % self.Blu('d'))
                    self.logger.error('[%s] Skipping "%s" - already exists in "%s"' \
                                   % (self.Ylw('w'), '.'.join(Path), self.editFile))
            elif modInPathNode == None and blkInPathNode == None:
                self.logger.error('[%s] Block "%s" couldn\'t be found in either "%s" or "%s"' \
                               % (self.Ylw('w'), '.'.join(Path), self.editFile, blkFile))
        else:
            raise Exception, '[%s] Couldn\'t replace "%s", %s is missing, exiting...' % (self.Red('e'), path, blkFile)

    def CollectorBlock(self, treeRoot, value):
        '''
        Gets a treeRoot of the edited file,
        creates an xml element list from matching
        machines from /etc/hosts and appends this element
        to the relevant parent.
        '''

        replaceBlkPath, functionIndex = re.split('\|', value, 1)[0], re.split('\|', value, 1)[1]
        path, Path = self.GetBlockPath(replaceBlkPath)

        searchPath = self.SetSearchString(Path)
        lastChild = Path[len(Path) - 1]

        ModInPathNodes = treeRoot.findall(searchPath + lastChild)
        if len(ModInPathNodes) > 1:
            self.logger.error('[%s] Found multiple targets, expected one, handling only the first...' % self.Ylw('w'))

        self.logger.debug('[%s] ForcedPush doesn\'t exist, defaulting to "False"' \
            % self.Blu('d'))

        parent = treeRoot.find(searchPath + lastChild)
        if parent == None:
            parent = treeRoot

        functionCall = self.Function[functionIndex]
        appendixRoot = functionCall.getroot()

        AppendixNodes = parent.findall(appendixRoot.tag)
        for appendixNode in AppendixNodes:
            Path.append(appendixNode.tag)
            self.logger.error('[%s] Removing an already existing block: %s' \
                % (self.Grn('i'), '.'.join(Path)))
            parent.remove(appendixNode)

        self.logger.error('[%s] Appending collector block "%s" to "%s"' \
            % (self.Grn('i'), appendixRoot.tag, '.'.join(Path)))

        parent.append(appendixRoot)
                    
    def Modification(self, treeRoot, role):
        '''
        Runs over the relevant tags in an xml tree and modifies their
        values according to the required methods
        (by value, by identifier, by name).
        Gets: (treeRoot) xml node, (role) string.
        Returns: N/A.
        '''

        methodName = 'Modification()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.logger.error('[%s] Starting modifications procedure, role %s...' % (self.Blu('*'), role))

        Mapper = self.MapXmlTree(treeRoot)

        if role == 'ModText':
            self.Modify = self.ModText
        elif role == 'ModAttr':
            self.Modify = self.ModAttr

        for key, value in self.Modify.iteritems():
            try:
                if role == 'ModAttr' and re.search('(.*})(:)(.*)', value):
                    path, newData = re.search('(.*})(:)(.*)', value).group(1), \
                                    re.search('(.*})(:)(.*)', value).group(3)
            except:
                pass

            if role != 'ModAttr':
                path, newData = value.split(':', 1)

            index, Index, Path = self.Matcher(path, role)

            searchPath = self.SetSearchString(Path)
            lastChild = Path[len(Path) - 1]
            InPathNodes = treeRoot.findall(searchPath + lastChild)
            
            if not InPathNodes:
                raise Exception, '[%s] Couldn\'t find the specified element "%s"' \
                % (self.Red('e'), '.'.join(Path))

            for node in InPathNodes:
                if (index.startswith('"') and index.endswith('"')) \
                or (index.startswith('\'') and index.endswith('\'')):
                    node = self.FilterByOldValue(node, Mapper, index, Path, lastChild)
                    self.logger.debug('[i] Modification by old value: %s["%s"]' \
                    % ('.'.join(Path), index.strip('"')))
                    if node != None:
                        node.text = newData
                        nodePath = self.ConstructPath(node, Mapper)
                        self.logger.error('[%s] Modified value of %s to %s' % (self.Grn('i'), nodePath, newData))
    
                elif Index:
                    if role == 'ModAttr':
                        try:
                            origStart = re.search('(^http://)(.*)(:.*$)', node.attrib.get(Index[0])).group(1)
                            origEnd = re.search('(^http://)(.*)(:.*$)', node.attrib.get(Index[0])).group(3)
                            newStart = re.search('(^http://)(.*)(:.*$)', Index[1]).group(1)
                            newEnd = re.search('(^http://)(.*)(:.*$)', Index[1]).group(3)
     
                            if origStart == newStart and origEnd == newEnd:
                                node.set(Index[0], newData)
                                self.logger.debug('[%s] Modification by node attribute: %s="%s" in %s' \
                                % (self.Blu('i'), Index[0], Index[1], '.'.join(Path)))
                                self.logger.error('[%s] Modified value of atribute "%s" to "%s"' \
                                % (self.Grn('i'), Index[0], newData))
                            elif origStart != newStart or origEnd != newEnd:
                                raise Exception, \
                                '[%s] Couldn\'t find a node %s with attribute %s="%s ... %s" please check the config file' \
                                % (self.Red('e'), '.'.join(Path), Index[0], newStart, newEnd)
                        except AttributeError:
                            pass 

                    elif role != 'ModAttr':
                        node = self.FilterByNodeIdent(node, Mapper, Index, Path)
                        self.logger.debug('[i] Modification by node identifier: %s="%s" in %s' \
                        % (Index[0], Index[1], '.'.join(Path[:-1])))
                        if node != None:
                            node.text = newData
                            self.logger.error('[%s] Modified value of %s to %s' % (self.Grn('i'), '.'.join(Path), newData))
                        
                elif newData:
                    if role == 'ModAttr' and node.attrib.get(index):
                        self.logger.debug('[%s] Modification by attribute name: %s' % (self.Blu('i'), index))
                        node.set(index, newData)
                        self.logger.error('[%s] Modified value of attribute %s to %s' % (self.Grn('i'), index, newData))
                    elif role == 'ModAttr' and not node.attrib.get(index):
                        raise Exception, '[%s] Couldn\'t find a node %s with attribute %s' % (self.Red('e'), '.'.join(Path), index)
                    elif role != 'ModAttr':
                        self.logger.debug('[%s] Modification by node name: %s' % (self.Blu('i'), '.'.join(Path)))
                        node = self.FilterByNodeName(node, Mapper, Path, lastChild)
                        if node != None:
                            node.text = newData
                            self.logger.error('[%s] Modified value of %s to %s' \
                            % (self.Grn('i'), '.'.join(Path), newData))
                else:
                    raise Exception, 'Unable to modify the element %s, %s' % (key, value)

    def Deletion(self, treeRoot, role):
        '''
        Runs over the relevant tags in an xml tree and deletes them
        according to the required methods (by identifier, by name).
        Gets: (treeRoot) xml node, (role) string.
        Returns: N/A.
        '''

        methodName = 'Deletion()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.logger.error('[%s] Starting deletion procedure...' % self.Blu('*'))

        Mapper = self.MapXmlTree(treeRoot)

        for key, value in self.Delete.iteritems():
            count = 0
            path = value.split(':', 1)
            if type(path) == list:
                path = path[0]

            index, Index, Path = self.Matcher(path, role)

            searchPath = self.SetSearchString(Path)
            lastChild = Path[len(Path) - 1]
            InPathNodes = treeRoot.findall(searchPath + lastChild)

            if not InPathNodes:
                self.logger.error('[%s] Couldn\'t find the specified element "%s"' \
                % (self.Ylw('w'), '.'.join(Path)))
                continue

            for node in InPathNodes:
                if (index.startswith('"') and index.endswith('"')) \
                or (index.startswith('\'') and index.endswith('\'')):
                    node = self.FilterByOldValue(node, Mapper, index, Path, lastChild)
                    self.logger.error('[i] Del. by old value: %s["%s"]' \
                    % ('.'.join(Path), index.strip('"')))
                    if node != None:
                        nodePath = self.ConstructPath(Mapper[node], Mapper)
                        parent = Mapper[Mapper[node]]
                        parent.remove(Mapper[node])
                        self.logger.error('[%s] Deleted tag %s' % (self.Grn('i'), nodePath))

                elif Index:
                    if index == 'parent':
                        node = self.FilterByNodeIdent(node.find(Index[0]), Mapper, Index, Path)
                    else:    
                        node = self.FilterByNodeIdent(node, Mapper, Index, Path)
                        self.logger.debug('[i] Del. by node ident: %s="%s", checking in %s' \
                        % (Index[0], Index[1], '.'.join(Path[:-1])))

                    if node != None:
                        if index == 'parent':
                            nodePath = self.ConstructPath(Mapper[node], Mapper)
                            parent = Mapper[node]
                            Mapper[parent].remove(parent)
                            self.logger.error('[%s] Deleted parent %s by index %s' % (self.Grn('i'), nodePath, Index))
                        else:
                            nodePath = self.ConstructPath(node, Mapper)
                            parent = Mapper[node]
                            parent.remove(node)
                            self.logger.error('[%s] Deleted child %s by index %s' % (self.Grn('i'), nodePath, Index))
                    else:
                        count += 1

                    if count == len(InPathNodes):
                        self.logger.error('[%s] Couldn\'t find %s in %s[%s="%s"], skipping...' \
                        % (self.Ylw('w'), lastChild, '.'.join(Path[:-1]), Index[0], Index[1]))

                elif Path:
                    nodes = self.FilterByNodeName(node, Mapper, Path, lastChild)
                    self.logger.debug('[i] Del. by node name: %s' % '.'.join(Path))
                    if node != None:
                        nodePath = self.ConstructPath(node, Mapper)
                        parent = Mapper[node]
                        parent.remove(node)
                        self.logger.error('[%s] Deleted tag %s' % (self.Grn('i'), nodePath))
                else:
                    raise Exception, 'Unable to delete the element %s, %s' % (key, value)

    def Appendix(self, treeRoot, role):
        '''
        Appends tags to relevant parent in an xml tree,
        according to required methods (by value, by identifier, by name).
        Gets: (treeRoot) xml node, (role) string.
        Returns: N/A.
        '''

        methodName = 'Appendix()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.logger.error('[%s] Starting appendix procedure "%s" role...' % (self.Blu('*'), role))

        if len(self.Block) <= 0:
            Mapper = self.MapXmlTree(treeRoot)
    
            if role == 'Tag':
                AppendixDict = self.AppendTag
            elif role == 'Block':
                AppendixDict = self.AppendBlock
    
            for key, value in AppendixDict.iteritems():
                try:
                    re.search('(.*)(\|)(.*)', value).group()
                    self.CollectorBlock(treeRoot, value)
                    continue
                except:
                    try:
                        re.search('(.*)(\:)(.*)', value).group()
                    except AttributeError:
                        self.Replacement(treeRoot, value)
                        continue

                path = value.split(':', 1)
                if type(path) == list:
                    if len(path) > 1:
                        value = path[1]
                    else:
                        value = ''
                    path = path[0]
    
                Index, Path = self.Matcher(path, role)
    
                if role == 'Tag':
                    searchPath = self.SetSearchString(Path[:-1])
                    lastChild = Path[len(Path[:-1]) - 1]
                    appendix = Path[len(Path) - 1]
                elif role == 'Block':
                    searchPath = self.SetSearchString(Path)
                    lastChild = Path[len(Path) - 1]
                    appendix = value
    
                if len(Path) == 1:
                    appendTree = eparse(value)
                    appendRoot = appendTree.getroot()
                    if not self.Exists(treeRoot, appendRoot.tag, Index, 'name'):
                        treeRoot.append(appendRoot)
                        nodePath = self.ConstructPath(treeRoot, Mapper)
                        self.logger.error('[%s] Appended block "%s"' \
                        % (self.Grn('i'), nodePath + '.' + appendRoot.tag))
                    else:
                        self.logger.error('[%s] Couldn\'t append block "%s" from %s - already exists in %s' \
                        % (self.Ylw('w'), appendRoot.tag, appendix, '.'.join(Path)))
                    continue
    
                InPathNodes = treeRoot.findall(searchPath + lastChild)
    
                if not InPathNodes:
                    raise Exception, '[%s] Couldn\'t find the specified element "%s"' \
                    % (self.Red('e'), '.'.join(Path))
    
                for node in InPathNodes:
                    if Index and role == 'Tag':
                        self.logger.debug('[%s] Append by node ident, looking for: %s="%s" in %s' \
                        % (self.Blu('i'), Index[0], Index[1], '.'.join(Path[:-1])))
                        node = self.FilterByNodeIdent(node.find(Index[0]), Mapper, Index, Path)
                        if node != None:
                            if not self.Exists(Mapper[node], appendix, Index, 'name'):
                                appendixNode = Element(appendix)
                                appendixNode.text = value
                                parent = Mapper[node]
                                parent.append(appendixNode)
                                Mapper[appendixNode] = parent
                                nodePath = self.ConstructPath(appendixNode, Mapper)
                                self.logger.error('[%s] Appended tag "%s"' % (self.Grn('i'), nodePath))
                            else:
                                self.logger.error('[%s] Couldn\'t append tag "%s" - already exists in %s' \
                                % (self.Ylw('w'), appendix, '.'.join(Path[:-1])))
    
                    elif Index and role == 'Block':
                        self.logger.debug('[%s] Append block by node ident, looking for: %s="%s" in %s' \
                        % (self.Blu('i'), Index[0], Index[1], '.'.join(Path)))
                        node = self.FilterByNodeIdent(node.find(Index[0]), Mapper, Index, Path)
                        if node != None:
                            appendTree = eparse(value)
                            appendRoot = appendTree.getroot()
                            if not self.Exists(Mapper[node], appendRoot.tag, Index, 'name'):
                                parent = Mapper[node]
                                parent.append(appendRoot)
                                nodePath = self.ConstructPath(parent, Mapper)
                                self.logger.error('[%s] Appended block "%s"' \
                                % (self.Grn('i'), nodePath + '.' + appendRoot.tag))
                            elif self.Exists(Mapper[node], appendRoot.tag, Index, 'name') \
                            and not self.Same(Mapper[node].find(appendRoot.tag), appendRoot):
                                parent = Mapper[node]
                                parent.append(appendRoot)
                                nodePath = self.ConstructPath(parent, Mapper)
                                self.logger.error('[%s] Appended block "%s"' \
                                % (self.Grn('i'), nodePath + '.' + appendRoot.tag))
                            elif self.Exists(Mapper[node], appendRoot.tag, Index, 'name') \
                            and self.Same(Mapper[node].find(appendRoot.tag), appendRoot):
                                self.logger.error('[%s] Couldn\'t append block "%s" from %s - already exists in %s' \
                                % (self.Ylw('w'), appendRoot.tag, appendix, '.'.join(Path)))
    
                    elif not Index and role == 'Tag':
                        self.logger.debug('[%s] Append by node name, looking for: %s' \
                        % (self.Blu('i'), '.'.join(Path[:-1])))
                        node = self.FilterByNodeName(node, Mapper, Path, Path[len(Path[:-1]) - 1])
                        if node != None:
                            if not self.Exists(node, appendix, Index, 'name'):
                                appendixNode = Element(appendix)
                                appendixNode.text = value
                                node.append(appendixNode)
                                Mapper[appendixNode] = node
                                nodePath = self.ConstructPath(appendixNode, Mapper)
                                self.logger.error('[%s] Appended tag %s' % (self.Grn('i'), nodePath))
                            else:
                                self.logger.error('[%s] Couldn\'t append tag %s - already exists in %s' \
                                % (self.Ylw('w'), appendix, '.'.join(Path[:-1])))
    
                    elif not Index and role == 'Block':
                        self.logger.debug('[%s] Append block by node name, looking for: %s' \
                        % (self.Blu('i'), '.'.join(Path)))
                        node = self.FilterByNodeName(node, Mapper, Path, lastChild)
                        if node != None:
                            appendTree = eparse(value)
                            appendRoot = appendTree.getroot()
                            if not self.Exists(node, appendRoot.tag, Index, 'name'):
                                node.append(appendRoot)
                                nodePath = self.ConstructPath(node, Mapper)
                                self.logger.error('[%s] Appended block %s' % (self.Grn('i'), nodePath + '.' + appendRoot.tag))
                            elif self.Exists(node, appendRoot.tag, Index, 'name') \
                            and not self.Same(node.find(appendRoot.tag), appendRoot):
                                node.remove(node.find(appendRoot.tag))
                                node.append(appendRoot)
                                nodePath = self.ConstructPath(node, Mapper)
                                self.logger.error('[%s] Appended block %s' % (self.Grn('i'), nodePath + '.' + appendRoot.tag))
                            elif self.Exists(node, appendRoot.tag, Index, 'name') \
                            and self.Same(node.find(appendRoot.tag), appendRoot):
                                self.logger.error('[%s] Couldn\'t append block "%s" from %s - already exists in %s' \
                                % (self.Ylw('w'), appendRoot.tag, appendix, '.'.join(Path)))
                    else:
                        raise Exception, '[%s] Unable to append %s' % (self.Red('e'), value)
                
    def GetBlockPath(self, path):
        Path = re.split('\.', path)
        return path, Path

    def Cloning(self, treeRoot, role):
        '''
        Clones tags in the xml tree, according to required methods
        (by value, by identifier, by name).
        Gets: (treeRoot) xml node, (role) string.
        Returns: N/A.
        '''

        methodName = 'Cloning()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.logger.error('[%s] Starting cloning procedure' % self.Blu('*'))

        Mapper = self.MapXmlTree(treeRoot)

        for key, value in self.Clone.iteritems():
            path = value.split(':', 1)
            if type(path) == list and len(path) > 1 and len(path[1].split(',')) > 1:
                NewValues = path[1].split(',')
            elif type(path) == list and len(path) > 1 and len(path[1].split(',')) == 1:
                newValue = path[1]
            else:
                self.logger.error('Wrong configuration detected...')
                exit(911)
            path = path[0]

            elemType, Index, Path = self.Matcher(path, role)

            if elemType == 'Parent':
                searchPath = self.SetSearchString(Path)
                lastChild = Path[len(Path) - 1]
                skipInPathNodes = False
            elif elemType == 'Child':
                searchPath = self.SetSearchString(Path[:-1])
                lastChild = Path[len(Path[:-1]) - 1]
                cloneTarget = Path[len(Path) - 1]
            elif elemType == 'MultipleChildren':
                searchPath = self.SetSearchString(Path)
                lastChild = Path[len(Path) - 1]
                CloneTargets = {}
                i = 0
                try:
                    while i < len(Index):
                        CloneTargets[Index[i]] = NewValues[i]
                        i += 1
                except IndexError:
                    raise Exception, '[%s] Not enough new values given for cloning, exiting...\n' % self.Red('e')
                Missing = []
                Present = {}
                clonedAtLeastOne = False
                skipInPathNodes = False

            InPathNodes = treeRoot.findall(searchPath + lastChild)

            if elemType == 'MultipleChildren':
                if skipInPathNodes == False:
                    if not InPathNodes:
                        raise Exception, '[%s] Couldn\'t find the specified element "%s"' % (self.Red('e'), '.'.join(Path))

            for node in InPathNodes:
                if Index and elemType != 'MultipleChildren':
                    self.logger.debug('[i] Clone by node ident, looking for: %s="%s" in %s' \
                    % (Index[0], Index[1], '.'.join(Path[:-1])))

                    if elemType == 'Parent':
                        if self.MultElemExistCheck(InPathNodes, {Index:newValue}, Mapper):
                            skipInPathNodes = True
                            continue

                    else:
                        if self.MultElemExistCheck(Mapper[node], {Index:newValue}, Mapper):
                            self.logger.error('[%s] Element %s already exists in another %s, skipping'\
                            % (self.Ylw('w'), Index, Mapper[node].tag))
                            skipInPathNodes = True
                            continue

                    node = self.FilterByNodeIdent(node.find(Index[0]), Mapper, Index, Path)

                    if node != None and elemType == 'Parent':
                        self.logger.debug('Checking for element existence: %s, in "%s"'
                        % (Index, Mapper[node].tag))
                        
                        if self.MultElemExistCheck(Mapper[node], {Index:newValue}, Mapper):
                            self.logger.error('[%s] Element %s already exists in another %s, skipping'\
                            % (self.Ylw('w'), Index, Mapper[node].tag))
                            skipInPathNodes = True
                            continue

                        parent = Mapper[node]
                        appendixNode = Element(parent.tag)
                        for child in parent:
                            clonedChild = Element(child.tag)
                            if child.tag == Index[0] and child.text == Index[1]:
                                clonedChild.text = newValue
                            else:
                                clonedChild.text = child.text
                            appendixNode.append(clonedChild)
                        Mapper[parent].append(appendixNode)
                        Mapper[appendixNode] = Mapper[parent]
                        nodePath = self.ConstructPath(parent, Mapper)
                        self.logger.error('[%s] Cloned parent "%s" with new value "%s" for child "%s"' \
                        % (self.Grn('i'), nodePath, newValue, Index[0]))

                    elif node != None and elemType == 'Child' \
                    and not self.Exists(Mapper[node], node.tag, (Index[0],newValue), 'ident'):
                        parent = Mapper[node]
                        appendixNode = Element(cloneTarget)
                        appendixNode.text = newValue
                        parent.append(appendixNode)
                        Mapper[appendixNode] = parent
                        nodePath = self.ConstructPath(appendixNode, Mapper)
                        self.logger.error('[%s] Cloned child "%s" with new value "%s"' \
                        % (self.Grn('i'), nodePath, newValue))
                    elif node != None and elemType == 'Child' \
                    and self.Exists(Mapper[node], node.tag, (Index[0],newValue), 'ident'):
                        self.logger.error('[%s] Element (\'%s\', \'%s\') already exists in %s, skipping'\
                        % (self.Ylw('w'), Index[0], newValue, Mapper[node].tag))

                elif CloneTargets.keys() and elemType == 'MultipleChildren':
                    inPathNode = node
                    AppendixMapper = {}

                    for ct in CloneTargets.keys():
                        node = self.FilterByNodeIdent(inPathNode.find(ct[0]), \
                        Mapper, ct, Path)
                        if node == None:
                            Missing.append(inPathNode)

                    if inPathNode in Missing:
                        continue

                    node = self.FilterByNodeIdent(inPathNode.find(CloneTargets.keys()[0][0]), \
                    Mapper, CloneTargets.keys()[0], Path)

                    if self.MultElemExistCheck(InPathNodes, CloneTargets, Mapper):
                        self.logger.error('[%s] Elements %s already exists in another %s, skipping'\
                        % (self.Ylw('w'), CloneTargets, Mapper[node].tag))
                        continue

                    if node == None:
                        continue

                    parent = Mapper[node]
                    self.parent = parent
                    self.Mapper = Mapper
                    appendixNode = Element(parent.tag)
                    firstRun = True
                    for Tuple in CloneTargets.keys():
                        node = self.FilterByNodeIdent(inPathNode.find(Tuple[0]), \
                        self.Mapper, Tuple, Path)
                        if node != None:
                            self.parent = self.Mapper[node]
                            if firstRun:
                                for child in self.parent:
                                    clonedChild = Element(child.tag)
                                    if (child.tag == Tuple[0] and child.text == Tuple[1]):
                                        clonedChild.text = CloneTargets[Tuple]
                                    else:
                                        clonedChild.text = child.text
                                    if not self.Exists(appendixNode, clonedChild.tag, Tuple, 'name'):
                                        appendixNode.append(clonedChild)
                                        AppendixMapper[clonedChild] = appendixNode
                            else:
                                self.parent.find(Tuple[0]).text = CloneTargets[Tuple]
                        inPathNode = appendixNode
                        self.Mapper = AppendixMapper
                        firstRun = False
                    Mapper[parent].append(appendixNode)
                    Mapper[appendixNode] = Mapper[parent]
                    nodePath = self.ConstructPath(parent, Mapper)
                    newValues, elements = '', ''
                    for cloneTarget in CloneTargets.keys():
                        newValues = newValues + CloneTargets[cloneTarget] + ', '
                        elements = elements + cloneTarget[0] + ', '
                    newValues = newValues.rstrip(', ')
                    elements = elements.rstrip(', ')
                    clonedAtLeastOne = True
                    self.logger.error('[%s] Cloned "%s", "%s". New values: %s' \
                    % (self.Grn('i'), nodePath, CloneTargets.keys(), newValues))

            if elemType == 'MultipleChildren':
                if len(Missing) != 0 and clonedAtLeastOne == False and skipInPathNodes == True:
                    raise Exception, '[%s] Couldn\'t find the combination "%s"' % (self.Red('e'), CloneTargets.keys())
            elif elemType == 'Parent' and skipInPathNodes == True:
                self.logger.error('[%s] Element (\'%s\', \'%s\') already exists in another %s, skipping'\
                % (self.Ylw('w'), Index[0], newValue, node.tag))


    def GetValues(self, hash):
        '''
        Creates a dictionary with type:value pairs from the config file strings.
        The values converted from their variable names to data.
        Ex. If Text_1 holds the data "SomeData", then
            p.p.p.c:Text_1 -> p.p.p.c:SomeData
        Gets: (hash) dictionary with all configuration strings.
        Returns: (hash) dictionary with all configuration strings.
        '''

        methodName = 'GetValues()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        for k, v in hash.iteritems():
            try:
                if '="http://' in hash[k] or '="https://' in hash[k]:
                    path, info = v.rsplit(':', 1)
                else:
                    path, info = v.split(':', 1)
            except:
                continue

            info = info.split(',')

            if len(info) < 2:
                info = info[0]

                if info.startswith('Text_'):
                    hash[k] = path + ':' + self.Text[info]
                elif info.startswith('Snmp_'):
                    try:
                        re.search('^[a-zA-Z0-9_]+\(.*\)$', self.Snmp[info]).group()
                        try:
                            hash[k] = path + ':' + eval(self.Snmp[info])
                        except:
                            self.logger.error(traceback.format_exc())
                            raise Exception, 'Failed to get values for %s' % hash
                    except AttributeError:
                        hash[k] = path + ':' + self.Snmp[info]
                elif info.startswith('DigHostIP_'):
                    hash[k] = path + ':' + DigHostsIP(reg=self.DigHostIP[info])[0]
                elif info.startswith('BlockFile_'):
                    hash[k] = path + ':' + self.BlockFile[info]
                elif info.startswith('Function_'):
                    hash[k] = path + ':' + self.Function[info]
                else:
                    raise Exception, 'Failed to get values for %s' % hash
            else:
                Info = info
                hash[k] = path + ':'
                for info in Info:
                    if info.startswith('Text_'):
                        hash[k] =  hash[k] + self.Text[info] + ','
                hash[k] = hash[k].rstrip(',')

        return hash

    def SetSearchString(self, Path):
        '''
        Creates a search string up to a level above the target node.
        Gets: (Path) split path to the last element, as list.
        Returns: (searchPath) search path as string.
        '''

        methodName = 'SetSearchString()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        self.Path = Path[1:]
        i, searchPath = 0, ''
        while i < len(self.Path) - 1:
            searchPath = searchPath + self.Path[i] + '/'
            searchPath = searchPath.lstrip('/')
            i += 1

        return searchPath

    def Matcher(self, path, role):
        '''
        Creates relevant lists, strings and paths accrording to the
        required role.
        Gets: (path) dotted path as string, (role) which role called the function, as string.
        Returns: Dependant on the role, (index) current value of a node, as string,
                 (Index) name and value of the identifier node, as list,
                 (Path) split path as list.
        '''

        methodName = 'Matcher()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        if re.search('(.*)\[(.*)\]\.(.*)', path):
            if role == 'Cloning':
                index = 'Child'
            else:
                index = ''
            Index = re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]\.(.*)', path).group(2)).group(1), \
                    re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]\.(.*)', path).group(2)).group(2)
            Path = re.split('\.', re.search('(.*)\[(.*)\]\.(.*)', path).group(1) + '.' + \
                                  re.search('(.*)\[(.*)\]\.(.*)', path).group(3))
        elif re.search('(.*)\[(.*)\]', path):
            index = re.search('(.*)\[(.*)\]', path).group(2)
            if role == 'Block' or role == 'Cloning':
                CloneChildren = re.search('(.*)\[(.*)\]', path).group(2).split(',')
                if role == 'Cloning' and len(CloneChildren) > 1:
                    index = 'MultipleChildren'
                    Index = []
                    for cloneChild in CloneChildren:
                        Index.append((re.search('(.*)\="(.*)"', cloneChild).group(1), \
                                     re.search('(.*)\="(.*)"', cloneChild).group(2)))
                if role == 'Block' or (role == 'Cloning' and len(CloneChildren) == 1):
                    Index = re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]', path).group(2)).group(1), \
                            re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]', path).group(2)).group(2)
                if role == 'Cloning' and len(CloneChildren) == 1:
                    index = 'Parent'
            elif role == 'Deletion':
                Index = re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]', path).group(2)).group(1), \
                        re.search('(.*)\="(.*)"', re.search('(.*)\[(.*)\]', path).group(2)).group(2)
                index = 'parent'
            else:
                Index = ''
            Path = re.split('\.', re.search('(.*)\[(.*)\]', path).group(1))

        elif re.search('(.*){(.*)}', path):
            try:
                index = ''
                Index = re.search('(.*)\="(.*)"', re.search('(.*){(.*)}', path).group(2)).group(1), \
                        re.search('(.*)\="(.*)"', re.search('(.*){(.*)}', path).group(2)).group(2)
            except:
                    Index = ''
                    index = re.search('(.*){(.*)}', path).group(2)
            Path = re.split('\.', re.search('(.*){(.*)}', path).group(1))

        else:
            index = ''
            Index = ''
            Path = re.split('\.', re.search('(.*)', path).group(1))

        if role == 'Deletion' or role == 'ModText' or role == 'ModAttr' or role == 'Cloning':
            return index, Index, Path
        elif role == 'Tag' or role == 'Block':
            return Index, Path

    def FilterByOldValue(self, node, Mapper, index, Path, lastChild):
        '''
        Creates a list of nodes found in the XML tree, by their name and current value.
        Gets: (node) xml node, (Mapper) child:parent dictionary,
              (index) target child node's current value as string,
              (Path) split path as list, (lastChild) name of the last child
              in the path, as string.
        Returns: (Nodes) list of xml nodes.
        '''

        methodName = 'FilterByOldValue()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        if node.text == index.strip('"'):
            return node
        else:
            return None

    def FilterByNodeIdent(self, node, Mapper, Index, Path):
        '''
        Finds an xml node from an XML tree, by it's brother's name and value.
        Gets: (node) xml node, (Mapper) child:parent dictionary,
              (Index) identifier node's name and value as tuple,
              (Path) split path as list.
        Returns: Either (node) xml node or None.
        '''

        methodName = 'FilterByNodeIdent()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        try:
            identNode = Mapper[node].find(Index[0])
        except KeyError:
            return None

        if identNode.text == Index[1]:
            return node
        else:
            return None

    def FilterByNodeName(self, node, Mapper, Path, element):
        '''
        Makes sure a given node is named as the reference element.
        Gets: (node) xml node, (Mapper) child:parent dictionary,
              (Path) split path as list, (element) name of the last child
              in the path, as string.
        Returns: (Nodes) list of xml nodes.
        '''

        methodName = 'FilterByNodeName()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        if node.tag == element:
            return node
        else:
            return None
    
    def ConstructPath(self, node, Mapper):
        '''
        Constructs a path from the root element to a given node.
        Gets: (node) xml node, (Mapper) child:parent dictionary.
        Returns: (nodePath) string of the node's path.
        '''

        methodName = 'ConstructPath()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))
    
        self.node = node
        NodePath = []
        i = 0

        try:
            while Mapper[self.node]:
                NodePath.append(self.node.tag)
                self.node = Mapper[self.node]
                i += 1
        except:
            NodePath.append(self.node.tag)
            NodePath.reverse()
            nodePath = '.'.join(NodePath)

            return nodePath

    def Exists(self, parent, appendix, Index, checkType):
        '''
        Checks for element existence (appendix) in the parent element.
        [*] The 'ident' check type is supported only for tags, not blocks.
        Gets: (parent) xml node, (appendix) name of the node to check as string,
              (checkType) check type, as string.
              (Index) values of the identifier node as tuple,
              (dataType) either "Block" or "Tag" as string.
        Returns: True or False.
        '''
        
        methodName = 'Exists()'
        self.logger.debug('[d] Accessing %s.%s' % (self.className, methodName))

        if len(parent.findall(appendix)) > 1:
            Children = parent.findall(appendix)
            for child in Children:
                if checkType == 'ident' and child.tag == appendix \
                and child.text == Index[1]:
                    return True
                elif checkType == 'name':
                    return True
        elif parent.find(appendix) != None:
            if checkType == 'ident' and parent.find(Index[0]).tag == appendix \
            and parent.find(Index[0]).text == Index[1]:
                return True
            elif checkType == 'name':
                return True
        else:
            return False

    def ReformatXmlTree(self, elem, level=0):
        '''
        Reformating the XML for human consumption.
        Gets: (elem) root element as xml node,
              (level) starting identation level.
        Returns: N/A
        '''

        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.ReformatXmlTree(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

    def MultElemExistCheck(self, Parents, Children, Mapper):
        '''
        Checks if multiple children exist in a parent element.
        Gets: (parent) xml node, (Children) dictionary of children
              and values.
        Returns: True or False.
        '''

        count = 0
        Present = {}

        if type(Parents) != list and type(Parents) != dict:
            Parents = [Parents]

        for parent in Parents:
            count = 0
            for key in Children.keys():
                try:
                    if parent.find(key[0]).tag == key[0] and parent.find(key[0]).text == Children[key]:
                        count += 1
                except:
                    pass

        if count == len(Children):
            return True
        else:
            return False

    def Red(self, text):
        return "\033[31m%s\033[0m" % (text)
    def Grn(self, text):
        return "\033[32m%s\033[0m" % (text)
    def Ylw(self, text):
        return "\033[33m%s\033[0m" % (text)
    def Blu(self, text):
        return "\033[34m%s\033[0m" % (text)

    def Same(self, first, second):
        '''
        Check if two xml parents are the same.
        Gets: (first) xml node, (second) xml node.
        Returns: True if the two are equal, False
                 if the two are different.
        '''

        state = True
        FirstChildren, FirstValues, SecondChildren, SecondValues = [], [], [], []

        FirstRootMapper = dict( [ (child, parent) \
                          for parent in first.getiterator() \
                          for child in parent ] )
        SecondRootMapper = dict( [ (child, parent) \
                          for parent in second.getiterator() \
                          for child in parent ] )

        if len(FirstRootMapper) != len(SecondRootMapper):
            state = False

        for fKey in FirstRootMapper.keys():
            FirstChildren.append(fKey.tag)
        for sKey in SecondRootMapper.keys():
            SecondChildren.append(sKey.tag)

        for fKey in FirstRootMapper.keys():
            try:
                if re.search('^[0-9a-zA-Z .]', fKey.text).group():
                    FirstValues.append(fKey.text)
            except AttributeError:
                pass
        for sKey in SecondRootMapper.keys():
            try:
                if re.search('^[0-9a-zA-Z .]', sKey.text).group():
                    SecondValues.append(sKey.text)
            except AttributeError:
                pass

        for child in FirstChildren:
            if child not in SecondChildren:
                state = False
        for child in SecondChildren:
            if child not in FirstChildren:
                state = False
        for value in FirstValues:
            if value not in SecondValues:
                state = False
        for value in SecondValues:
            if value not in FirstValues:
                state = False

        return state

    def GetHeader(self, editFile):
        fh = open(editFile, 'r')
        line = fh.readline()
        fh.close()
        return line

    def AppendHeader(self, editFile, headerLine):
        fh = open(editFile, 'r')
        Lines = fh.readlines()
        fh.close()

        fh = open(editFile, 'w')
        if re.search('(<\?xml.*>\n)', headerLine):
            fh.write(headerLine)

        for line in Lines:
            fh.write(line)
        fh.close()

    def BuildConfigDict(self, config, pattern, name='BuildConfigDict function'):
        '''
        Prepares a dictionary from key/value pairs
        located in a given configuration file.
        Returns a dictionary.
        '''
    
        Configurations = {}
        for key, value in config.iteritems():
            if key.startswith(pattern):
                Configurations[key] = value
        return Configurations
def ReformatXmlTree(elem, level=0):
        '''
        Reformating the XML for human consumption.
        Gets: (elem) root element as xml node,
              (level) starting identation level.
        Returns: N/A
        '''

        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                ReformatXmlTree(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

def tree_xpath(root,xpath,attributes=None,text=None,delimiter='/',text_regex=False,tag_regex=False):
    '''
    Search for all childern under certain xpath.
    if tag_regex is True then the end of the xpath will be considered as regex and not a tag name.
    if text_regex is True then text is considered as regex.
    '''
    paths=[]
    if not xpath.startswith(delimiter):
        raise Exception('Invalid Xpath')
    xpath=xpath.split(delimiter,1)[1]
    def _tree_xpath(root,xpath):
        current_tag=xpath.split(delimiter,1)[0]
        if not current_tag == xpath:
            new_tag=(xpath.split(delimiter,1)[1]).split(delimiter)[0]
            new_xpath=xpath.split(delimiter,1)[1]
            for child in ((tag_regex == False or new_tag != new_xpath) and root.findall(new_tag)) or \
                    (tag_regex == True and __tree_xpath(List= root.getchildren(),regex=new_tag)) or [] :
                _tree_xpath(root=child,xpath=new_xpath)
        elif (( attributes is None ) or ( attributes == root.attrib  )) and (( text is None ) or \
                ((text_regex == False and text == root.text )or (text_regex == True and re.search(text,root.text )))):
            paths.append(root)
    def __tree_xpath(List,regex):
        '''
        Return a list of elements mathing to tag with regex removing None
        '''
        Elements=[]
        for E in List:
            if re.search(regex,E.tag):
                Elements.append(E)
        return Elements
    _tree_xpath(root=root,xpath=xpath)
    return paths

def get_parent(parent,elem):
    '''
    Scan an entire tree looking for the element if found it will be returned
    '''
    for E in parent.getchildren():
        if E == elem:
            return parent
    R=None
    for child in  parent.getchildren():
          R=R or get_parent(parent=child,elem=elem)
    return R

