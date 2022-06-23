import json
import re
import typing

__all__ = [
    'is_int', 'is_float', 'is_list', 'is_dict', 'is_tuple', 'is_bool',
    'str2int', 'str2float', 'str2digit', 'str2bool', 'str2iter',
    'comma_separated_str2list', 'query_str2dict',
    'is_json_str'
]

# Notice: Following regex patterns are not accurate, may cause unexpected errors

REGEX_INT = r'^-?\d+$'
REGEX_FLOAT = r'^-?\d+\.\d+$'
REGEX_LIST = r'^\[.*?\]$'
REGEX_DICT = r'^({[\"\'].*?[\"\'].*?:.*})'
REGEX_TUPLE = r'^(\(.*?\)|\(\))$'
REGEX_BOOL = r'^(true|false)'


def is_int(obj):
    if isinstance(obj, str):
        return bool(re.match(REGEX_INT, obj))
    elif isinstance(obj, int):
        return True
    return False


def is_float(obj: typing.Union[float, str]):
    if isinstance(obj, str):
        return bool(re.match(REGEX_FLOAT, obj))
    elif isinstance(obj, float):
        return True
    return False


def is_list(obj: typing.Union[list, str], json_required=True):
    if isinstance(obj, str) and re.match(REGEX_LIST, obj):
        if json_required:
            try:
                json.loads(obj)
            except json.JSONDecodeError:
                return False
        return True
    elif isinstance(obj, list):
        return True
    return False


def is_dict(obj, json_required=True):
    if isinstance(obj, str) and re.match(REGEX_DICT, obj):
        if json_required:
            try:
                json.loads(obj)
            except json.JSONDecodeError:
                return False
        return True
    elif isinstance(obj, dict):
        return True
    return False


def is_tuple(obj):
    if isinstance(obj, tuple):
        return True
    elif isinstance(obj, str) and re.match(REGEX_TUPLE, obj):
        return True
    return False


def is_bool(string, strict=True):
    flags = 0
    if not strict:
        flags = re.IGNORECASE
    return bool(re.match(REGEX_BOOL, string, flags=flags))


def str2int(string, default=None, silent=False):
    """Raise exceptions if default is None"""
    if isinstance(string, int):
        return string
    elif isinstance(string, str):
        if is_int(string):
            return int(string)
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2float(string, default=None, silent=False) -> float:
    """Raise exceptions if default is None"""
    if isinstance(string, float):
        return string
    elif isinstance(string, str):
        if re.match(r'^-?\d+\.?\d*$', string):
            return float(string)
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2digit(string, default=None):
    """
    String to int or float
    """
    if isinstance(string, (int, float)):
        return string
    elif isinstance(string, str):
        if is_int(string):
            return str2int(string, default=default)
        elif re.match(REGEX_FLOAT, string):
            return str2float(string, default=default)


def str2bool(string, default: bool = None, silent=False):
    """
    str to bool
    """
    if isinstance(string, bool):
        return string
    elif isinstance(string, str):
        if string in ('true', 'True'):
            return True
        elif string in ('false', 'False'):
            return False
        else:
            if default is not None:
                return default
            if not silent:
                raise ValueError
    else:
        if default is not None:
            return default
        if not silent:
            raise TypeError


def str2iter(string):
    """
    Turn string to list, tuple, set or str
    """
    if not isinstance(string, str):
        return string
    if is_list(string) or is_dict(string) or is_tuple(string):
        return eval(string)
    return string


def comma_separated_str2list(string, default=None):
    if not string:
        return default
    return string.split(',')


def query_str2dict(string, default=None):
    """
    queryset查询字符串转为字典
    """
    if not string:
        return default

    # 逗号隔开的条件，转成列表
    # 如 name=hello,id__in=1,2,3,datetime__range=2022-01-10T09:00:00Z,2022-02-01T09:00:00Z
    # 转为 ['name=hello', 'id__in=1,2,3', 'datetime__range=2022-01-10T09:00:00Z,2022-02-01T09:00:00Z']
    # 注意，条件中可能有逗号
    result_list = list()
    items = [s for s in string.split(',')]
    for i, item in enumerate(items):
        if not item:
            continue
        split_items = item.split('=')
        if len(split_items) > 2:
            raise ValueError
        elif len(split_items) == 1:
            if len(result_list) > 0:
                # id__in=1,2,3
                result_list[-1] += f',{split_items[0]}'
            else:
                # 1,2,3
                raise ValueError
        else:
            result_list.append(item)

    # 组合为条件字典
    result_dict = dict()
    for item in result_list:
        try:
            k, v = item.split('=')
        except ValueError:
            raise
        result_dict.update({k: v})
    return result_dict


def is_json_str(raw_str):
    if isinstance(raw_str, str):
        try:
            json.loads(raw_str)
        except ValueError:
            return False
        return True
    else:
        return False
