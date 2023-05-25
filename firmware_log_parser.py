"""
This script parse firmware log
Usage
"""
import getopt
import os.path
import re
import sys

import numpy as np
import pandas as pd
from typing import List

from xml.dom.minidom import parse
import xml.dom.minidom


def usage() -> None:
    """

    :return:
    :rtype:
    """
    pass


#  1. open .log
def read_log_file(file_link: str) -> str:
    """

    :param file_link:
    :type file_link:
    :return:
    :rtype:
    """
    if not os.path.isfile(file_link):
        usage()
        exit(1)

    with open(file_link, 'r') as file:
        data = file.read()

    return data


def remove_first_bytes(log: List[str], number_bytes: int) -> List[str]:
    if log and type(log) is list and type(number_bytes) is int and 0 < number_bytes < len(log):
        for i in range(number_bytes):
            log.pop(0)

    return log


def print_hexadecimal(log: np.array) -> None:
    if log and type(log) is np.array:
        for i in log:
            for j in i:
                print(hex(int(j)), end=',')
            print()


def split_log(log: List[str], length_of_line: int = 20) -> List[List[str]]:
    bytes_in_log_line = 20

    if log and type(log) is list and type(length_of_line) is int:
        return [log[i:i + bytes_in_log_line] for i in range(0, len(log), length_of_line)]


# Entry point
required_tags = []
opts = []
args = ""
nibble_size = 4

# parse command-line:
try:
    opts, args = getopt.getopt(sys.argv[1:], "fx", longopts=['lof-file', 'xml-events'])
except getopt.GetoptError as err:
    # log.e(err)
    print("Error in get opt")
    usage()

for opt, arg in opts:
    if opt in ('-h', '--help'):
        usage()
    elif opt in ('-f', '--lof-file'):
        pass
    elif opt in ('-x', '--xml-events'):
        pass

if len(args) != 1:
    usage()

#  remove_words(arg...)
logs_str = read_log_file("d457_fw_lose_vc.log")

# remove all except numbers and ','
logs_str = re.sub("[^0-9,]", "", logs_str)

logs_list = logs_str.split(',')

logs_list = remove_first_bytes(logs_list, 4)
logs_matrix = split_log(logs_list)

# create numpy array
logs_np = np.array(logs_matrix)

# remove rows that contain only zeroes
logs_np = logs_np[~np.all(logs_np == '0', axis=1)]

# print(logs_np)

# Open XML document using minidom parser
DOMTree = xml.dom.minidom.parse("HWLoggerEventsDS5.xml")
xml_data = DOMTree.documentElement


def print_log_headers() -> None:
    """
    Print headers to console
    :return: None
    """
    print_format_log_line('Seq.', 'File name', '?', 'Thread name', 'Sev.',
                          'Line', 'Timestamp', 'Delta timestamp', 'Description')


def get_file_name_from_xml(_id: str) -> str:
    """
    This function get file name from xml data by file id
    :param _id: file id number
    :type _id: str
    :return: file name
    :rtype: str
    """
    global xml_data

    if type(_id) is str:
        files = xml_data.getElementsByTagName('File')

        for f in files:
            if f.hasAttribute('id') and f.hasAttribute('Name'):
                file_id_xml = f.getAttribute('id')
                if file_id_xml == _id:
                    return f.getAttribute('Name')

    return 'File not found'


def get_thread_name_from_xml(tread_id: int) -> str:
    """
    Scan xml for thread name according given thread id
    :param tread_id: thread id
    :type tread_id: int
    :return: thread name
    :rtype str
    """
    global xml_data

    if type(thread_id) is int:
        threads = xml_data.getElementsByTagName('Thread')

        for t in threads:
            if t.hasAttribute('id') and t.hasAttribute('Name'):
                thread_id_xml = t.getAttribute('id')
                if thread_id_xml == str(tread_id):
                    return t.getAttribute('Name')

    return 'Thread not found'


def get_format_string_from_xml(_id: str) -> str:
    """
    This function get format string from xml data by event id
    :param _id: event id
    :type _id: str
    :return: format string
    :rtype: str
    """
    global xml_data

    if type(_id) is str:
        events = xml_data.getElementsByTagName('Event')

        for event in events:
            if event.hasAttribute('id') and event.hasAttribute('format'):
                id_xml = event.getAttribute('id')
                if id_xml == _id:
                    return event.getAttribute('format')

    return 'Event not found'


def get_number_of_arguments_from_xml(_id: str) -> int:
    """
    This function get amount of arguments in format by event id from xml file
    :param: event_id: event id
    :type: event_id: str
    :return: amount of parameters
    :rtype: int
    """
    global xml_data

    if type(_id) is str:
        events = xml_data.getElementsByTagName('Event')

        for event in events:
            if event.hasAttribute('id') and event.hasAttribute('numberOfArguments'):
                id_xml = event.getAttribute('id')
                if id_xml == _id:
                    return int(event.getAttribute('numberOfArguments'))

    return 0


