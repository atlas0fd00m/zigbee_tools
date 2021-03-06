#! /usr/bin/env python

###############################
# Imports taken from zbscapy
###############################

# Import logging to suppress Warning messages
import logging
logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

try:
	from scapy.all import *
except ImportError:
	print 'This Requires Scapy To Be Installed.'
	from sys import exit
	exit(-1)

from killerbee import *
from killerbee.scapy_extensions import *	# this is explicit because I didn't want to modify __init__.py

del hexdump
from scapy.utils import hexdump				# Force using Scapy's hexdump()
import os, sys
from glob import glob
###############################

###############################
# Processing Functions
###############################
# Defaults
indent      = "    "
DEBUG       = False
SHOW_RAW    = False
#zb_file     = None
zb_files    = []
find_key    = False
#network_key = "\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf" # Network Key from zbgoodfind
network_key = None
cert_key    = None
SE_Smart_Energy_Profile = 0x0109 # 265

# Dictionaries may not be processed in order. Therefore, these must be separate lists
ZB_Layers = [ \
    Dot15d4, \
    Dot15d4FCS, \
    Dot15d4Beacon, \
    Dot15d4Data, \
    Dot15d4Ack, \
    Dot15d4Cmd, \
    ZigbeeNWK, \
    ZigBeeBeacon, \
    ZigbeeSecurityHeader, \
    ZigbeeAppDataPayload, \
    ZigbeeAppCommandPayload, \
]
ZB_Layers_Names = [ \
    "Dot15d4", \
    "Dot15d4FCS", \
    "Dot15d4Beacon", \
    "Dot15d4Data", \
    "Dot15d4Ack", \
    "Dot15d4Cmd", \
    "ZigbeeNWK", \
    "ZigBeeBeacon", \
    "ZigbeeSecurityHeader", \
    "ZigbeeAppDataPayload", \
    "ZigbeeAppCommandPayload" \
]

def usage():
    print "%s Usage"%sys.argv[0]
    print "    -h: help"
    print "    -f <filename>: capture file with zigbee packets."
    print "    -d <directory name>: directory containing capture files with zigbee packets."
    print "    -k <network_key>: Network Key in ASCII format. Will be converted for use."
    print "    -D: Turn on debugging."
    sys.exit()

def detect_encryption(pkt):
    '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
    if not pkt.haslayer(ZigbeeSecurityHeader) or not pkt.haslayer(ZigbeeNWK):
        return False
    return True

def detect_app_layer(pkt):
    '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
    if not pkt.haslayer(ZigbeeAppDataPayload):
        return False
    return True

def detect_layer(pkt,layer):
    '''detect_entryption: Does this packet have encrypted information? Return: True or False'''
    #if not pkt.haslayer(ZigbeeAppDataPayload):
    if not pkt.haslayer(layer):
        return False
    return True
###############################

if __name__ == '__main__':

    # Process options
    ops = ['-f','-d','-k','-D','-h']

    while len(sys.argv) > 1:
        op = sys.argv.pop(1)
        if op == '-f':
            zb_files = [sys.argv.pop(1)]
        if op == '-d':
            dir_name = sys.argv.pop(1)
            zb_files = glob(os.path.abspath(os.path.expanduser(os.path.expandvars(dir_name))) + '/*.pcap')
        if op == '-k':
            network_key = sys.argv.pop(1).decode('hex')
        if op == '-D':
            DEBUG = True
        if op == '-h':
            usage()
        if op not in ops:
            print "Unknown option:",op
            usage()

    # Test for user input
    if not zb_files: usage()
    #if not network_key: usage()

    if DEBUG: print "\nProcessing files:",zb_files,"\n"
    for zb_file in zb_files:
        if DEBUG: print "\nProcessing file:",zb_file,"\n"
        #print "\nProcessing file:",zb_file,"\n"
        data = kbrdpcap(zb_file)
        num_pkts = len(data)

        # Detect Layers
        if DEBUG: print indent + "Detecting ZigBee Layers"
        for e in range(num_pkts):
            if DEBUG:
                print indent + "Packet " + str(e),data[e].summary()
            else:
                print indent + "Packet " + str(e)

            for l in ZB_Layers:
                if detect_layer(data[e],l): print indent*2 + ZB_Layers_Names[ZB_Layers.index(l)]

            if detect_encryption(data[e]): 
                try:
                    print indent*2 + "%s"%scapy.layers.dot15d4._zcl_profile_identifier[enc_data.getlayer(ZigbeeAppDataPayload).fields['profile']]
                except:
                    print indent*2 + "Unknown Encrypted App Layer"
                if network_key:
                    enc_data = kbdecrypt(data[e],network_key)
                    for a in ZB_Layers:
                        if detect_layer(enc_data,a): print indent*3 + ZB_Layers_Names[ZB_Layers.index(a)]
                        # TODO: Might have additional encryption
                        #if detect_encryption(enc_data): print indent*3 + "Additional Encryption Detected."
                else:
                    print indent*3 + "Has Encrypted Data, no network key provided."

        print ""

