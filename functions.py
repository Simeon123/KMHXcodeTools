#!/usr/bin/env python

# KMHXcodeTools
# functions.py
# Ken M. Haggerty
# CREATED: 2017 Mar 09
# EDITED:  2017 May 02

##### IMPORTS

import re

##### Shared

### Constants

PBXGroupSectionChildrenKey = "children"
PBXGroupSectionIdKey = "fileRef"

### Functions

def sortElements(elements, order):
    orderCopy = list(order)
    sortedArray = []
    while len(orderCopy) > 0:
        item = orderCopy.pop(0)
        fileRef = item[PBXGroupSectionIdKey]
        if PBXGroupSectionChildrenKey in item:
            orderCopy = item[PBXGroupSectionChildrenKey] + orderCopy
        elif fileRef in elements:
            value = elements[fileRef]
            sortedArray.append(value)
    return sortedArray

##### PBXProj Order

### Constants

PBXGroupSectionNameKey = "name" # temp
PBXBuildSectionIdKey = "id"

### Regexes

PBXGroupSectionRegex = r"(^[\S\s]*)(\/\*\s*Begin\s+PBXGroup\s+section\s*\*\/s*[^\n]*\n)([\S\s]*)(\n\s*\/\*\s*End\s+PBXGroup\s+section\s*\*\/s*[^\n]*)([\S\s]*$)"
# 1 = Beginning of file
# 2 = PBXGroup section header
# 3 = PBXGroup section body
# 4 = PBXGroup section footer
# 5 = End of file

PBXGroupSectionGroupRegex = r"(^|\n)([^\n\w]*(\w*)\s*(\/\*\s*(.*)\s*\*\/){0,1}\s*=\s*(\{[^\}]*\})\s*;[^\n]*)"
# 1 = (start of file / newline)
# 2 = (value)
# 3 = PBXGroupSection fileRef
# 4 = (unused)
# 5 = PBXGroupSection name # temp
# 6 = PBXGroupSection dictionary

PBXGroupSectionChildrenRegex = r"children\s*=\s*\(([^\)\;]*)\)\;"
# 1 = PBXGroup children

PBXGroupSectionChildRegex = r"(^|\n)(\s*(\w*)\s*(\/\*\s*((\S+.*\.\S+)|\S+[^\*\/]*).*\*\/)\s*,[^\n]*)"
# 1 = (start of file / newline)
# 2 = (value)
# 3 = PBXGroupSection child fileRef
# 4 = PBXGroupSection name and directory # temp
# 5 = PBXGroupSection name # temp
# 6 = (unused)

PBXBuildFileSectionRegex = r"\/\*\s*Begin\s*PBXBuildFile\s*section\s*\*\/\n*([\S\s]*)\n*\/\*\s*End\s*PBXBuildFile\s*section\s*\*\/"
# 1 = PBXBuildFileSection body

PBXBuildFileSectionLineRegex = r"(^|\n)\s*(\w*).*=\s*\{.*fileRef\s*=\s*(\w+).*\};"
# 1 = (start of file / newline)
# 2 = PBXBuildFile ID
# 3 = PBXBuildFile fileRef

### Functions

def processPBXProjOrder(text):
    pbxGroupSectionBody = re.search(PBXGroupSectionRegex, text).group(3)
    pbxGroupSections = re.findall(PBXGroupSectionGroupRegex, pbxGroupSectionBody)
    pbxBuildFileSectionBody = re.search(PBXBuildFileSectionRegex, text).group(1)
    pbxBuildFileSectionLines = re.findall(PBXBuildFileSectionLineRegex, pbxBuildFileSectionBody)
    fileRefDictionary = {}
    for line in pbxBuildFileSectionLines:
        fileRef = line[2]
        fileId = line[1]
        fileRefDictionary[fileRef] = fileId
    elements = {}
    parentIds = set([])
    childrenIds = set([])
    for section in pbxGroupSections:
        fileRef = section[2]
        dictionary = section[5]
        children = re.search(PBXGroupSectionChildrenRegex, dictionary).group(1)
        children = re.findall(PBXGroupSectionChildRegex, children)
        childDictionaries = []
        for child in children:
            childFileRef = child[2]
            childName = child[4]
            dictionary = {
                PBXGroupSectionIdKey : childFileRef,
                PBXGroupSectionNameKey : childName
            }
            try:
                fileId = fileRefDictionary[childFileRef]
                dictionary[PBXBuildSectionIdKey] = fileId
            except Exception:
                pass
            childDictionaries.append(dictionary)
        children = list(map(lambda x: x[2], children))
        dictionary = {}
        if len(childDictionaries) > 0:
            dictionary[PBXGroupSectionChildrenKey] = childDictionaries
        try: # temp
            name = section[4]
            dictionary[PBXGroupSectionNameKey] = name
        except Exception: 
            pass
        elements[fileRef] = dictionary
        parentIds.update([fileRef])
        childrenIds.update(children)
    parents = parentIds - childrenIds
    pbxProjOrder = []
    for parent in parents:
        dictionary = generateChildren(parent, elements)
        pbxProjOrder.append(dictionary)
    return pbxProjOrder

