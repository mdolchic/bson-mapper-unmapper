import struct
import math
from typing import Any
import collections
from datetime import datetime, timezone
from dataclasses import is_dataclass, fields as dataclass_fields
from collections import OrderedDict

PROMPT = '>>> '


def run_calc(context: dict[str, Any] | None = None) -> None:
    """Run interactive calculator session in specified namespace"""


if __name__ == '__main__':
    context = {'math': math}
    run_calc(context)

class MapperConfigError(ValueError):
    pass

class MapperUnsupportedOptionError(MapperConfigError):
    pass

class BsonError(ValueError):
    pass

class BsonMarshalError(BsonError):
    pass

class BsonUnsupportedObjectError(BsonMarshalError):
    pass

class BsonUnsupportedKeyError(BsonMarshalError):
    pass

class BsonKeyWithZeroByteError(BsonUnsupportedKeyError):
    pass

class BsonInputTooBigError(BsonMarshalError):
    pass

class BsonBinaryTooBigError(BsonInputTooBigError):
    pass

class BsonIntegerTooBigError(BsonInputTooBigError):
    pass

class BsonStringTooBigError(BsonInputTooBigError):
    pass

class BsonDocumentTooBigError(BsonInputTooBigError):
    pass

class BsonCycleDetectedError(BsonMarshalError):
    pass

class BsonUnmarshalError(BsonError):
    pass

class BsonBrokenDataError(BsonUnmarshalError):
    pass

class BsonIncorrectSizeError(BsonBrokenDataError):
    pass

class BsonTooManyDataError(BsonBrokenDataError):
    pass

class BsonNotEnoughDataError(BsonBrokenDataError):
    pass

class BsonInvalidElementTypeError(BsonBrokenDataError):
    pass

class BsonInvalidStringError(BsonBrokenDataError):
    pass

class BsonStringSizeError(BsonBrokenDataError):
    pass

class BsonInconsistentStringSizeError(BsonBrokenDataError):
    pass

class BsonBadStringDataError(BsonBrokenDataError):
    pass

class BsonBadKeyDataError(BsonBrokenDataError):
    pass

class BsonRepeatedKeyDataError(BsonBrokenDataError):
    pass

class BsonBadArrayIndexError(BsonBrokenDataError):
    pass

class BsonInvalidArrayError(BsonBrokenDataError):
    pass

class BsonInvalidBinarySubtypeError(BsonBrokenDataError):
    pass

class Mapper:
    _allowed_options = {"python_only", "keep_types"}
    _python_only: bool = False
    _keep_types: bool = False

    def __init__(self, **options: Any) -> None:
        for name in options:
            if name not in self._allowed_options:
                raise MapperUnsupportedOptionError(name)
        python_only = options.get("python_only", False)
        super().__setattr__("_python_only", python_only)
        keep_types = options.get("keep_types", False)
        super().__setattr__("_keep_types", keep_types)

    @property
    def python_only(self) -> bool:
        return self._python_only
    @property
    def keep_types(self) -> bool:
        return self._keep_types
    def __setattr__(self, name: str, value: Any) -> None:
        if name in self._allowed_options:
            raise AttributeError()
        super().__setattr__(name, value)
    def __delattr__(self, name: str) -> None:
        if name in self._allowed_options:
            raise AttributeError()
        super().__delattr__(name)

    def marshal(self, doc: dict[str, Any]) -> bytes:
        orig = doc

        if not isinstance(doc, dict):
            asdoc = as_doc(doc)
            if asdoc is None:
                raise BsonUnsupportedObjectError(doc)
            doc = asdoc

        nt_reg: NTReg | None = None
        root_type_tag: str | None = None
        if self._keep_types:
            nt_reg = NTReg()
            if is_namedtuple_instance(orig):
                root_type_tag = nt_reg.get_or_reg(orig)

        return encode_document(doc, set(), keep_types = self._keep_types, nt_reg = nt_reg, is_root=True,
                               root_type_tag = root_type_tag)

    def unmarshal(self, data: bytes) -> dict[str, Any]:
        if len(data) < 4:
            raise BsonBrokenDataError(data)

        (size,) = struct.unpack_from("<i", data, 0)
        if size < 0:
            raise BsonNotEnoughDataError(data)
        if len(data) == 4 and size < 5:
            raise BsonIncorrectSizeError(data)
        if size < len(data):
            raise BsonTooManyDataError(data)
        if size > len(data):
            raise BsonNotEnoughDataError(data)
        if size < 5:
            raise BsonIncorrectSizeError(data)

        nt_types: dict[str, Any] | None = None
        if self._keep_types:
            nt_types = {}

        doc, _ = decode_document(data, 0, python_only = self._python_only, keep_types = self._keep_types,
                                 nt_types=nt_types)
        if self._keep_types and nt_types is not None:
            root_tag = nt_types.get("__root_self__")
            if isinstance(root_tag, str):
                NT = get_namedtuple_class_from_nt_types(root_tag, nt_types)
                info = nt_types.get(root_tag)
                fields = info.get("fields") if isinstance(info, dict) else None
                if NT is not None and isinstance(fields, list) and all(isinstance(f, str) for f in fields):
                    args = [doc[f] for f in fields]
                    doc = NT(*args)
            doc = fix_pending_nt(doc, nt_types)

        return doc

