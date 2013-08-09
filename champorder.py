#!/usr/bin/python
import argparse
import mmap
import pydot
import re
import sys, os
from collections import defaultdict
import Image

LOGS_FOLDER = 'Game - R3d Logs'


''' Search the entire computer recursively for the League Logs Directory '''
def find_log_dir():
    # Determine operating system to locate root folder. This feels dirty.
    # Please tell me if you find a better way.
    rootdir = ''
    if os.name == 'posix':
        rootdir = '/'
    elif os.name == 'nt':
        rootdir = 'C:\\'
    else:
        sys.exit('''Operating system not recognized - please enter the logs
                    path manually''')

    # Recursive find
    for root, dirs, files in os.walk('/'):
        if LOGS_FOLDER in dirs:
            return os.path.join(root, LOGS_FOLDER)

    # Nothing found
    return None

''' Parse the summoner names input and split it to a list '''
def parse_names(raw_names):
    result = raw_names.split(',')
    result = map((lambda x: x.strip()), result)     # strip whitespace
    return result


''' Search the logs in the given path for the given summoner names and record
the order of champions played '''
def get_order(summoners, path):
    # Find the acutal log files
    logs = os.listdir(path)
    logs = filter((lambda x: x.endswith('.txt')), logs)
    logs.sort()

    champion_order = []
    
    # Iterate over logs
    for log in logs:
        # Open and mmap the file
        fn = os.path.join(path,log)
        size = os.stat(fn).st_size
        f = open(fn)
        data = mmap.mmap(f.fileno(), size, access=mmap.ACCESS_READ)

        pattern = re.compile(r'(\w+)\(\d+\) created for ' + summoners[0])
        result = pattern.search(data)
        if result:
            champion = result.groups()[0]
            champion_order.append(champion)

    return champion_order

''' Parse through the champion order, returning a DOT file showing a flowchart
    of champion selections and a frequency associated with each edge'''
def parse_order(champion_order):
    # This is kinda ugly...
    ordermap = defaultdict(lambda: defaultdict(lambda: 0))
    last = '<<start>>'
    total = 0.0
    result = ''
    for champion in champion_order:
        ordermap[last][champion] += 1.0
        ordermap[last]['<total>'] += 1.0
        last = champion
    result += 'digraph champions {\n'
    for left,leftmap in ordermap.iteritems():
        for right,count in leftmap.iteritems():
            if right is not '<total>':
                result += '\t' + left + ' -> ' + right + '[label="%.2f%%"]' % \
                (count/ordermap[left]['<total>']) + '\n'
    result += '}\n'
    return result


''' Entry point for the program '''
if __name__ == '__main__':
    # argument parsing
    #parser = argparse.ArgumentParser()
    #parser.add_argument('SUMMONER_NAMES', 
    #                    help='''a comma-separated list of all your summoner
    #                    names (if you wish to track more than one)''')
    #parser.add_argument('OUTPUT_FILENAME',
    #                    help='''the name of the file to save the graph to''')
    #parser.add_argument('-i', '--input', 
    #                    help='''path of your logs folder (Game - R3d Logs).
    #                    Leave empty to find automatically (may be slower than
    #                    manual input)''')
    #args = parser.parse_args()
    
    args_SUMMONER_NAMES = raw_input('Enter Summoner names (comma-separated): ')
    args_OUTPUT_FILENAME = 'temp'
    args_input = None

    # Get the log directory (or error out appropriately)
    log_dir = ''
    if args_input:
        log_dir = args_input
        if not os.path.exists(log_dir):
            sys.exit('directory not found')
    else:
        log_dir = find_log_dir()
        if not log_dir:
            sys.exit('logs folder not found')

    # Parse summoner names
    summoner_list = parse_names(args_SUMMONER_NAMES)

    print '// Logs Direcoty: %s' % log_dir
    print '// Player Summoners: %s' % summoner_list

    # Get champion order
    champion_order = get_order(summoner_list, log_dir)
    print '// Champion Order: %s' % champion_order
    dot_data = parse_order(champion_order)
    graph = pydot.graph_from_dot_data(dot_data)
    graph.write_png(args_OUTPUT_FILENAME + '.png')
    img = Image.open(args_OUTPUT_FILENAME + '.png')
    img.show()
