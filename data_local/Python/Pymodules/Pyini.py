
######################################
#   By: Netanel Malka                #
#   Mail: Netanel.Malka@comverse.com #
#   Ver: 5.5.5                       #
#   Date: 08/07/10                   #
#   ModuleName: Pyini.py             #
######################################


from Pyfiledit import builder
from Pydecorators import *
import os, time, re ,sys
from pdb import set_trace as st
from Pyconf import HashParser
import string

class Section:
    def __init__(self):
        self.first = False
        self.Line = {}
        self.counter = 0

    def setFirst(self):
        self.first = True

    def addLineToSection(self, newDict):
        #print str(self.counter) + "  " + str(newDict)
        self.Line[self.counter] = newDict
        self.counter += 1
        #self.logger

    def removeLineFromSection(self, sercheKey):
        counter=0
        for count, val in self.Line.iteritems():
            for lineType, line in val.iteritems():
                if lineType == sercheKey:
                    indexToDel = counter
            counter+=1
        del self.Line[indexToDel]

    def setNewValueForKey(self, sercheKey, newVal):
        for count, val in self.Line.iteritems():
            for lineType, line in val.iteritems():
                if lineType == sercheKey:
                    for key, value in line.iteritems():
                        if value == "":
                            line[key] = newVal
                        else:
                            line[key] = newVal + '\n'

    def checkSectionExist(self, sectionName):
        for count, val in self.Line.iteritems():
            for lineType, line in val.iteritems():
                for secName, value in line.iteritems():
                    if sectionName == secName:
                        return True    
    
    def checkKeyExist(self, sercheKey):
        for count, val in self.Line.iteritems():
            for lineType, line in val.iteritems():
                if sercheKey == lineType:
                    return True

               
    def getAllLines(self):
        lines = ""
        for count, val in self.Line.iteritems():
            for lineType, line in val.iteritems():
                for key, value in line.iteritems():
                    if lineType != 'Section' and lineType != 'Comment' and lineType != 'NewLine':
                        lines += key + value
                    else:
                        lines += value  
        return lines

class SectionManager:
    def __init__(self, logger, file):
        self.sections=[]
        self.logger = logger
        self.fileToEdit = file

    def addSection(self, section):
        self.sections.append(section)

    def getAllLines(self):
        allLines=""
        for section in self.sections:
            if (type(section)) != "<type 'classobj'>":
                allLines += section.getAllLines()

        return allLines

    def setValueBySectionAndKey(self, sectionToSetValue, sectionName, key, value):
        sectionToSetValue.setNewValueForKey(key, value )
        self.logger.error("In [%s] Section, The value of Key: --> %s was set to <%s>" % (sectionName, key, value))

    def addKeyValueLineToSection(self,sectionToAddLine, newDict):
        sectionToAddLine.addLineToSection(newDict)

    def removeKeyValueLineFromSection(self, sectionToRemoveKey, key):
        sectionToRemoveKey.removeLineFromSection(key)

    def sercheIfSectionExist(self, sectionName):
        for section in self.sections:
            if (type(section)) != "<type 'classobj'>":
                if section.checkSectionExist(sectionName) == True:
                    return section
        return None

    def sercheIfKeyExistInSection(self, sectionToSerche, sercheKey):
        if sectionToSerche.checkKeyExist(sercheKey) == True:
            return True
        return False
 