def is_namedtuple_instance(value: Any) -> bool:
    if not isinstance(value, tuple):
        return False
    cls = value.__class__
    fields = getattr(cls, "_fields", None)
    if not isinstance(fields, tuple):
        return False
    return all(isinstance(name, str) for name in fields)

def as_doc(obj: Any) -> dict[str, Any] | None:
    cls = obj.__class__
    if is_namedtuple_instance(obj):
        fields = getattr(obj, "_fields")
        if isinstance(fields, tuple):
            mapping = OrderedDict()
            for name in fields:
                mapping[name] = getattr(obj, name)
            return mapping

    if is_dataclass(obj) and not isinstance(obj, type):
        fields = list(dataclass_fields(obj))
        mapping = OrderedDict()
        for f in fields:
            mapping[f.name] = getattr(obj, f.name)
        return mapping

    props: list[str] = []
    for name in dir(cls):
        attr = getattr(cls, name, None)
        if isinstance(attr, property):
            props.append(name)
    if not props:
        return None

    props.sort()
    supported_value_types = (bool, type(None), int, float, str, bytes, bytearray, datetime, dict, list, tuple)

    mapping: OrderedDict[str, Any] = OrderedDict()
    for name in props:
        try:
            value = getattr(obj, name)
        except RecursionError:
            raise
        except Exception:
            continue
        if value is obj:
            raise BsonCycleDetectedError()
        if not isinstance(value, supported_value_types) and as_doc(value) is None:
            continue
        mapping[name] = value
    if not mapping:
        return None
    return mapping

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1

class NTReg:
    def __init__(self) -> None:
        self._class_to_id: dict[type, str] = {}
        self._id_to_info: dict[str, dict[str, Any]] = {}
        self._counter: int = 0

    def get_or_reg(self, value: Any) -> str | None:
        if not is_namedtuple_instance(value):
            return None
        cls = value.__class__
        type_id = self._class_to_id.get(cls)
        if type_id is None:
            type_id = f"nt-{self._counter}"
            self._counter += 1
            name = getattr(cls, "__name__", "")
            fields = list(getattr(cls, "_fields", ()))
            defaults_map = getattr(cls, "_field_defaults", None)
            if not isinstance(defaults_map, dict):
                defaults_map = {}
            self._class_to_id[cls] = type_id
            self._id_to_info[type_id] = {"name": name, "fields": fields, "defaults": defaults_map}
        return type_id

    @property
    def type_info(self) -> dict[str, dict[str, Any]]:
        return self._id_to_info