def read_byte(dword: int, position: str) -> int:
    """
    This function read high or low byte from a double word
    :param position: high or low byte
    :type position: str
    :param dword: double word
    :type dword: int
    :return: bytee
    :rtype: int
    """
    if position == 'high':
        # cut HIGH word from there with event id
        low_byte = dword & 0b0000_0000_1111_1111_0000_0000_0000_0000
        high_byte = dword & 0b1111_1111_0000_0000_0000_0000_0000_0000

        # swap high and low bytes in the word
        low_byte >>= (nibble_size * 2)  # 2 nibbles (4 bits)
        high_byte >>= (nibble_size * 6)  # 6 nibbles (4 bits)

    elif position == 'low':
        low_byte = dword & 0b0000_0000_0000_0000_0000_0000_1111_1111
        high_byte = dword & 0b0000_0000_0000_0000_1111_1111_0000_0000

        # swap high and low bytes in the word
        low_byte <<= (nibble_size * 2)  # 2 nibbles (4 bits)
        high_byte >>= (nibble_size * 2)  # 2 nibbles (4 bits)

    else:
        return 0

    byte = high_byte | low_byte

    return byte


def read_magic_number(dword: int) -> int:
    """
    Read magic number from double word. Not in use
    :param dword: double word
    :type dword: int
    :return: magic number
    :rtype: int
    """
    # get 8 bits according a mask
    number = dword & 0b1111_1111_0000_0000_0000_0000_0000_0000
    # move the bits to the right side
    number >>= (nibble_size * 6)  # 6 nibbles (4 bits)

    return number


def read_thread_id(dword: int) -> int:
    """
    Read thread id from double word
    :param dword: double word
    :type dword: int
    :return: thread id
    :rtype: int
    """
    # get 3 bits according a mask
    thread_id_ = dword & 0b0000_0000_1110_0000_0000_0000_0000_0000
    # move the bits to the right side
    thread_id_ >>= (nibble_size * 5 + 1)  # 5 nibbles (4 bits)

    return thread_id_


def read_severity(dword: int) -> int:
    """
    Read severity number from double word
    :param dword: double word
    :type dword: int
    :return: severity value
    :rtype: int
    """
    # get 5 bits according a mask
    sev = dword & 0b0000_0000_0001_1111_0000_0000_0000_0000
    # move the bits to the right side
    sev >>= (nibble_size * 4)  # 4 nibbles (4 bits)

    return sev


def read_file_id(dword: int) -> int:
    """
    Read file id number from double word
    :param dword: double word
    :type dword: int
    :return: file id value
    :rtype: int
    """
    # get 3 bits according a mask
    low_byte = dword & 0b0000_0000_0000_0000_0000_0000_1110_0000
    # get 8 bits according a mask
    high_byte = dword & 0b0000_0000_0000_0000_1111_1111_0000_0000

    # swap high and low bytes in the word
    low_byte <<= 3  # (3 bits)
    high_byte >>= (nibble_size * 2)  # 2 nibbles (4 bits)

    f_id = high_byte | low_byte
    return f_id


def read_group_id(dword: int) -> int:
    """
    Read group id number from double word
    :param dword: double word
    :type dword: int
    :return: group id value
    :rtype: int
    """
    # get 5 bits according a mask
    return dword & 0b0000_0000_0000_0000_0000_0000_0001_1111


def read_metadata(bytes_: pd.Series) -> int:
    """
    Read metadata value from double word
    :param bytes_: pandas byte list
    :type bytes_: ps.Series
    :return: metadata
    :rtype: int
    """
    global byte_pointer
    shift_bits = 24
    size_of_byte = 8
    bytes_in_dword = 4

    byte = 0

    # This loop reverse bytes in double word
    for i in range(bytes_in_dword):
        temp = int(bytes_[byte_pointer + 3 - i])  # start read bytes from the end of the Low byte
        temp <<= shift_bits
        byte += temp

        shift_bits -= size_of_byte

    byte_pointer += bytes_in_dword * size_of_byte
    return byte


def read_line(dword: int) -> int:
    """
    Read line number from double word
    :param dword: double word
    :type dword: int
    :return: line value
    :rtype: int
    """
    # get 4 bits according a mask
    low_byte = dword & 0b0000_0000_0000_0000_0000_0000_0000_1111
    # get 8 bits according a mask
    high_byte = dword & 0b0000_0000_0000_0000_1111_1111_0000_0000

    # swap high and low bytes in the word
    low_byte <<= (nibble_size * 2)  # 2 nibbles (4 bits)
    high_byte >>= (nibble_size * 2)  # 2 nibbles (4 bits)

    byte = high_byte | low_byte

    return byte


def read_sequence(dword: int) -> int:
    """
    Read sequence number from double word
    :param dword: double word
    :type dword: int
    :return: sequence value
    :rtype: int
    """
    # get 4 bits according a mask
    s = dword & 0b0000_0000_0000_0000_0000_0000_1111_0000
    # move the bits to the right side
    s >>= nibble_size

    return s


