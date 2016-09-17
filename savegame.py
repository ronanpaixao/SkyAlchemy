# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

from __future__ import unicode_literals

import struct
import enum
from collections import namedtuple, OrderedDict
from binascii import hexlify
from cStringIO import StringIO
from datetime import datetime

#try:
#    from typing import List, Union
#except ImportError:  # python 3.4 and below
#    pass


#%% unpack
_types = {
    "bool": struct.Struct('?'),
    "uint8": struct.Struct('B'),
    "uint16": struct.Struct('H'),
    "uint32": struct.Struct('I'),
    "int32": struct.Struct('i'),
    "uint64": struct.Struct('Q'),
    "float32": struct.Struct('f'),
}


def unpack(type, f):
    type = _types[type]
    if callable(type):
        return type(f)
    else:
        return type.unpack(f.read(type.size))[0]


#%% wstring
def read_wstring(f):
    size = unpack("uint16", f)
    return f.read(size).decode('cp1252')
_types["wstring"] = read_wstring


#%% filetime
_EPOCH_AS_FILETIME = 116444736000000000
_HUNDREDS_OF_NANOSECONDS = 10000000

def read_filetime(f):
    ns100_1601 = struct.unpack("<Q", f.read(8))[0]
    (s, ns100_rem) = divmod(ns100_1601 - _EPOCH_AS_FILETIME,
                            _HUNDREDS_OF_NANOSECONDS)
    dt = datetime.utcfromtimestamp(s)
    dt = dt.replace(microsecond=(ns100_rem // 10))
    return dt
_types["filetime"] = read_filetime

#%% stats
_stat_categories = {
    0: "General",
    1: "Quest",
    2: "Combat",
    3: "Magic",
    4: "Crafting",
    5: "Crime",
    6: "DLC Stats",
}

class Stat(object):
    def __init__(self, f):
        self.name = unpack("wstring", f)
        self.category = unpack("uint8", f)
        self.category_name = _stat_categories[self.category]
        self.value = unpack("uint32", f)

    def __repr__(self):
        return "Stat<{}({}):{} = {}>".format(self.category_name,
                                              self.category,
                                              self.name,
                                              self.value)

def read_miscStats(f):
    count = unpack("uint32", f)
    return [Stat(f) for i in range(count)]
_types["miscStat"] = read_miscStats


#%% Created objects

#def read_createdObjects(f):
#    weaponCount = unpack("uint32", f)
#    weapons = [Enchantment(f) for i in range(weaponCount)]
#    return [weapons, armour, potion, poison]
#_types["createdObjects"] = read_createdObjects

#%% Ingredient Shared
#class Stat(object):
#    def __init__(self, f):
#        self.name = unpack("wstring", f)
#        self.category = unpack("uint8", f)
#        self.category_name = _stat_categories[self.category]
#        self.value = unpack("uint32", f)
#
#    def __repr__(self):
#        return "Stat<{}({}):{} = {})>".format(self.category_name,
#                                              self.category,
#                                              self.name,
#                                              self.value)

#%% Form ID
class FormID(object):
    def __init__(self, f):
        self.name = unpack("wstring", f)
        self.category = unpack("uint8", f)
        self.category_name = _stat_categories[self.category]
        self.value = unpack("uint32", f)

    def __repr__(self):
        return "FormID<>".format()


#def read_formIDs(f):
#    count = unpack("uint32", f)
#    return [Stat(f) for i in range(count)]
_types["formID"] = FormID

#%% global data
_gdata_type_names = {
    0: ("Misc Stats", read_miscStats),
    1: ("Player Location", lambda f: "Not implemented"),
    2: ("TES", lambda f: "Not implemented"),
    3: ("Global Variables", lambda f: "Not implemented"),
    4: ("Created Objects", lambda f: "Not implemented"),
    5: ("Effects", lambda f: "Not implemented"),
    6: ("Weather", lambda f: "Not implemented"),
    7: ("Audio", lambda f: "Not implemented"),
    8: ("SkyCells", lambda f: "Not implemented"),
    100: ("Process Lists", lambda f: "Not implemented"),
    101: ("Combat", lambda f: "Not implemented"),
    102: ("Interface", lambda f: "Not implemented"),
    103: ("Actor Causes", lambda f: "Not implemented"),
    104: ("Unknown 104", lambda f: "Not implemented"),
    105: ("Detection Manager", lambda f: "Not implemented"),
    106: ("Location MetaData", lambda f: "Not implemented"),
    107: ("Quest Static Data", lambda f: "Not implemented"),
    108: ("StoryTeller", lambda f: "Not implemented"),
    109: ("Magic Favorites", lambda f: "Not implemented"),
    110: ("PlayerControls", lambda f: "Not implemented"),
    111: ("Story Event Manager", lambda f: "Not implemented"),
    112: ("Ingredient Shared", lambda f: "Not implemented"),
    113: ("MenuControls", lambda f: "Not implemented"),
    114: ("MenuTopicManager", lambda f: "Not implemented"),
    1000: ("Temp Effects", lambda f: "Not implemented"),
    1001: ("Papyrus", lambda f: "Not implemented"),
    1002: ("Anim Objects", lambda f: "Not implemented"),
    1003: ("Timer", lambda f: "Not implemented"),
    1004: ("Synchronized Animations", lambda f: "Not implemented"),
    1005: ("Main", lambda f: "Not implemented"),
}

def read_globalData(f):
    type_ = unpack("uint32", f)
    type_name, type_decoder = _gdata_type_names[type_]
    lenght = unpack("uint32", f)
    return (type_, type_name, type_decoder(StringIO(f.read(lenght))))
_types["globalData"] = read_globalData


#%%
class Savegame(object):
    """This class loads a The Elder Scrolls V: Skyrim savegame file and parses
    useful information.
    """
    def __init__(self, filename):
        #%%
        d = OrderedDict()  # Data storage
        f = open(filename, 'rb')  # TODO: replace
        f.seek(0)
        if True:
#        with open(filename, 'rb') as f:
            # File
            d['magic'] = f.read(13)
            if d['magic'] != 'TESV_SAVEGAME':
                raise AssertionError("Incorrect magic in file header")
            f.seek(13)
            d['headerSize'] = unpack("uint32", f)
            # Header
            header = StringIO(f.read(d['headerSize']))
            d['version'] = unpack("uint32", header)
            if not 7 <= d['version'] <= 9:
                raise AssertionError("Only versions 7 to 9 are supported")
            d['saveNumber'] = unpack("uint32", header)
            d['playerName'] = unpack("wstring", header)
            d['playerLevel'] = unpack("uint32", header)
            d['playerLocation'] = unpack("wstring", header)
            d['gameDate'] = unpack("wstring", header)
            d['playerRaceEditorId'] = unpack("wstring", header)
            d['playerSex'] = {0: "male", 1: "female"}[unpack("uint16", header)]
            d['playerCurExp'] = unpack("float32", header)
            d['playerLvlUpExp'] = unpack("float32", header)
            header.seek(63)
            d['filetime'] = unpack("filetime", header)
            d['shotWidth'] = unpack("uint32", header)
            d['shotHeight'] = unpack("uint32", header)
            # Back to file
            d['screenshotData'] = f.read(3*d['shotWidth']*d['shotHeight'])
            from PIL import Image
            screenshot = Image.frombytes("RGB",
                                         (d['shotWidth'], d['shotHeight']),
                                         d['screenshotData'])
            d['formVersion'] = unpack("uint8", f)
            d['pluginInfoSize'] = unpack("uint32", f)
            # Plugin
            plugin = StringIO(f.read(d['pluginInfoSize']))
            d['pluginCount'] = unpack("uint8", plugin)
            d['plugins'] = [unpack("wstring", plugin)
                            for i in range(d['pluginCount'])]
            # File Location Table
            f.seek( 184494L)
            formIDArrayCountOffset = unpack("uint32", f)
            unknownTable3Offset = unpack("uint32", f)
            globalDataTable1Offset = unpack("uint32", f)
            globalDataTable2Offset = unpack("uint32", f)
            changeFormsOffset = unpack("uint32", f)
            globalDataTable3Offset = unpack("uint32", f)
            globalDataTable1Count = unpack("uint32", f)
            globalDataTable2Count = unpack("uint32", f)
            globalDataTable3Count = unpack("uint32", f)
            changeFormCount = unpack("uint32", f)
            f.read(4*15)  # unused
            # Global Data 1
            f.seek(globalDataTable1Offset)
            gdata1 = []
            for i in range(globalDataTable1Count):
                gdata1.append(unpack("globalData", f))
            # Global Data 2
            f.seek(globalDataTable2Offset)
            gdata2 = []
            for i in range(globalDataTable2Count):
                gdata2.append(unpack("globalData", f))
            # changeForms
            # ...
            # Global Data 3
            f.seek(globalDataTable3Offset)
            gdata3 = []
            for i in range(globalDataTable3Count):
                gdata3.append(unpack("globalData", f))
            # formID
            f.seek(formIDArrayCountOffset)
            formIDArrayCount = unpack("uint32", f)
            formid = struct.Struct('{}I'.format(formIDArrayCount)).unpack(
                f.read(formIDArrayCount*4))
            # Visited Worldspace
            visitedWorldspaceArrayCount = unpack("uint32", f)
            visitedWorldspaceArray = struct.Struct('{}I'.format(
                visitedWorldspaceArrayCount)).unpack(f.read(
                visitedWorldspaceArrayCount*4))
            # unknownTable3
            f.seek(unknownTable3Offset)
            ukt3count = unpack("uint32", f)
            assert(len(f.read()) == ukt3count)
            # EOF
            assert(f.read() == "")



