import argparse
import grp
import os.path
import pwd
import stat
import sys
from collections import defaultdict
from datetime import datetime

from cli_formatter.output_formatting import colorize_string, Color, error, warning
from dateutil import tz

from .libary import get_alternate_data_streams_recursively, get_alternate_data_streams_of_file, path_is_an_ntfs_filesystem

WARNING_TEXT_WRONG_FILE_SYSTEM_PATH = 'Path is not under a NTFS filesystem partition - Alternate Data Streams can not be detected. Ensure that the mounted partition is mounted as NTFS. Use the -o streams_interface=windows option when using the mount command.'
WARNING_TEXT_WRONG_FILE_SYSTEM_BASE_PATH = 'The provided path is not under a NTFS filesystem partition - Alternate Data Streams can only be detected under a mounted NTFS partition. Use the -o streams_interface=windows option when using the mount command. If an NTFS filesystem is mounted to a subfolder lad will detect Alternate Data Streams in this folder.'


def __parse_cli_arguments():
    flags_to_parse = list()
    path = None
    for x in sys.argv[1:]:
        if not x.startswith('-') and path is None:
            path = x
        else:
            flags_to_parse.append(x)
    # if no path was specified in the arguments take the current directory as default
    if path is None:
        path = '.'
    return flags_to_parse, path


def __generate_output_single_file(arguments, path_to_file: str, file_name: str, file_info, alternate_data_streams: list) -> list:
    if arguments.filter_files_with_ads and len(alternate_data_streams) == 0:
        return list()

    file_permission_string = stat.filemode(file_info.st_mode)

    if arguments.numeric_uid_gid:
        owner = str(file_info.st_uid)
        group = str(file_info.st_gid)
    else:
        owner = pwd.getpwuid(file_info.st_uid).pw_name
        group = grp.getgrgid(file_info.st_gid).gr_name

    # file size
    if arguments.human_readable:
        file_size = __bytes_to_human_readable(file_info.st_size)
    else:
        file_size = str(file_info.st_size)

    # time of last modification
    time_last_change = file_info.st_mtime  # seconds since epoch in UTC
    time_last_change = datetime.fromtimestamp(time_last_change)
    time_last_change = time_last_change.astimezone(tz.tzlocal())  # convert time to local time zone
    if arguments.full_time:
        time_last_change_new = [time_last_change.strftime('%Y-%m-%d %T.{:.9f} %z'.format(file_info.st_mtime))]
    else:
        time_last_change_new = ['{}.'.format(time_last_change.strftime('%e').rjust(2)),
                                time_last_change.strftime('%B'),
                                time_last_change.strftime('%Y'),
                                time_last_change.strftime('%H:%M')]

    # strip the first '/' of the file name
    if len(file_name) > 1:
        file_name = file_name[1:]

    output_list = list()

    # add the file itself
    output_list.append([file_permission_string, owner, group, file_size] + time_last_change_new + [file_name])

    # add alternate data streams
    for ads in alternate_data_streams:
        ads_file_stats = os.stat(path_to_file + ':' + ads)
        if arguments.human_readable:
            file_size = __bytes_to_human_readable(ads_file_stats.st_size)
        else:
            file_size = str(ads_file_stats.st_size)

        output_list.append([file_permission_string, owner, group, file_size] + time_last_change_new + [file_name + ':' + colorize_string(text=ads, color=Color.BLUE)])

    return output_list


def __bytes_to_human_readable(number_of_bytes: int) -> str:
    """ converts a number of bytes in a human readable string, e.g. 5,0K; 10,0M """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(number_of_bytes) < 1024.0:
            string_representation = "{:3.1f}".format(number_of_bytes)
            # remove trailing zeros
            if string_representation[-1] == '0':
                return string_representation[:-2] + unit
            return string_representation + unit
        number_of_bytes /= 1024.0
    return "{.1f}{}".format(number_of_bytes, 'Y')