def get_namedtuple_class_from_nt_types(type_id: str, nt_types: dict[str, Any],) -> type | None:
    info = nt_types.get(type_id)
    if not isinstance(info, dict):
        return None
    cls = info.get("__cls__")
    if isinstance(cls, type):
        return cls

    name = info.get("name")
    fields = info.get("fields")
    defaults = info.get("defaults", {})

    if not isinstance(name, str):
        return None
    if not isinstance(fields, list) or not all(isinstance(f, str) for f in fields):
        return None
    if not isinstance(defaults, dict):
        defaults = {}

    field_names: list[str] = list(fields)
    nt_factory = getattr(collections, "namedtuple")
    NT = nt_factory("NT", field_names)
    NT.__name__ = name

    if defaults:
        new_defaults = [0] * len(fields)
        field_index = {fname: i for i, fname in enumerate(fields)}
        for fname, fval in defaults.items():
            idx = field_index.get(fname)
            if idx is not None and 0 <= idx < len(new_defaults):
                new_defaults[idx] = fval
        NT.__new__.__defaults__ = tuple(new_defaults)

    info["__cls__"] = NT
    return NT

class PendingNT:
    def __init__(self, type_id: str, value: Any):
        self.type_id = type_id
        self.value = value

def get_type_metadata(value: Any, nt_reg: NTReg | None = None) -> str:
    if nt_reg is not None:
        type_id = nt_reg.get_or_reg(value)
        if type_id is not None:
            return type_id
    if isinstance(value, tuple):
        return "tuple"
    if isinstance(value, bytearray):
        return "bytearray"
    return ""

def encode_cstring(name: str) -> bytes:
    data = name.encode('utf-8')
    return data + b"\x00"

def encode_string(value: str) -> bytes:
    data = value.encode('utf-8')
    length = len(data) + 1
    if length > INT32_MAX:
        raise BsonStringTooBigError(length)
    length_bytes = struct.pack('<i', length)
    return length_bytes + data + b"\x00"

def encode_array(seq: list[Any] | tuple[Any, ...], st: set[int], keep_types: bool = False,
                 nt_reg: NTReg | None = None) -> bytes:
    if id(seq) in st:
        raise BsonCycleDetectedError()

    st.add(id(seq))
    elements = bytearray()

    type_tags: list[str] = []

    for i, item in enumerate(seq):
        key = str(i)
        elements += encode_element(key, item, st, keep_types, nt_reg)
        if keep_types:
            type_tags.append(get_type_metadata(item, nt_reg))

    if keep_types and type_tags and any(type_tags):
        meta_str = ":".join(type_tags)
        meta_bytes = meta_str.encode('utf-8')
        length = len(meta_bytes)
        if length > INT32_MAX:
            raise BsonBinaryTooBigError(length)
        metadata = bytearray()
        metadata += b"\x05"
        metadata += encode_cstring("__metadata__")
        metadata += struct.pack("<i", length)
        metadata += bytes([128])
        metadata += meta_bytes
        elements += metadata

    length = 4 + len(elements) + 1
    if length > INT32_MAX:
        raise BsonDocumentTooBigError(length)
    length_bytes = struct.pack("<i", length)
    st.remove(id(seq))
    return length_bytes + elements + b"\x00"

