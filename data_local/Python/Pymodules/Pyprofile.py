
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   Ver: 5.5.5                       #
#   Date: 26/08/10                   #
#   ModuleName: Pyprofile.py         #
######################################


from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys
from pdb import set_trace as st
import string
from re import search
from copy import deepcopy
from elementtree.ElementTree import ElementTree, dump, parse as eparse
from elementtree.ElementTree import Element

class profile(builder):
    def __init__(self, config, loggerName='', *args, **kwargs):
        super(profile, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        self.xmlHeader = '<?xml version="1.0" encoding="UTF-8" ?>'
    def __call__(self, editFiles):
        for file in editFiles:
            self.currentFile = file
            self.parseFile(file)
    def parseFile(self, file):
        try:
            self.logger.error('#### Start parsing the "%s" file.####\n' % file)
            self.tree = eparse(file)
            self.treeRoot = self.tree.getroot()
        except:
            raise Exception, 'Couln\'t parse the "%s" file.' % file
        self.startID = 0
        self.getUniqueCos()
        self.setStartID()
        self.synCosToProfileId()

        splitPath = (self.config['ProfilePath']).split('/')
        if os.path.basename(self.currentFile).startswith('conf.Gw'):
            basePath = splitPath[0] + '/' + splitPath[1]
        elif os.path.basename(self.currentFile).startswith('conf.sm'):
            basePath = splitPath[0]
        elem = self.treeRoot.find(basePath)

        if elem != None:
            self.createNewProfiles(elem)
            self.setStates()
            self.Formatter(elem = self.treeRoot)
            self.Writer(self.tree)
            self.logger.error('')
            self.logger.error('#### Finish to parse the "%s" file. ####\n' % file)
        else:
            raise Exception, 'Element "%s" not found.' % basePath

    def getUniqueCos(self):
        self.UniqueCos = []
        if os.path.basename(self.currentFile).startswith('conf.Gw'):
            self.events = self.config.get('gw_events', False)
        elif os.path.basename(self.currentFile).startswith('conf.sm'):
            self.events = self.config.get('sm_events', False)
        if self.events:
            for elem in self.events:
                for key, val in elem.iteritems():
                    if key == 'cos_id':
                        if not val in self.UniqueCos:
                            self.UniqueCos.append(val)
        self.logger.debug('Unique coses are %s' % str(self.UniqueCos))
    def setStartID(self):
        IDs = []
        self.Profiles = self.treeRoot.findall(self.config['ProfilePath'])
        if len(self.Profiles) > 0:
            for p in self.Profiles:
                for c in p._children:
                    if c.tag == 'Id' or c.tag == 'ProfileId':
                        IDs.append(int(c.text))
            IDs.sort()
            self.startID = IDs[-1] + 1
            self.logger.debug('The start ID number is %s' % self.startID)

    def synCosToProfileId(self):
        self.CosToProfile = {}
        self.NewCosIds = []
        for p in self.Profiles:
            for c in p._children:
                if c.tag == 'CoSId':
                    if c.text in self.UniqueCos:
                        if os.path.basename(self.currentFile).startswith('conf.Gw'):
                            ID = p.find('Id')
                        elif os.path.basename(self.currentFile).startswith('conf.sm'):
                            ID = p.find('ProfileId')
                        if ID != None:
                            self.CosToProfile[int(ID.text)] = c.text
                            self.UniqueCos.remove(c.text)

        for cos in self.UniqueCos:
            self.CosToProfile[self.startID] = cos
            self.NewCosIds.append(self.startID)
            self.startID += 1
        self.logger.debug('Profile ID to Cos ID dict are %s' % self.CosToProfile)

    def createNewProfiles(self, baseElem):
        for i in range(0, len(self.UniqueCos)):
            self.logger.info('New Default Profile element was created.')
            newElem = Element('DefaultProfile')
            for key, val in self.config['ProfileTags'].iteritems():
                e = Element(key)
                if e.tag == 'Id' or e.tag == 'ProfileId':
                    self.logger.info('The id is %s' % str(self.NewCosIds[i]))
                    e.text = str(self.NewCosIds[i])
                elif e.tag == 'CoSId':
                    self.logger.info('The CoSId is %s' % str(self.UniqueCos[i]))
                    e.text = self.UniqueCos[i]
                else:
                    e.text = val
                newElem._children.append(e)
            baseElem._children.append(newElem)

    def setStates(self):
        for state in self.events:
            for key, val in state.iteritems():
                if key == 'id':
                    elem = self.treeRoot.find(self.config['StatePath'] + '/' + val)
                    if elem != None:
                        subElements = elem.findall('Info')
                        if len(subElements) > 0:
                            for e in subElements:
                                pId = e.find('ProfileId')
                                if pId != None:
                                    id = self.getIdByCos(state['cos_id'])
                                    self.logger.info('The state %s value was set to profile ID: %s.' % \
                                            (val,str(id)))
                                    pId.text = str(id)
                    else:
            		raise Exception, 'Element "%s" not found.' % '%s/%s' % (self.config['StatePath'], val)

    def getIdByCos(self, cos):
        for k, v in self.CosToProfile.iteritems():
            if cos == v:
                return k
                
    def getHeader(self, file):
        try:
            fh = open(file, 'r')
            line = fh.readline()
            fh.close()
            if search('<\?xml\s*version', line):
                return line.strip()
            else:
                return self.xmlHeader
        except:
            raise Exception, 'Couln\'t open the "%s" file' % file

    def Formatter(self, elem, level=0):
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                self.Formatter(elem, level+1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i
    def Writer(self, tree, *args, **kwargs):
        tempFilePath = open(self.currentFile, 'w')
        tempFilePath.write('%s\n' % self.xmlHeader)
        tree.write(tempFilePath)
        tempFilePath.close()
