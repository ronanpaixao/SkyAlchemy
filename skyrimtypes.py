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
from cStringIO import StringIO
from datetime import datetime
import os.path as osp
import cPickle


#%% unpack
_types = {
    "bool": struct.Struct('?'),
    "int8": struct.Struct('b'),
    "uint8": struct.Struct('B'),
    "char": struct.Struct("s"),
    "wchar": struct.Struct("2s"),
    "int16": struct.Struct('h'),
    "uint16": struct.Struct('H'),
    "int32": struct.Struct('i'),
    "uint32": struct.Struct('I'),
    "int64": struct.Struct('q'),
    "uint64": struct.Struct('Q'),
    "float": struct.Struct('f'),
    "float32": struct.Struct('f'),
    "float64": struct.Struct('d'),
    "formid": struct.Struct("I"),
    "iref": struct.Struct("I"),
    "hash": struct.Struct("Q"),
#    "lstring": struct.Struct("I"),
}


def unpack(type_str, f):
    type_ = _types[type_str]
    if callable(type_):
        return type_(f)
    elif getattr(f, "read", False):  # file-like
        tup = type_.unpack(f.read(type_.size))
    else:  # string-like
        tup = type_.unpack(f)
    if len(tup) == 1:
        return tup[0]
    else:
        return tup


#%% wstring
def wstring(f):
    size = unpack("uint16", f)
    try:
        return f.read(size).decode('utf8')
    except:
        return f.read(size).decode('cp1252')
_types["wstring"] = wstring

#%% zstring
def zstring(f):
    if isinstance(f, str) or isinstance(f, bytes):
        try:
            return f[:-1].decode('utf8')
        except:
            return f[:-1].decode('cp1252')
    bs = []
    b = f.read(1)
    while b != b'\x00':
        bs.append(b)
        b = f.read(1)
    ret = b''.join(bs)
    try:
        return ret.decode('utf8')
    except:
        return ret.decode('cp1252')

_types["zstring"] = zstring

#%% lstring

lstrings_file = "lstrings.pkl"
if osp.exists(lstrings_file):
    with open(lstrings_file, 'r') as f:
        lstrings = cPickle.load(f)
else:
    lstrings = {}


def lstring(f):
    id_ = unpack("uint32", f)
    return lstrings.get(id_, "Unknown string")

_types["lstring"] = lstring

#%% vsval
def vsval(f):
    b1 = unpack("uint8", f)
    length = b1 & 0x3
    if length == 0:
        return b1 >> 2
    elif length == 1:
        return (b1 | (unpack("uint8", f) << 8)) >> 2
    elif length == 2:
        return (b1 | (unpack("uint8", f) << 8) | (unpack("uint8", f) << 16)) >> 2
    else:
        raise NotImplementedError("vsval type {} found: 0x{:x}".format(length, b1))
_types["vsval"] = vsval
assert vsval(StringIO(struct.pack("BB", 0xe1, 0x13))) == 0x4f8


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


#%% RefID
class RefID(object):
    formid = {}
    defaultid = {}
    createdid = {}
    __nameless = "Unknown"
    def __init__(self, fd):
#        fd = StringIO(struct.pack("BBB", 0x41, 0xc0, 0xf2))
        first = unpack("uint8", fd)
        rest = struct.Struct('>H').unpack(fd.read(2))[0]
        type_ = first >> 6
        self.value = (first & 0x3f) << 16 ^ rest
        if type_ == 0:
            self.name = self.formid.get(self.value, self.__nameless)
        elif type_ == 1:
            self.name = self.defaultid.get(self.value, self.__nameless)
        elif type_ == 2:
            self.name = self.createdid.get(self.value,self. __nameless)
        elif type_ == 3:
            self.name = self.__nameless
        self.type = {0: "F", 1: "D", 2: "C", 3: "U"}[type_]

    def __repr__(self):
        if self.name == self.__nameless:
            return "RefID<{}:{:08X}>".format(self.type, self.value)
        else:
            return "RefID<{}>".format(self.name)
_types["RefID"] = RefID


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
_types["FormID"] = FormID