def encode_element(name: str, value: object, st: set[int], keep_types: bool = False, nt_reg: NTReg | None = None)\
        -> bytes:
    name_bytes = encode_cstring(name)
    asdoc = as_doc(value)
    if asdoc is not None:
        type_byte = b"\x03"
        value_byte = encode_document(asdoc, st, keep_types, nt_reg, is_root=False, root_type_tag=None)
    elif isinstance(value, bool):
        type_byte = b"\x08"
        value_byte = b"\x01" if value else b"\x00"
    elif value is None:
        type_byte = b"\x0A"
        value_byte = b""
    elif isinstance(value, int):
        if value < INT64_MIN or value > INT64_MAX:
            raise BsonIntegerTooBigError(value)
        if INT32_MIN <= value <= INT32_MAX:
            type_byte = b"\x10"
            value_byte = struct.pack('<i', value)
        else:
            type_byte = b"\x12"
            value_byte = struct.pack('<q', value)
    elif isinstance(value, float):
        type_byte = b"\x01"
        value_byte = struct.pack('<d', value)
    elif isinstance(value, str):
        type_byte = b"\x02"
        value_byte = encode_string(value)
    elif isinstance(value, (bytes, bytearray)):
        type_byte = b"\x05"
        data = bytes(value)
        length = len(data)
        if length > INT32_MAX:
            raise BsonBinaryTooBigError(length)
        value_byte = struct.pack('<i', length) + b"\x00" + data
    elif isinstance(value, datetime):
        type_byte = b"\x09"
        dt_utc = value.astimezone(timezone.utc)
        epoch = datetime(1970, 1, 1, tzinfo=timezone.utc)
        ms = int((dt_utc - epoch).total_seconds() * 1000)
        value_byte = struct.pack("<q", ms)
    elif isinstance(value, dict):
        type_byte = b"\x03"
        value_byte = encode_document(value, st, keep_types, nt_reg, is_root=False, root_type_tag=None)
    elif isinstance(value, (list, tuple)):
        type_byte = b"\x04"
        value_byte = encode_array(value, st, keep_types, nt_reg)
    else:
        raise BsonUnsupportedObjectError(value)
    return type_byte + name_bytes + value_byte

def encode_document(doc: dict[str, Any], st: set[int], keep_types: bool = False,
                    nt_reg: NTReg | None = None, is_root: bool = False, root_type_tag: str | None = None) -> bytes:
    if id(doc) in st:
        raise BsonCycleDetectedError()

    st.add(id(doc))
    elements = bytearray()

    for key in doc.keys():
        if not isinstance(key, str):
            raise BsonUnsupportedKeyError(key)
    for key in doc.keys():
        key_bytes = key.encode('utf-8')
        if b"\x00" in key_bytes:
            raise BsonKeyWithZeroByteError(key)
    supported_value_types = (bool, type(None), int, float, str, bytes, bytearray, datetime, dict, list, tuple)
    for key, value in doc.items():
        if not isinstance(value, supported_value_types) and as_doc(value) is None:
            raise BsonUnsupportedObjectError(value)
    for key, value in doc.items():
        if value == doc:
            raise BsonCycleDetectedError()

    type_tags: list[str] = []

    if isinstance(doc, OrderedDict):
        keys = doc.keys()
    else:
        keys = sorted(doc.keys())

    for key in keys:
        elements += encode_element(key, doc[key], st, keep_types, nt_reg)
        if keep_types:
            type_tags.append(get_type_metadata(doc[key], nt_reg))

    if keep_types:
        meta_str = ":".join(type_tags) if type_tags else ""
        if is_root and nt_reg is not None and nt_reg.type_info:
            meta_doc: dict[str, Any] = {"types": nt_reg.type_info}
            if meta_str:
                meta_doc["children"] = meta_str
            if root_type_tag is not None:
                meta_doc["self"] = root_type_tag
            meta_bson = marshal(meta_doc)
            doc_bytes = b"\x00" + meta_bson
            length = len(doc_bytes)
            if length > INT32_MAX:
                raise BsonBinaryTooBigError(length)
            metadata = bytearray()
            metadata += b"\x05"
            metadata += encode_cstring("__metadata__")
            metadata += struct.pack("<i", length)
            metadata += bytes([128])
            metadata += doc_bytes
            elements += metadata
        elif type_tags and any(type_tags):
            meta_bytes = meta_str.encode("utf-8")
            length = len(meta_bytes)
            if length > INT32_MAX:
                raise BsonBinaryTooBigError(length)
            metadata = bytearray()
            metadata += b"\x05"
            metadata += encode_cstring("__metadata__")
            metadata += struct.pack("<i", length)
            metadata += bytes([128])
            metadata += meta_bytes
            elements += metadata

    length = 4 + len(elements) + 1
    if length > INT32_MAX:
        raise BsonDocumentTooBigError(length)
    length_bytes = struct.pack('<i', length)
    res = bytearray()
    res += length_bytes + elements + b"\x00"
    st.remove(id(doc))
    return bytes(res)

