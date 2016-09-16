# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

import struct
import enum

try:
    from typing import List, Union
except ImportError:  # python 3.4 and below
    pass

_struct_bool = struct.Struct('>?')
_struct_uint8 = struct.Struct('>B')
_struct_uint16 = struct.Struct('>H')
_struct_uint32 = struct.Struct('>I')
_struct_int32 = struct.Struct('>i')
_struct_uint64 = struct.Struct('>Q')
_struct_float = struct.Struct('>f')


class Savegame(object):
    """This class loads a The Elder Scrolls V: Skyrim savegame file and parses
    useful information.
    """
    def __init__(self, filename):
        pass