def get_double_word(bytes_: pd.Series) -> int:
    """
    This function return double word
    :param bytes_: bytes in row log
    :type bytes_: pd.Series
    :return: double word
    :rtype: int
    """
    global byte_pointer
    shift_bits = 24
    size_of_byte = 8
    bytes_in_dword = 4

    byte = 0

    for i in range(bytes_in_dword):
        temp = int(bytes_[byte_pointer])
        temp <<= shift_bits
        byte += temp

        shift_bits -= size_of_byte
        byte_pointer += 1

    return byte


def get_description_string(format_str: str, number_args: int, var_1, var_2, var_3) -> str:
    """
    This function build description string
    :param format_str: format string
    :type format_str: str
    :param number_args: number of arguments that string expecting
    :type number_args: int
    :param var_1:
    :type var_1:
    :param var_2:
    :type var_2:
    :param var_3:
    :type var_3:
    :return: final description string
    :rtype: int
    """
    if number_args == 0:
        string = format_str
        return string
    elif number_args == 1:
        string = format_str.format(var_1)
        return string
    elif number_args == 2:
        string = format_str.format(var_1, var_2)
        return string
    elif number_args == 3:
        string = format_str.format(var_1, var_2, var_3)
        return string
    else:
        return format_str + " (Wrong number of arguments read from the log line!)"


def print_format_log_line(seq_id, file_name: str, num1, thread_n: str, num2, timestamp_line, timestamp, delta_timestamp, description):
    """
    Prints string of parsed log line according format
    :param seq_id:
    :type seq_id:
    :param file_name:
    :type file_name:
    :param num1:
    :type num1:
    :param thread_n:
    :type thread_n:
    :param num2:
    :type num2:
    :param timestamp_line:
    :type timestamp_line:
    :param timestamp:
    :type timestamp:
    :param delta_timestamp:
    :type delta_timestamp:
    :param description:
    :type description:
    :return:
    :rtype:
    """
    print('{:<6}{:<30}{:<6}{:<15}{:<6}{:<6}{:<15}{:<15}{:<150}'.format(seq_id,
                                                                       file_name,
                                                                       num1,
                                                                       thread_n,
                                                                       num2,
                                                                       timestamp_line,
                                                                       timestamp,
                                                                       str(delta_timestamp)[0: 7: 1],
                                                                       description))


def calculate_delta_timestamp(timestamp, last_timestamp) -> int:
    """
    Calculates delta timestamp between previous and current timestamp
    :param timestamp:
    :type timestamp:
    :param last_timestamp:
    :type last_timestamp:
    :return: delta timestamp
    :rtype: int
    """
    timestamp_factor = 0.00001

    if not last_timestamp:
        return 0
    else:
        return (timestamp - last_timestamp) * timestamp_factor


df = pd.DataFrame(logs_np)

last_timestamp = 0

print_log_headers()

for index, row_bytes in df.iterrows():
    byte_pointer = 0

    dword1 = get_double_word(row_bytes)
    # print('dword1 ' + hex(dword1))
    # print('dword1 ' + bin(dword1))

    dword2 = get_double_word(row_bytes)
    # print('dword2 ' + hex(dword2))
    # print('dword2 ' + bin(dword2))

    dword3 = get_double_word(row_bytes)
    # print('dword3 ' + hex(dword3))
    # print('dword3 ' + bin(dword3))

    dword4 = get_double_word(row_bytes)
    # print('dword4 ' + hex(dword4))
    # print('dword4 ' + bin(dword4))

    dword5 = read_metadata(row_bytes)
    # print('dword5 ' + hex(dword5))
    # print('dword5 ' + bin(dword5))

    # double word 1 scope
    # TODO - what is a usage of magic_number? (8 bits)

    magic_number = read_magic_number(dword1)
    thread_id = read_thread_id(dword1)
    severity = read_severity(dword1)
    file_id = read_file_id(dword1)
    #  TODO - what is a usage of group_id? (5 bits)
    group_id = read_group_id(dword1)

    # double word 2 scope
    event_id = read_byte(dword2, 'high')
    line = read_line(dword2)
    sequence = read_sequence(dword2)

    # double word 3 scope
    data_1 = read_byte(dword3, 'high')
    data_2 = read_byte(dword3, 'low')

    # double word 4 scope
    data_3 = read_byte(dword4, 'high')

    # double word 5 scope
    timestamp = dword5

    file_name = get_file_name_from_xml(str(file_id))
    thread_name = get_thread_name_from_xml(thread_id)
    delta_timestamp = calculate_delta_timestamp(timestamp, last_timestamp)
    last_timestamp = timestamp

    number_arguments = get_number_of_arguments_from_xml(str(event_id))
    format_string = get_format_string_from_xml(str(event_id))
    description_string = get_description_string(format_string, number_arguments, data_1, data_2, data_3)

    print_format_log_line(sequence, file_name, 0, thread_name, severity, line, timestamp, delta_timestamp, description_string)