def marshal(doc: dict[str, Any]) -> bytes:
    return Mapper().marshal(doc)

def read_int(data: bytes, offset: int) -> tuple[int, int]:
    try:
        (value,) = struct.unpack_from('<i', data, offset)
    except struct.error as e:
        raise BsonBrokenDataError() from e
    return value, offset + 4

def read_int64(data: bytes, offset: int) -> tuple[int, int]:
    (value,) = struct.unpack_from('<q', data, offset)
    return value, offset + 8

def read_float(data: bytes, offset: int) -> tuple[float, int]:
    (value,) = struct.unpack_from('<d', data, offset)
    return value, offset + 8

def read_cstring(data: bytes, offset: int) -> tuple[str, int]:
    end = data.find(0, offset)
    if end == -1:
        raise BsonBrokenDataError(data)
    st = data[offset:end]
    try:
        s = st.decode("utf-8")
    except UnicodeDecodeError as e:
        raise BsonBadStringDataError(data) from e
    return s, end + 1

def read_string(data: bytes, offset: int, end: int) -> tuple[str, int]:
    if offset + 4 > end:
        raise BsonStringSizeError(data)
    (length,) = struct.unpack_from("<i", data, offset)
    if length <= 0:
        raise BsonStringSizeError(data)
    offset += 4
    str_end = offset + length
    if str_end >= end:
        raise BsonInconsistentStringSizeError(data)
    if data[str_end - 1] != 0:
        raise BsonBrokenDataError(data)
    st = data[offset : str_end - 1]
    try:
        s = st.decode("utf-8")
    except UnicodeDecodeError as e:
        raise BsonBadStringDataError(data) from e
    return s, str_end

def decode_array(data: bytes, offset: int, python_only: bool = False, keep_types: bool = False,
                 nt_types: dict[str, Any] | None = None) -> tuple[list[Any], int]:
    doc, new_offset = decode_document(data, offset, python_only, keep_types, nt_types)
    idxs: list[int] = []
    for key in doc.keys():
        if not key.isdigit():
            raise BsonBadArrayIndexError()
        if key != "0" and key.startswith("0"):
            raise BsonBadArrayIndexError(key)
        try:
            idx = int(key)
        except ValueError:
            raise BsonBadArrayIndexError()
        if idx < 0:
            raise BsonBadArrayIndexError(key)
        idxs.append(idx)
    if not idxs:
        return [], new_offset
    mx = max(idxs)
    if python_only and mx + 1 != len(idxs):
        raise BsonInvalidArrayError(data)
    result: list[Any] = [None] * (mx + 1)
    for idx in idxs:
        result[idx] = doc[str(idx)]
    return result, new_offset

def decode_value(type_byte: int, data: bytes, offset: int, end: int, python_only: bool = False,
                 keep_types: bool = False, nt_types: dict[str, Any] | None = None) -> tuple[Any, int]:
    if type_byte == 0x01:
        value, offset = read_float(data, offset)
    elif type_byte == 0x02:
        value, offset = read_string(data, offset, end)
    elif type_byte == 0x03:
        value, offset = decode_document(data, offset, python_only, keep_types, nt_types)
    elif type_byte == 0x04:
        value, offset = decode_array(data, offset, python_only, keep_types, nt_types)
    elif type_byte == 0x05:
        subtype, value, offset = decode_binary_value(data, offset, end, python_only)
    elif type_byte == 0x08:
        if offset >= end:
            raise BsonBrokenDataError(data)
        value = data[offset]
        offset += 1
        value = True if value else False
    elif type_byte == 0x09:
        ms, offset = read_int64(data, offset)
        value = datetime.fromtimestamp(ms / 1000.0, tz=timezone.utc)
    elif type_byte == 0x0A:
        value = None
    elif type_byte == 0x10:
        value, offset = read_int(data, offset)
    elif type_byte == 0x12:
        value, offset = read_int64(data, offset)
    else:
        raise BsonInvalidElementTypeError(type_byte)
    return value, offset

