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


#%% unpack
_types = {
    "bool": struct.Struct('?'),
    "uint8": struct.Struct('B'),
    "uint16": struct.Struct('H'),
    "uint32": struct.Struct('I'),
    "int32": struct.Struct('i'),
    "uint64": struct.Struct('Q'),
    "float32": struct.Struct('f'),
    "float": struct.Struct('f'),
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