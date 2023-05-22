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
DOMTree = xml.dom.minidom.parse("HWLoggerEventsDS5.xml")
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

    if type(thread_id) is str:
        threads = xml_data.getElementsByTagName('Thread')

        for t in threads:
            if t.hasAttribute('id') and t.hasAttribute('Name'):
                thread_id_xml = t.getAttribute('id')
                if thread_id_xml == tread_id:
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


def get_double_word(bytes: pd.Series) -> int:
    """
    This function return double word
    :param bytes: bytes in row log
    :type bytes: pd.Series
    :return: double word
    :rtype: int
    """
    global byte_pointer

    lower_byte_1 = bytes[byte_pointer]
    # print(lower_byte_1)
    byte_pointer += 1
    lower_byte_2 = bytes[byte_pointer]
    # print(lower_byte_2)
    byte_pointer += 1

    higher_byte_1 = bytes[byte_pointer]
    byte_pointer += 1
    higher_byte_2 = bytes[byte_pointer]
    byte_pointer += 1

    # higher_byte_1 = bytes[byte_pointer]
    # byte_pointer += 1
    # higher_byte_2 = bytes[byte_pointer]
    # byte_pointer += 1
    # lower_byte_1 = bytes[byte_pointer]
    # byte_pointer += 1
    # lower_byte_2 = bytes[byte_pointer]
    # byte_pointer += 1

    return int(lower_byte_2 + lower_byte_1 + higher_byte_2 + higher_byte_1)
    # return int(lower_byte_1 + lower_byte_2 + higher_byte_1 + higher_byte_2)



def print_format_log_line(counter, file_name: str, num1, thread_n: str, num2, timestamp_line, timestamp, delta_timestamp, description):
    print('{:<6}{:<30}{:<6}{:<15}{:<6}{:<6}{:<15}{:<15}{:<150}'.format(counter, file_name, num1, 'TYPE', num2, timestamp_line, timestamp, 0.7777777, description))


def shift_right_until_not_zeros(binary_number: int) -> int:
    if type(binary_number) is not int or binary_number == 0:
        return 0

    while binary_number & 0b1 != 1:
        binary_number >>= 1

    return binary_number


def calculate_delta_timestamp(timestamp, last_timestamp) -> tuple:
    timestamp_factor = 0.00001

    if not last_timestamp:
        return 0, timestamp
    else:
        return (timestamp - last_timestamp) * timestamp_factor, timestamp


df = pd.DataFrame(logs_np)
print(df)

last_timestamp = 0
for index, row_bytes in df.iterrows():
    byte_pointer = 0

    dword1 = get_double_word(row_bytes)
    dword2 = get_double_word(row_bytes)
    dword3 = get_double_word(row_bytes)
    dword4 = get_double_word(row_bytes)
    dword5 = get_double_word(row_bytes)

    # double word 1 scope
    print('dword=', dword1)
    magic_number = dword1 & 0b1111_1111_0000_0000_0000_0000_0000_0000
    print('magic=', bin(magic_number))
    magic_number = shift_right_until_not_zeros(magic_number)
    print('shift=', bin(magic_number))
    print()

    severity = dword1 & 0b0000_0000_1111_1000_0000_0000_0000_0000
    severity = shift_right_until_not_zeros(severity)

    thread_id = dword1 & 0b0000_0000_0000_0111_0000_0000_0000_0000
    thread_id = shift_right_until_not_zeros(thread_id)

    file_id = dword1 & 0b0000_0000_0000_0000_1111_1111_1110_0000
    file_id = shift_right_until_not_zeros(file_id)

    group_id = dword1 & 0b0000_0000_0000_0000_0000_0000_0001_1111
    group_id = shift_right_until_not_zeros(group_id)

    # double word 2 scope
    event_id = dword2 & 0b1111_1111_1111_1111_0000_0000_0000_0000
    event_id = shift_right_until_not_zeros(event_id)

    line = dword2 & 0b0000_0000_0000_0000_1111_1111_1111_0000
    line = shift_right_until_not_zeros(line)

    sequence = dword2 & 0b0000_0000_0000_0000_0000_0000_0000_1111
    sequence = shift_right_until_not_zeros(sequence)

    # double word 3 scope
    data_1 = dword3 & 0b1111_1111_1111_1111_0000_0000_0000_0000
    data_1 = shift_right_until_not_zeros(data_1)

    data_2 = dword3 & 0b0000_0000_0000_0000_1111_1111_1111_1111
    data_2 = shift_right_until_not_zeros(data_2)

    # double word 4 scope
    data_3 = dword4

    # double word 5 scope
    timestamp = dword5

    delta_timestamp, last_timestamp = calculate_delta_timestamp(timestamp, last_timestamp)

    file_name = get_file_name(str(file_id))
    thread_name = get_thread_name(thread_id)

    number_arguments = get_number_of_arguments(str(event_id))




    # # file name
    # if file_id == 0xE1:  # In case E1 value we have INTERRUPT type and next byte is a file name id.
    #     byte_pointer += 1
    #     file_id = get_byte(row_bytes)
    #
    #     file_name = get_file_name(str(file_id))
    # else:
    #     file_name = get_file_name(str(file_id))

    #


    amount_arguments = get_number_of_arguments(str(event_id))

    #
    format_string = get_format_string(str(event_id))

    # print(hex(magic_number))
    # print_format_log_line(index, file_name, 0, thread_name, 0, 0, timestamp, delta_timestamp, "TODO")
    break