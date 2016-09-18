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
import zlib
import re
import os
import os.path as osp

from skyrimtypes import _types, unpack


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

filename = osp.join(folder, "Data", "Skyrim.esm")
f = open(filename, 'rb')
#%%
class Record(object):
    def __init__(self, fd, type_):
        self.type = type_
        self.size = unpack("uint32", fd)
        if type_ == "GRUP":
            self.label = fd.read(4).decode("cp1252")
            self.groupType = unpack("int32", fd)
            self.stamp = unpack("uint16", fd)
            unpack("uint16", fd)  # Unknown
            self.version = unpack("uint16", fd)
            unpack("uint16", fd)  # Unknown
#            children = []
#            group_end = fd.tell() + self.size - 24
#            while fd.tell() < group_end:
#                type_ = f.read(4).decode("cp1252")
#                children.append(Record(fd, type_))
#            self.children = children
#            self.data = fd.read(self.size - 24)
            fd.seek(fd.tell() + self.size - 24)
            return
        self.flags = unpack("uint32", fd)
        self.id = unpack("uint32", fd)
        self.revision = unpack("uint32", fd)
        self.version = unpack("uint16", fd)
        self.unknown = unpack("uint16", fd)
        if self.flags & 0x00040000:  # Data is compressed
            decompSize = unpack("uint32", fd)
            compData = fd.read(self.size - 4)
            self.data = zlib.decompress(compData, 0, decompSize)
        else:
            self.data = fd.read(self.size)
    def __repr__(self):
        if self.type == "GRUP":
            return "{}:{}".format(self.type, self.label)
        return self.type


f.seek(0)
records = []
i = 0
while True:
    type_ = f.read(4).decode("cp1252")
#    if i == 10:
#        break
    if type_ == b"":  # EOF
        break
    record = Record(f, type_)
    records.append(record)
    print i, record, f.tell()
    i += 1
