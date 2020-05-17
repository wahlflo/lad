import re
import subprocess
from collections import defaultdict
from typing import List, Dict

import psutil

REGEX_PATTERN_TO_PARSE_GETFATTR_OUTPUT = re.compile(r'ntfs\.streams\.list="(.*)"')


def path_is_an_ntfs_filesystem(path: str) -> bool:
    """ :returns True if the path points to an NTFS filesystem otherwise False """
    filesystem_type = __get_type_of_filesystem(path=path)
    # fuseblk is the name of an ntfs partition mounted  by the mount command
    if filesystem_type == 'ntfs' or filesystem_type == 'fuseblk':
        return True
    return False


def __get_type_of_filesystem(path: str) -> str:
    """ :returns the name of the filesystem """
    root_type = ""
    for part in psutil.disk_partitions():
        if part.mountpoint == '/':
            root_type = part.fstype
            continue
        if path.startswith(part.mountpoint):
            return part.fstype
    return root_type


def get_alternate_data_streams_recursively(path_to_directory: str) -> Dict[str, List[str]]:
    """
    returns a dict of files mapping to a list of Alternate Data Streams of each file
    only files which contain an ADS are represented in the dict to save memory
    :param path_to_directory: Path to the directory which should be scanned
    :return: dict mapping files to a list of Alternate Data Streams of each file
    """
    try:
        getfattr_output = subprocess.check_output('getfattr -Rn ntfs.streams.list "{}"'.format(path_to_directory.replace('"', '\\"')), stderr=subprocess.DEVNULL, shell=True, text=True)
    except subprocess.CalledProcessError as exc:
        getfattr_output = exc.output
    return __parse_getfattr_output(getfattr_output=getfattr_output)


def get_alternate_data_streams_of_file(path_to_file: str) -> list:
    """
    returns a list of Alternate Data Streams of the file
    :param path_to_file: Path to the file
    :return: list of Alternate Data Streams
    """
    try:
        getfattr_output = subprocess.check_output('getfattr -n ntfs.streams.list "{}"'.format(path_to_file.replace('"', '\\"')), stderr=subprocess.DEVNULL, shell=True, text=True)
    except subprocess.CalledProcessError as exc:
        getfattr_output = exc.output

    alternate_data_streams_dict = __parse_getfattr_output(getfattr_output=getfattr_output)
    return alternate_data_streams_dict.get(path_to_file, list())


def __parse_getfattr_output(getfattr_output: str) -> Dict[str, List[str]]:
    """ returns the names Alternate Data Streams extracted from the getfattr command output """
    result_dict = defaultdict(list)
    lines = getfattr_output.split('\n')
    line_index = 0
    number_of_lines = len(lines)
    while line_index < number_of_lines:
        line_to_scan = lines[line_index]
        if line_to_scan.startswith('#'):  # found a file in NTFS filesystem
            path_to_file = '/' + line_to_scan.strip('# file: ')
            # check next line if it contains
            line_with_ads_list = lines[line_index + 1]
            match = re.fullmatch(REGEX_PATTERN_TO_PARSE_GETFATTR_OUTPUT, line_with_ads_list)
            names_of_alternate_data_streams = match.group(1)
            if len(names_of_alternate_data_streams) > 0:
                result_dict[path_to_file] = [alternate_data_stream for alternate_data_stream in names_of_alternate_data_streams.split(r'\000')]
            line_index += 3
        else:
            line_index += 1
    return result_dict