def skip_value(type_byte: int, data: bytes, offset: int, end: int, python_only: bool = False) -> int:
    if type_byte == 0x06:
        return offset
    if type_byte == 0x07:
        if offset + 12 > end:
            raise BsonBrokenDataError(data)
        return offset + 12
    if type_byte == 0x0B:
        _, offset = read_cstring(data, offset)
        _, offset = read_cstring(data, offset)
        return offset
    if type_byte == 0x0C:
        _, offset = read_string(data, offset, end)
        if offset + 12 > end:
            raise BsonBrokenDataError(data)
        return offset + 12
    if type_byte == 0x0D:
        _, offset = read_string(data, offset, end)
        return offset
    if type_byte == 0x0E:
        _, offset = read_string(data, offset, end)
        return offset
    if type_byte == 0x0F:
        strlen, offset = read_int(data, offset)
        end_code = offset + strlen
        if end_code > end:
            raise BsonBrokenDataError(data)
        offset = end_code
        _, offset = decode_document(data, offset, python_only, keep_types=False, nt_types=None)
        return offset
    if type_byte == 0x11:
        if offset + 8 > end:
            raise BsonBrokenDataError(data)
        return offset + 8
    if type_byte == 0x13:
        if offset + 16 > end:
            raise BsonBrokenDataError(data)
        return offset + 16
    if type_byte in (0x7F, 0xFF):
        return offset
    raise BsonInvalidElementTypeError(data)

def decode_binary_value(data: bytes, offset: int, end: int, python_only: bool = False, name: str | None = None)\
        -> tuple[int, bytes, int]:
    length, offset = read_int(data, offset)
    if offset >= end:
        raise BsonBrokenDataError(data)
    if offset >= len(data):
        raise BsonBrokenDataError(data)
    subtype = data[offset]
    offset += 1
    if not (0 <= subtype <= 9 or 128 <= subtype <= 255):
        raise BsonInvalidBinarySubtypeError(subtype)
    if python_only and subtype != 0:
        if not (name == "__metadata__" and subtype == 128):
            raise BsonInvalidBinarySubtypeError(subtype)
    if offset + length > end:
        raise BsonBrokenDataError(data)
    raw = data[offset: offset + length]
    offset += length
    return subtype, bytes(raw), offset

