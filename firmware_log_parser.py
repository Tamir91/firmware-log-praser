"""
This script parse firmware log
Usage
"""
import getopt
import os.path
import re
import sys

import numpy


# from cgi import log


def usage() -> None:
    """

    :return:
    :rtype:
    """
    pass


#  1. open .log
def remove_characters(file_link: str) -> str:
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

        data.replace(' ', '')  # remove white spaces
        data = re.sub("[^0-9,]", "", data)  # remove all except numbers and ','

    return data

def split_string(string: str, separator: int) -> str:
    if str and type(string) is str and type(separator) is int:
        mat = []

        for (i : str)





#  3. create matrix of lines


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
logs = remove_characters("d457_fw_lose_vc.log")
list = logs.split(',')

lines = numpy.array_split(list, 160)
print(lines)

