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
DOMTree = xml.dom.minidom.parse("a.xml")
xml_data = DOMTree.documentElement


def get_file_name(file_id: str) -> str:
    """
    This function get file name from xml data by file id
    :param file_id: file id number
    :type file_id: str
    :return: file name
    :rtype: str
    """
    global xml_data

    if type(file_id) is str:
        files = xml_data.getElementsByTagName('File')

        for f in files:
            if f.hasAttribute('id') and f.hasAttribute('Name'):
                file_id_xml = f.getAttribute('id')
                if file_id_xml == file_id:
                    return f.getAttribute('Name')

    return 'File not found'


def get_thread_name(tread_id: int):
    global xml_data

    if type(thread_id) is int:
        threads = xml_data.getElementsByTagName('Thread')

        for t in threads:
            if t.hasAttribute('id') and t.hasAttribute('Name'):
                thread_id_xml = t.getAttribute('id')
                if thread_id_xml == str(tread_id):
                    return t.getAttribute('Name')

    return 'Thread not found'


def get_format_string(event_id: str) -> str:
    """
    This function get format string from xml data by event id
    :param event_id: event id
    :type event_id: str
    :return: format string
    :rtype: str
    """
    global xml_data

    if type(event_id) is str:
        events = xml_data.getElementsByTagName('Event')

        for event in events:
            if event.hasAttribute('id') and event.hasAttribute('format'):
                id_xml = event.getAttribute('id')
                if id_xml == event_id:
                    return event.getAttribute('format')

    return 'Event not found'


def get_number_of_arguments(event_id: str) -> int:
    """
    This function get amount of arguments in format by event id from xml file
    :param: event_id: event id
    :type: event_id: str
    :return: amount of parameters
    :rtype: int
    """
    global xml_data

    if type(event_id) is str:
        events = xml_data.getElementsByTagName('Event')

        for event in events:
            if event.hasAttribute('id') and event.hasAttribute('numberOfArguments'):
                id_xml = event.getAttribute('id')
                if id_xml == event_id:
                    return int(event.getAttribute('numberOfArguments'))

    return 0


def bytes(integer):
    return divmod(integer, 0x100)


def read_byte(dword: int, position: str) -> int:
    """
    This function read high or low byte from a double word
    :param position:
    :type position:
    :param dword: double word
    :type dword: int
    :return: event id
    :rtype: int
    """
    if position == 'high':
        # cut HIGH word from there with event id
        low_byte = dword & 0b0000_0000_1111_1111_0000_0000_0000_0000
        high_byte = dword & 0b1111_1111_0000_0000_0000_0000_0000_0000

        # swap high and low bytes in the word
        low_byte >>= (4 * 2)  # 2 octal (4 bits)
        high_byte >>= (4 * 6)  # 6 octal (4 bits)

    elif position == 'low':
        low_byte = dword & 0b0000_0000_0000_0000_0000_0000_1111_1111
        high_byte = dword & 0b0000_0000_0000_0000_1111_1111_0000_0000

        # swap high and low bytes in the word
        low_byte <<= (4 * 2)  # 2 octal (4 bits)
        high_byte >>= (4 * 2)  # 2 octal (4 bits)

    else:
        return 0

    byte = high_byte | low_byte

    return byte


def read_metadata(bytes: pd.Series) -> int:
    global byte_pointer
    shift_bits = 24
    size_of_byte = 8
    bytes_in_dword = 4

    byte = 0

    for i in range(4):
        temp = int(bytes[byte_pointer + 3 - i])  # start read bytes from the end of the Low byte
        temp <<= shift_bits
        byte += temp

        shift_bits -= size_of_byte
        # byte_pointer += 1
        # print(hex(int(byte)), end=' | ')

    byte_pointer += bytes_in_dword * size_of_byte
    return byte


def read_line(dword: int) -> int:
    low_byte = dword & 0b0000_0000_0000_0000_0000_0000_0000_1111
    high_byte = dword & 0b0000_0000_0000_0000_1111_1111_0000_0000

    # swap high and low bytes in the word
    low_byte <<= (4 * 2)  # 2 octal (4 bits)
    high_byte >>= (4 * 2)  # 2 octal (4 bits)

    byte = high_byte | low_byte

    return byte


