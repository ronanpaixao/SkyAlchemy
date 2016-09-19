# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

from __future__ import unicode_literals, division

import struct
import enum
from collections import namedtuple, OrderedDict
from binascii import hexlify
from cStringIO import StringIO
from datetime import datetime
import zlib
import re
import os
import os.path as osp
import cPickle

from skyrimtypes import _types, unpack

#%%
db_types = ['MGEF', 'INGR']
db = {k: {} for k in db_types}

#%% Find Skyrim folder
with open(r"C:\Program Files (x86)\Steam\SteamApps\libraryfolders.vdf") as f:
    folders = [r"C:\Program Files (x86)\Steam"]
    lf = f.read()
    folders.extend([fn.replace("\\\\", "\\") for fn in
        re.findall('^\s*"\d*"\s*"([^"]*)"', lf, re.MULTILINE)])

def getSkyrimFolder(folders):
    for folder in folders:
        if osp.exists(osp.join(folder, "SteamApps")):
            if "Skyrim" in os.listdir(osp.join(folder, "SteamApps", "common")):
                return osp.join(folder, "SteamApps", "common", "Skyrim")

folder = getSkyrimFolder(folders)
if folder is None:
    raise RuntimeError("Could not find Skyrim folder")

data_filename = osp.join(folder, "Data", "Skyrim.esm")
strings_filename = osp.join(folder, "Data", "Strings", "Skyrim_English.STRINGS")

#%% Strings
def strdir(f):
    return (unpack("uint32", f), unpack("uint32", f))

def extract_strings(filename):
    """Extract strings from string table

    Based on data from:
    http://en.m.uesp.net/wiki/Tes5Mod:String_Table_File_Format
    """
    f = open(filename, 'rb')
    str_count = unpack("uint32", f)
    dataSize = unpack("uint32", f)
    strings = {}
    strings_dir = []
    for i in range(str_count):
        print "Reading directory: {}/{} = {:0.2f}".format(
            i, str_count, i/str_count*100)
        strings_dir.append(strdir(f))

    data = StringIO(f.read(dataSize))
    f.close()
    if filename.lower().endswith(".strings"):
        for i, (id_, offset) in enumerate(strings_dir):
            print "Reading string: {}/{} = {:0.2f}".format(
                i, str_count, i/str_count*100)
            data.seek(offset)
            strings[id_] = unpack("zstring", data)
    else:  # .dlstrings, .ilstrings
        for i, (id_, offset) in enumerate(strings_dir):
            print "Reading string: {}/{} = {:0.2f}".format(
                i, str_count, i/str_count*100)
            data.seek(offset + 4)  # ignore lenght
            strings[id_] = unpack("zstring", data)
    return strings

lstrings_file = "lstrings.pkl"
#if osp.exists(lstrings_file):
#    with open(lstrings_file, 'r') as f:
#        lstrings = cPickle.load(f)
#else:
if not osp.exists(lstrings_file):
    lstrings = extract_strings(strings_filename)
    with open(lstrings_file, 'w') as f:
        cPickle.dump(lstrings, f)


#%% Data
f = open(data_filename, 'rb')

#%% Field
class Field(object):
    def __init__(self, f):
        self.type = f.read(4)
        size = unpack("uint16", f)
        self.data = f.read(size)

    def __repr__(self):
        return "Field<{}>".format(self.type)
_types["Field"] = Field

#%%
class Record(object):
    def __init__(self, fd, type_):
        self.type = type_
        dataSize = unpack("uint32", fd)
#        if type_ == "GRUP":
#            self.label = fd.read(4).decode("cp1252")
#            self.groupType = unpack("int32", fd)
#            self.stamp = unpack("uint16", fd)
#            unpack("uint16", fd)  # Unknown
#            self.version = unpack("uint16", fd)
#            unpack("uint16", fd)  # Unknown
##            children = []
##            group_end = fd.tell() + self.size - 24
##            while fd.tell() < group_end:
##                type_ = f.read(4).decode("cp1252")
##                children.append(Record(fd, type_))
##            self.children = children
##            self.data = fd.read(self.size - 24)
#            if self.label in _read_record_types:
#                data = StringIO(fd.read(self.size - 24))
#            else:  # skip
#                fd.seek(fd.tell() + self.size - 24)
#            return
        self.flags = unpack("uint32", fd)
        self.id = unpack("uint32", fd)
        self.revision = unpack("uint32", fd)
        self.version = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        if self.flags & 0x00040000:  # Data is compressed
            decompSize = unpack("uint32", fd)
            compData = fd.read(dataSize - 4)
            data = zlib.decompress(compData, 0, decompSize)
            dataSize = decompSize
        else:
            data = fd.read(dataSize)
        data = StringIO(data)
        fields = []
        while data.tell() < dataSize:
            fields.append(Field(data))
        self.fields = fields
    def __repr__(self):
        if self.type == "GRUP":
            return "{}:{}".format(self.type, self.label)
        return self.type