def main():
    flags_to_parse, path = __parse_cli_arguments()

    parser = argparse.ArgumentParser(usage='lad [OPTION]... [FILE]...', description='Lists information about the FILEs (the current directory by default) including Alternate Data Streams.', add_help=False)
    parser.add_argument('-h', '--human-readable', dest="human_readable", help="print sizes like 1K 234M 2G etc.", action='store_true', default=False)
    parser.add_argument('--help', dest='help', help="prints the help text", action='store_true', default=False)
    parser.add_argument('-R', '--recursive', dest="recursive", help="list subdirectories recursively", action='store_true', default=False)
    parser.add_argument('--full-time', dest="full_time", help="Shows the complete timestamp", action='store_true', default=False)
    parser.add_argument('-n', '--numeric-uid-gid', dest="numeric_uid_gid", help="list numeric user and group IDs", action='store_true', default=False)
    parser.add_argument('-F', dest="filter_files_with_ads", help="Show only files which include Alternate Data Streams", action='store_true', default=False)
    parser.add_argument('--no-warning', dest="no_warning", help="Suppress warnings (e.g. if the filesystem is not NTFS)", action='store_true', default=False)

    parsed_arguments = parser.parse_args(flags_to_parse)

    if parsed_arguments.help:
        parser.print_help()
        exit()

    base_path = os.path.abspath(path)
    if not os.path.exists(base_path):
        error('Path "{}" does not exist'.format(path))
        exit()

    output = list()

    if os.path.isfile(path):  # the path points to a file
        # check the filesystem and collect the alternate data streams
        if path_is_an_ntfs_filesystem(path=base_path):
            alternate_data_streams = get_alternate_data_streams_of_file(path_to_file=base_path)
        else:
            alternate_data_streams = list()
            if not parsed_arguments.no_warning:
                warning(WARNING_TEXT_WRONG_FILE_SYSTEM_PATH)

        output.extend(__generate_output_single_file(arguments=parsed_arguments, path_to_file=base_path, file_name=path, file_info=os.stat(base_path), alternate_data_streams=alternate_data_streams))

    elif not parsed_arguments.recursive:  # the path points to a directory (recursive flag is not set)
        if path_is_an_ntfs_filesystem(path=base_path):
            search_alternate_data_streams = True
        else:
            search_alternate_data_streams = False
            if not parsed_arguments.no_warning:
                warning(WARNING_TEXT_WRONG_FILE_SYSTEM_PATH)

        for x in os.scandir(base_path):
            file_name = x.path.replace(base_path, '')
            file_info = x.stat()
            if search_alternate_data_streams and x.is_file():
                alternate_data_streams = get_alternate_data_streams_of_file(path_to_file=x.path)
            else:
                alternate_data_streams = list()

            generated_output = __generate_output_single_file(arguments=parsed_arguments, path_to_file=x.path, file_name=file_name, file_info=file_info, alternate_data_streams=alternate_data_streams)
            output.extend(generated_output)

    else:  # the path points to a directory (recursive flag is set)
        # to faster the scan apply getfattr recursively on the directory and parse the complete output

        if not parsed_arguments.no_warning and not path_is_an_ntfs_filesystem(base_path):
            warning(WARNING_TEXT_WRONG_FILE_SYSTEM_BASE_PATH)

        alternate_data_streams_dict = get_alternate_data_streams_recursively(path_to_directory=base_path)

        def scan_directory(path_to_dir):
            for x in os.scandir(path_to_dir):
                file_name = x.path.replace(base_path, '')
                try:
                    file_info = x.stat()
                except OSError:
                    warning(message='File {} could not be analyzed'.format(file_name))
                    continue

                alternate_data_streams = alternate_data_streams_dict.get(x.path, list())
                generated_output = __generate_output_single_file(arguments=parsed_arguments, path_to_file=x.path, file_name=file_name, file_info=file_info, alternate_data_streams=alternate_data_streams)
                output.extend(generated_output)

                if parsed_arguments.recursive and x.is_dir():
                    scan_directory(path_to_dir=x.path)

        scan_directory(path_to_dir=base_path)

    # Find maximum width of each column to print the table nicely
    max_width_for_each_column = defaultdict(int)
    for line in output:
        for i, cell in enumerate(line):
            max_width_for_each_column[i] = max(max_width_for_each_column[i], len(cell))

    for line in output:
        for i, cell in enumerate(line):
            if i == len(line) - 1:
                print(cell.ljust(max_width_for_each_column[i]), end='\n')
            elif i == 3:  # the file size has to be aligned to the right
                print(cell.rjust(max_width_for_each_column[i]), end=' ')
            else:
                print(cell.ljust(max_width_for_each_column[i]), end=' ')


if __name__ == '__main__':
    main()