def get_double_word(bytes: pd.Series) -> int:
    """
    This function return double word
    :param bytes: bytes in row log
    :type bytes: pd.Series
    :return: double word
    :rtype: int
    """
    global byte_pointer
    shift_bits = 24
    size_of_byte = 8

    byte = 0

    for i in range(4):
        temp = int(bytes[byte_pointer])
        temp <<= shift_bits
        byte += temp

        shift_bits -= size_of_byte
        byte_pointer += 1
        # print(hex(int(byte)), end=' | ')

    return byte


def get_description_string(format_str: str, number_args: int, var_1, var_2, var_3) -> str:
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


def print_format_log_line(counter, file_name: str, num1, thread_n: str, num2, timestamp_line, timestamp, delta_timestamp, description):
    print('{:<6}{:<30}{:<6}{:<15}{:<6}{:<6}{:<15}{:<15}{:<150}'.format(counter,
                                                                       file_name,
                                                                       num1,
                                                                       thread_n,
                                                                       num2,
                                                                       timestamp_line,
                                                                       timestamp,
                                                                       str(delta_timestamp)[0: 7: 1],
                                                                       description))


def shift_right_until_not_zeros(binary_number: int) -> int:
    """
    Don't USE IT!
    :param binary_number:
    :type binary_number:
    :return:
    :rtype:
    """
    if type(binary_number) is not int or binary_number == 0:
        return 0

    len = binary_number.bit_length()

    while binary_number & 0b1 != 1 and len > 7:
        binary_number >>= 1
        len = binary_number.bit_length()

    return binary_number


def calculate_delta_timestamp(timestamp, last_timestamp) -> tuple:
    timestamp_factor = 0.00001

    if not last_timestamp:
        return 0, timestamp
    else:
        return (timestamp - last_timestamp) * timestamp_factor, timestamp


df = pd.DataFrame(logs_np)

last_timestamp = 0
hexa_counter = 2

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
    magic_number = dword1 & 0b1111_1111_0000_0000_0000_0000_0000_0000
    magic_number >>= (4 * 6)  # 6 octal (4 bits)

    severity = dword1 & 0b0000_0000_1111_1000_0000_0000_0000_0000
    severity >>= (4 * 4 + 3)  # 4 octal (4 bits)

    thread_id = dword1 & 0b0000_0000_1110_0000_0000_0000_0000_0000
    thread_id >>= (4 * 5 + 1)  # 4 octal (4 bits)    print(thread_id)

    # TODO Understand why we need use only 8 bites and not 11 bits?
    file_id = dword1 & 0b0000_0000_0000_0000_1111_1111_1110_0000
    file_id >>= (4 + 4)  # 6 octal (4 bits)


    group_id = dword1 & 0b0000_0000_0000_0000_0000_0000_0001_1111

    # double word 2 scope
    event_id = read_byte(dword2, 'high')

    line = read_line(dword2)
    # line >>= 4  # 4 octal

    sequence = dword2 & 0b0000_0000_0000_0000_0000_0000_0000_1111

    # double word 3 scope
    data_1 = read_byte(dword3, 'high')
    data_2 = read_byte(dword3, 'low')

    # double word 4 scope
    data_3 = read_byte(dword4, 'high')

    # double word 5 scope
    timestamp = dword5

    file_name = get_file_name(str(file_id))
    thread_name = get_thread_name(thread_id)
    delta_timestamp, last_timestamp = calculate_delta_timestamp(timestamp, last_timestamp)

    number_arguments = get_number_of_arguments(str(event_id))
    format_string = get_format_string(str(event_id))
    description_string = get_description_string(format_string, number_arguments, data_1, data_2, data_3)


    print_format_log_line(hexa_counter, file_name, 0, thread_name, 0, line, timestamp, delta_timestamp, description_string)

    if hexa_counter == 0xF:
        hexa_counter = 0
    else:
        hexa_counter += 1

