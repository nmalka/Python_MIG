#!/usr/bin/env python

from PyelementTree import ElementTree
import pdb
import sys, os
if len(sys.argv) != 3:
    print "USAGE - %s <filename> <xpath>" % os.path.basename(sys.argv[0])
    print "<xpath> must be given with single quates if xpath contain \"$\"'"
    sys.exit(3)
    
file_name = sys.argv[1]
xpath = sys.argv[2]

f = ElementTree.open_xfile(file_name)
root = f.getroot_extend()
print 'file_name:', file_name
print 'XML Encoding:', f.docinfo.encoding
print 'XML Version:',  f.docinfo.xml_version
print 'XML Header:',  f.docinfo.header
print 'XML DOCTYPE:\n%s' % '\n'.join(f.docinfo.doctype)
print 'xpath:', xpath
print 'xpath data:'
i = 0
for x in ElementTree.list_xpath(xpath):
    i+=1
    print i, ')' ,x

elements = root.xpath_query(xpath)
print 

for e in elements:
    print '-'*10
    print 'Tag:', e
    print 'Full Path:', e.get_full_xpath()
    if e.text and e.text.strip(): print 'Text:', e.text.strip()
    if e.attrib: print 'Attribute:', e.attrib
    print 'ElementTree:\n%s' % ElementTree.tostring(element = e, encoding = f.docinfo.encoding.lower())
if elements:
    print '-'*10, '\n' 
    print 'Found (%s) elements:' % len(elements)
    print elements
    print
else:
    print "\nNo elements where found\n"