class conf_ini(builder, HashParser):
    def loadCurrentFile(self, SectionManager):
        newDict = {}
        sectionRegex = "[\s\t]*\[[\s\t]*(.*?)[\s\t]*\]"
        newLineRegex = "([\s\t]*\n)"
        keyValueRegex = "(([\s\t]*(.*?)[\s\t]*=)[\s\t]*)(.*[\s\t]*)"
        section = Section()
        section.setFirst()
        lines = self.linesRef
        self.logger.info("Start to read the %s file! " % self.fileToEdit)
        for current_line in lines:
            newDict = {}
            if re.match(self.config.get('CommentRegex', '^#'), current_line):
                newDict['Comment'] = {"" : current_line}
                section.addLineToSection(newDict)
            elif re.match(newLineRegex, current_line):
                newDict['NewLine'] = {"" : current_line}
                section.addLineToSection(newDict)
            elif re.match(sectionRegex, current_line):
                if section.first != True:
                    SectionManager.addSection(section)
                elif section.first == True:
                    SectionManager.addSection(section) 
                section = Section()
                newDict['Section'] = {re.match(sectionRegex, current_line).group(1) : current_line}
                self.logger.debug("New Section %s was added to Section Manager" % re.match(sectionRegex, current_line).group(1))
                self.logger.debug(newDict)
                section.addLineToSection(newDict)
            elif re.match(keyValueRegex, current_line):
                regObj = re.match(keyValueRegex, current_line)
                if regObj.group(1).endswith('=\n'):
                    newDict[regObj.group(3)] = {regObj.group(2) : '\n' }
                else:
                    newDict[regObj.group(3)] = {regObj.group(1) : regObj.group(4) }
                section.addLineToSection(newDict)
        SectionManager.addSection(section)

    def __init__(self, config, loggerName='', *args, **kwargs):
        super(conf_ini, self).__init__(config=config, loggerName=loggerName, *args, **kwargs)
        self.snmp = self.BuildDict(startwith='Snmp_',hash=self.config,hashFiles1={})
        self.snmp = self.GetValueFromFunctionToDict(hash=self.snmp,startwith='Snmp_')
        self.functions_and_text = self.BuildDict(startwith='Function_',hash=self.config,hashFiles1={})
        self.functions_and_text = self.BuildDict(startwith='Text_',hash=self.config,\
                                                hashFiles1=self.functions_and_text)
        self.functions_and_text = self.BuildDict(startwith='Snmp_',hash=self.config,\
                                  hashFiles1=self.functions_and_text)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text)
        self.functions_and_text = self.GetValueFromFunctionToDict(hash=self.functions_and_text,\
                                  startwith='Snmp_')

    def changeValue(self, fileName):
        filename = os.path.basename(fileName)
        actionsList = []
        counetr = 1
        iRules = self.config.get('iNiRules', False) or self.config['iRules'] 
        self.logger.info("Start parsing the actions for %s file! " % self.fileToEdit)
        self.logger.debug("The number of action from the %s file is --> %s" % (sys.argv[1], len(iRules)))
        self.logger.debug(iRules)
        self.logger.debug("The number of action from the fun_and_text file is --> %s" % (len(self.functions_and_text.keys())))
        for i in iRules:
            temp = i.split('=')
            temp[0] = temp[0].split('_')[0]
            if temp[0] == filename:
                temp[0] = temp[0] + '_'  + str(counetr)
                counetr += 1
                for k,v in self.functions_and_text.iteritems():
                    if temp[3] == k:
                        temp[3]= self.functions_and_text[k]
                        actionsList.append(temp)

        self.logger.debug("The list of action form func_and_text file %s as follow: " % filename)
        self.logger.debug(self.functions_and_text)
        self.logger.debug("The list of action for file %s as follow: " % filename)
        self.logger.debug(actionsList)
        self.logger.debug("The number of action for %s is --> %s" % (filename, len(actionsList)))
        return actionsList

    def buildActionDict(self, actionList):
        dic = {}
        for i in actionList:
            dic[i[0]] = {i[1]: {i[2]: i[3]}}
        return dic

    def appendLine(self, sectionInstance, sectionName, newDict, sectionMamager):
        if self.config['Append'].lower() != 'yes':
            key = newDict[sectionName].keys()[0].split('=')
            self.logger.error('Key: %s, Not exists under Section: [%s]' % (key[0], sectionName))
            #self.logger.error('Key: %s, Not exists under Section: [%s]' % (newDict[sectionName].keys()[0], sectionName))
            raise Exception, 'Value of Append Mode is => %s in the %s file!' % (str(self.config['Append']).upper(),os.path.basename(self.fileToEdit))
        else:
            self.logger.error('The %s=%s line will be append under %s section in the %s file!' \
            % (newDict[sectionName].keys()[0], newDict[sectionName].values()[0], sectionName, self.fileToEdit))
            sectionMamager.addKeyValueLineToSection(sectionInstance, newDict)

    def deleteLine(self, sectionToSerche, sectionName, key, value, sectionMamager):
            if self.config['Delete'].lower() != 'yes':
                self.logger.error("Value of Delete Mode is => %s in the %s file!!!" \
                               % (str(self.config['Delete']).upper(), sys.argv[1]))
                sectionMamager.setValueBySectionAndKey(sectionToSerche, sectionName, key, value)
            else:
                self.logger.error('The parameter %s line will be deleted under [%s] section from %s file!' \
                                    % (key, sectionName, os.path.basename(self.fileToEdit)))
                sectionMamager.removeKeyValueLineFromSection(sectionToSerche, key)
        
    def setChanges(self, actionList, sectionMamager):
        dic = self.buildActionDict(actionList)
       # newLineDict = {}
        for k, v in dic.iteritems():
            for sec, value in dic[k].iteritems():
                kyeVal = v[sec]
                for key, value in kyeVal.iteritems():
                    sectionName = re.match("[\s\t]*\[[\s\t]*(.*?)[\s\t]*\]", sec).group(1)
                    self.logger.error("The section is --> [%s]" % sectionName)
                    secInstance = sectionMamager.sercheIfSectionExist(sectionName)
                    if secInstance!= None:
                        keyName = key
                        if sectionMamager.sercheIfKeyExistInSection(secInstance, keyName) == True:
                            self.logger.error("The Key: --> %s and Value: --> %s" % (keyName, value))
                            if value == "":
                                self.deleteLine(secInstance, sectionName, keyName, value, sectionMamager)
                            else:
                                sectionMamager.setValueBySectionAndKey(secInstance, sectionName, keyName, value)
                        else:
                            newLineDict = {}
                            newLineDict[sectionName] = { keyName + '=' : value + '\n'}
                            self.appendLine(secInstance, sectionName, newLineDict, sectionMamager)        
                    else:
                        raise Exception, 'The section [%s] not exist in the %s file' % (sectionName, self.fileToEdit)

        allLinesToSave = sectionMamager.getAllLines()
        self.file.writelines(allLinesToSave)


    def __call__(self, editFiles):
        methodDict = {}
        for file in self.config.get('INI_Files', editFiles):
            methodDict[file] = '_ini_parser'
        super(conf_ini, self).__call__(editFiles=editFiles, methodDict=methodDict)

    def _ini_parser(self):
        sectionMgr = SectionManager(self.logger, self.fileToEdit)
        self.loadCurrentFile(sectionMgr)
        fileActionList = self.changeValue(self.fileToEdit)
        self.setChanges(fileActionList, sectionMgr)