def generateChildren(node, source):
    dictionary = {
        PBXGroupSectionIdKey : node
    }
    if PBXGroupSectionNameKey in source[node]: # temp
        dictionary[PBXGroupSectionNameKey] = source[node][PBXGroupSectionNameKey]
    children = source[node][PBXGroupSectionChildrenKey]
    i = 0
    while i < len(children):
        child = children[i]
        childFileRef = child[PBXGroupSectionIdKey]
        if childFileRef in source:
            children.pop(i)
            grandchildren = generateChildren(childFileRef, source)
            children.insert(i, grandchildren)
        i += 1
    dictionary[PBXGroupSectionChildrenKey] = children
    return dictionary

##### PBXBuildFile Section

### Functions

def updatePBXBuildFileSection(text, order):
    return text

##### PBXFileReference Section

### Regexes

PBXFileReferenceSectionRegex = r"(^[\S\s]*)(\/\*\s*Begin\s+PBXFileReference\s+section\s*\*\/s*[^\n]*\n)([\S\s]*)(\n\s*\/\*\s*End\s+PBXFileReference\s+section\s*\*\/s*[^\n]*)([\S\s]*$)"
# 1 = Beginning of file
# 2 = PBXGroup section header
# 3 = PBXGroup section body
# 4 = PBXGroup section footer
# 5 = End of file

PBXFileReferenceSectionLineRegex = r"(^|\n)(\s*(\w*)\s*(\/\*\s*[^(\*\/)]*\s*\*\/){0,1}\s*={0,1}\s*(\{[^\}]*\}){0,1}\s*;)"
# 1 = (start of file / newline)
# 2 = (value)
# 3 = PBXBuildFile reference ID
# 4 = PBXBuildFile name
# 5 = PBXBuildFile dictionary

### Functions

def updatePBXFileReferenceSection(text, order):
    pbxFileReferenceSectionBody = re.search(PBXFileReferenceSectionRegex, text).group(3)
    pbxFileReferenceSectionLines = re.findall(PBXFileReferenceSectionLineRegex, pbxFileReferenceSectionBody)
    elements = {}
    for line in pbxFileReferenceSectionLines:
        fileRef = line[2]
        value = line[1]
        elements[fileRef] = value
    orderCopy = list(order)
    array = []
    while len(orderCopy) > 0:
        item = orderCopy.pop(0)
        if PBXGroupSectionChildrenKey in item:
            orderCopy = item[PBXGroupSectionChildrenKey] + orderCopy
        elif item in elements:
            value = elements[item]
            array.append(value)
    pbxFileReferenceSectionBody = "\n".join(array)
    updatedText = re.sub(PBXFileReferenceSectionRegex, r"\1\2" + pbxFileReferenceSectionBody + r"\4\5", text, flags=re.IGNORECASE)
    return updatedText

##### PBXFrameworksBuildPhase Section

### Functions

def updatePBXFrameworksBuildPhaseSection(text, order):
    return text

##### PBXGroup Section

### Functions

def updatePBXGroupSection(text, order):
    return text

##### PBXResourcesBuildPhase Section

### Functions

def updatePBXResourcesBuildPhaseSection(text, order):
    return text

##### PBXSourcesBuildPhase Section

### Functions

def updatePBXSourcesBuildPhaseSection(text, order):
    return text