class Effect(object):
    def __init__(self, id_):
        self.EffectID = id_

    def cost(self):
        try:
            return (db['MGEF'][self.EffectID].BaseCost *
                    (self.Magnitude * self.Duration / 10) ** 1.1)
        except:
            return -1

    def __repr__(self):
        return "Field<{}>".format(self.type)
_types["Field"] = Field


class INGR(Record):
    def __init__(self, fd, type_="INGR"):
        super(INGR, self).__init__(fd, type_)
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.Value = unpack("uint32", field.data[:4])
                self.Weight = unpack("float", field.data[4:])
            elif field.type == "EFID":
                self.effects.append(Effect(unpack("formid", field.data)))
            elif field.type == "EFIT":
                last_effect = self.effects[-1]
                last_effect.Magnitude = unpack("float", field.data[:4])
                last_effect.AreaOfEffect = unpack("uint32", field.data[4:8])
                last_effect.Duration = unpack("uint32", field.data[:4])
        db['INGR'][self.id] = self

    def __repr__(self):
        return "INGR<{:08X}:{}>".format(self.id, self.FullName)

_types["INGR"] = INGR


class MGEF(Record):
    """Magic Effect.

    Data about magic effects from spells, enchantments and potions.

    Reference:
        http://en.m.uesp.net/wiki/Tes5Mod:Mod_File_Format/MGEF
    """
    def __init__(self, fd, type_="MGEF"):
        super(MGEF, self).__init__(fd, type_)
        self.FullName = "Nameless"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                fdata = StringIO(field.data)
                self.Flags = unpack("uint32", fdata)
                self.BaseCost = unpack("float", fdata)
                self.RelatedID = unpack("formid", fdata)
                self.Skill = unpack("int32", fdata)
                self.ResistanceAV = unpack("uint32", fdata)
                fdata.read(16)
                self.SkillLevel = unpack("uint32", fdata)
                self.Area = unpack("uint32", fdata)
                self.CastingTime = unpack("float", fdata)
                fdata.read(12)
                self.EffectType = unpack("uint32", fdata)
                self.PrimaryAV = unpack("int32", fdata)
            elif field.type == "ESCE":
                self.CounterEffects = unpack("formid", fdata)
            elif field.type == "DNAM":
                self.Description = unpack("lstring", fdata)
        db['MGEF'][self.id] = self

    def __repr__(self):
        return "MGEF<{:08X}:{}>".format(self.id, self.FullName)

_types["MGEF"] = MGEF


class Group(object):
    def __init__(self, fd, type_="GRUP"):
        self.type = type_
        self.size = unpack("uint32", fd)
        group_end = fd.tell() + self.size - 24
        self.label = fd.read(4).decode("cp1252")
        self.groupType = unpack("int32", fd)
        self.stamp = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        self.version = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        records = []
        if self.label in _read_record_types:  # Only read some groups
            while fd.tell() < group_end:
                type_ = f.read(4).decode("cp1252")
#                data = StringIO(fd.read(self.size - 24))

                if type_ == "":  # EOF
                    break
                record = _read_record_types[type_](fd, type_)
                records.append(record)
            self.records = records
        else:  # skip uninteresting groups
            fd.seek(fd.tell() + self.size - 24)
    def __repr__(self):
        if self.type == "GRUP":
            return "{}:{}".format(self.type, self.label)
        return self.type

_read_record_types = {'INGR': INGR, 'GRUP': Group, 'MGEF': MGEF}

f.seek(0)
records = []
i = 0
import sys
while True:
    type_ = f.read(4).decode("cp1252")
#    if i == 10:
#        break
    if type_ == "":  # EOF
        break
    if type_ == "GRUP":
        record = Group(f)
    else:
        record = Record(f, type_)
    records.append(record)
    print i, record, f.tell()
    sys.stdout.flush()
    i += 1

f.close()

#%% Save data
with open('data.pkl', 'wb') as f:
    cPickle.dump(db, f)