def decode_document(data: bytes, offset: int, python_only: bool = False, keep_types: bool = False,
                    nt_types: dict[str, Any] | None = None) -> tuple[dict[str, Any], int]:
    length, offset = read_int(data, offset)

    if length < 5:
        raise BsonIncorrectSizeError(data)

    end = offset + length - 4
    if end > len(data):
        raise BsonBrokenDataError(data)

    result: dict[str, Any] = {}
    allowed_types = {0x01, 0x02, 0x03, 0x04, 0x05, 0x08, 0x09, 0x0A, 0x10, 0x12}
    normal_types = {0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0x0C,
                    0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x13, 0x7F, 0xFF}
    key_order: list[str] = []
    metadata_tags: list[str] | None = None

    while offset < end - 1:
        type_byte = data[int(offset)]
        if type_byte not in normal_types:
            raise BsonInvalidElementTypeError(data)
        offset = int(offset) + 1
        try:
            name, offset = read_cstring(data, offset)
        except BsonBadStringDataError as e:
            raise BsonBadKeyDataError(data) from e

        if type_byte in allowed_types:
            if type_byte == 0x05:
                subtype, value, offset = decode_binary_value(data, offset, end, python_only, name=name)
                if subtype == 0:
                    if name in result:
                        raise BsonRepeatedKeyDataError(name)
                    result[name] = value
                    key_order.append(name)
                elif keep_types and name == "__metadata__" and subtype == 128:
                    if value and value[0] == 0:
                        meta_bson = value[1:]
                        meta_doc = unmarshal(meta_bson)
                        children_str = meta_doc.get("children", "")
                        if isinstance(children_str, str):
                            if children_str == "":
                                metadata_tags = []
                            else:
                                metadata_tags = children_str.split(":")
                        else:
                            metadata_tags = None
                        types_info = meta_doc.get("types")
                        self_tag = meta_doc.get("self")
                        if isinstance(types_info, dict) and nt_types is not None:
                            nt_types.update(types_info)
                        if isinstance(self_tag, str) and nt_types is not None:
                            nt_types["__root_self__"] = self_tag
                    else:
                        meta_str = value.decode("utf-8")
                        if meta_str == "":
                            metadata_tags = []
                        else:
                            metadata_tags = meta_str.split(":")
            else:
                if name in result:
                    raise BsonRepeatedKeyDataError(name)
                value, offset = decode_value(type_byte, data, offset, end, python_only, keep_types, nt_types)
                result[name] = value
                key_order.append(name)
        else:
            if python_only:
                raise BsonInvalidElementTypeError(type_byte)
            offset = skip_value(type_byte, data, offset, end, python_only)

    if offset != end - 1 or data[offset] != 0:
        raise BsonBrokenDataError(data)
    offset += 1

    if keep_types and metadata_tags is not None:
        n = min(len(key_order), len(metadata_tags))
        for i in range(n):
            key = key_order[i]
            tag = metadata_tags[i]
            if not tag:
                continue
            val = result[key]
            if tag == "tuple" and isinstance(val, list):
                result[key] = tuple(val)
            elif tag == "bytearray" and isinstance(val, bytes):
                result[key] = bytearray(val)
            elif tag.startswith("nt-") and isinstance(val, dict):
                NT = None
                if nt_types is not None:
                    NT = get_namedtuple_class_from_nt_types(tag, nt_types)
                if NT is None:
                    result[key] = PendingNT(tag, val)
                    continue
                info = nt_types.get(tag) if nt_types is not None else None
                if isinstance(info, dict):
                    fields = info.get("fields")
                else:
                    fields = None
                if not isinstance(fields, list):
                    result[key] = val
                    continue
                args = [val[f] for f in fields]
                result[key] = NT(*args)

    return result, offset

def fix_pending_nt(obj: Any, nt_types: dict[str, Any]) -> Any:
    if isinstance(obj, PendingNT):
        NT = get_namedtuple_class_from_nt_types(obj.type_id, nt_types)
        if NT is None:
            return obj.value

        info = nt_types.get(obj.type_id)
        fields = info.get("fields") if isinstance(info, dict) else None
        val = obj.value
        if not isinstance(fields, list):
            return val

        if isinstance(val, dict):
            val = {k: fix_pending_nt(v, nt_types) for k, v in val.items()}
        elif isinstance(val, list):
            val = [fix_pending_nt(v, nt_types) for v in val]
        elif isinstance(val, tuple):
            val = tuple(fix_pending_nt(v, nt_types) for v in val)
        args = [val[f] for f in fields]
        return NT(*args)


    if is_namedtuple_instance(obj):
        cls = obj.__class__
        field_names = getattr(cls, "_fields", ())
        values = [fix_pending_nt(getattr(obj, name), nt_types) for name in field_names]
        return cls(*values)

    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            obj[k] = fix_pending_nt(v, nt_types)
        return obj

    if isinstance(obj, list):
        for i, v in enumerate(obj):
            obj[i] = fix_pending_nt(v, nt_types)
        return obj

    if isinstance(obj, tuple):
        return tuple(fix_pending_nt(v, nt_types) for v in obj)

    return obj


def unmarshal(data:bytes) -> dict[str, Any]:
    return Mapper().unmarshal(data)

