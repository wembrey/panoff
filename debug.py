#!/usr/bin/env python
import xml.etree.ElementTree as xt
import sys
import os

# set variables
zone_dict={}
oldheader, newheader = 'Old Zone Name', 'New Zone Name'
error_log=''
dg_count=0
rule_count=0
zonefile=''
my_xml=''
devicegroups=''
outfile=''
infile=''
welcome="""\n\n\n
  _____               ____   __  __
 |  __ \             / __ \ / _|/ _|
 | |__) |_ _ _ __   | |  | | |_| |_
 |  ___/ _` | '_  \ | |  | |  _|  _|
 | |  | (_| | | | | | |__| | | | |
 |_|   \__,_|_| |_|  \____/|_| |_|

Welcome to PanOff - an offline XML config editor for items not supported in Pandevice\n\n"""
colors = {
        'blue': '\033[94m',
        'pink': '\033[95m',
        'green': '\033[92m',
        'red': '\033[91m',
        'yellow': '\033[93m',
        }

def highlight(string, color):
    if not color in colors: return string
    return colors[color] + string + '\033[0m'

# Clear the screen
os.system('clear')
print(highlight(welcome, 'blue'))

def get_infile():
    global infile
    infile=input('Enter the name of the XML file you want to work from in the same directory as this script\nExample "infile.xml" in current directory: ')
    if not bool(infile):
        infile='infile.xml'
        print(f"\nYou didn't enter an input file name. We will use 'infile.xml' as the input file.")

def get_outfile():
    global outfile
    outfile=input('\nEnter the name for the output file eg: "outfile.xml": ')
    if not bool(outfile):
        outfile='outfile.xml'
        print(f"\nYou didn't enter an output file name. We will use 'outfile.xml' as the output file.")

def get_zonefile():
    global zonefile
    zonefile=input('\nEnter the file name for zone conversions: "zones.txt": ')
    if not bool(zonefile):
        zonefile='zones.txt'
        print(f"\nYou didn't enter a zone file name. We will use 'zones.txt' as the zone file.")

def get_xml():
    # Open the input file and convert to XML tree
    global my_xml
    global error_log
    try:
        f=open(infile, 'r')
        my_data=f.read()
        my_xml=xt.fromstring(my_data)
        print(f'\nXML successfully file loaded as {my_xml}')
        f.close()
        return my_xml
    except Exception as e:
        print(f'\nFile open failed with error:\n{e}')
        error_log = error_log + str(e)
        sys.exit()

def get_zones():
    #Check if zone conversion file was added and load it
    if bool(zonefile):
        try:
            f=open(zonefile, 'r')
            zonedata=f.read()
            zonelist=zonedata.split('\n')
            print(f'\nZones imported from file: {zonefile}')
            f.close()
        except Exception as e:
            print(f'\nFile open of {zonefile} failed with error:\n{e}')
            error_log = error_log + str(e)
            sys.exit()
        x = 0
        for zonepair in zonelist:
            try:
                if len(zonepair) >= 3:
                    oldzone, newzone = zonepair.split(' ')
                    x+=1
                    zone_dict[oldzone]=newzone
            except Exception as e:
                print(f'\nZone file mapping failed for "{zonepair}" at line {x} with error:\n{e}')
                sys.exit()
        print('\nSummary of old to new zone mappings')
        print(f'{oldheader:>30}: - :{newheader:<}')
        print(f'{oldzone:>30} - {zone_dict[oldzone]:<}')
        command=input('\nIf these are wrong - press q to finish and start again or press [Enter] to continue: ')
        if str.lower(command)=='q':
            sys.exit()
        return zone_dict

    # Get the zones via CLI if not provided in a file
    if not bool(zonefile):
        print('Now we need to know the old zone mappings to new\nYou can paste in multiple entries but you need to enter the old and new zone consecutively as follows')
        print('Example:\noldzone\nnewzone\nveryoldzone\nnewzone\n')
        print('When done, just add a blank line to finish')
        while True:
            oldzone=input('Enter the old zone name: ')
            if not bool(oldzone):
                break
            newzone=input('Enter the new zone name: ')
            if not bool(newzone):
                break
            zone_dict[oldzone]=newzone
        print('checking zone mappings:')
        print(f'{oldheader:>30}: converts to :{newheader:<}')
        for oldzone in zone_dict:
            print(f'{oldzone:>10} - {zone_dict[oldzone]:<30}')
        command=input('If there are wrong - press q to finish and start again')
        if str.lower(command)=='q':
            sys.exit()
        return zone_dict


# my_xml - top level file element <config>
# getchildren[1] = <devices>
# getchildren[0] = <entry name=localhost.localdomain>
# getchildren[3] = <device-group>
# devicegroup 0  = myxml[1][0][3][0]
#rulebase = my_xml[1][0][3][25].find('pre-rulebase')
#rule = rulebase[0][0][0]
#fromzone = rule.find('from')
# rulebase = devicegroups[25].find('pre-rulebase')

def get_dgs():
    # Read the device groups from the XML tree
    global devicegroups
    try:
        devicegroups = my_xml[1][0][3][:]
    except Exception as e:
        print(f'Get device groups failed with error:\n')
        error_log = error_log + '\n' + str(e)
        sys.exit()

def update_zones():
    global devicegroups
    global zone_dict
    # Update zone names based on entries on supplied zone file
    global devicegroups # Use devicegroups as a global so that the function can change the XML document
    for dg in devicegroups:
        dg_name=dg.items()[0][1]
        print(f'Starting device group {dg_name}')
        try:
            rulebase = dg.find('pre-rulebase')
            if rulebase==None:
                print(f'Skipping {dg_name} as no rulebase found')
                continue
            else:
                try:
                    for rule_set in rulebase:
                        try:
                            if not bool(rule_set[0]):
                                print(f'Skipping rule set {rule_set.tag} in {dg_name} as there are no entries\n')
                                continue
                        except Exception as e:
                            print(f'Rule set parse failed')
                        rule_set_name=rule_set.tag
                        for rule in rule_set[0]:
                            update=False
                            rule_name = rule.items()[0][1]
                            fromzone = rule.find('from')
                            try:
                                tozone = rule.find('to')
                            except:
                                print(f'Unable to map to-zone for rule {rule_name} in {rule_set_name} - {dg_name}')
                            #print(f'Device Group: {dg_name} - Rule: {rule_name:>20} - From Zone: {fromzone[0].text} - To Zone: {tozone[0].text}')
                            #print(f'To Zone: {tozone[0].text:>20}')
                            for index, item in enumerate(fromzone):
                                if fromzone[index].text in zone_dict:
                                    print(f'Found entry fromzone {fromzone[index].text} that needs updating to {zone_dict[fromzone[index].text]} in {rule_name}:{dg_name} ')
                                    fromzone[index].text=zone_dict[fromzone[index].text]
                                    update=True
                            for index, item in enumerate(tozone):
                                if tozone[index].text in zone_dict:
                                    print(f'Found entry tozone {tozone[index].text} that needs updating to {zone_dict[tozone[index].text]} in {rule_name}:{dg_name} ')
                                    tozone[index].text=zone_dict[tozone[index].text]
                                    update=True
                            if update==True:
                                rule_count+=1
                        rule_name='None'
                        # end of rule
                    rule_set_name='None'
                    # End of rule_set
                except:
                    print(f'Unable to find rulebase in {dg_name}\n')
                    error_log = error_log + '\nFailed to find rulebase for' + dg_name + str(e)
                    continue
        except Exception as e:
            print(f'Failed operation for rule "{rule_name}" for rule set "{rule_set.tag}" in DeviceGroup "{dg_name}" with error\n{e}')
            error_log = error_log + '\n' + 'Failed operation for rule' + rule_name + ' in rule set ' + rule_set_name + ' in DeviceGroup ' + str(dg_name) + ' with error\n' + str(e)
        print(f'Device Group {dg_name} finished\n')
        dg_count +=1
        dg_name='None'
        # end of devicegroup
    print(f'Finished operation on {rule_count} rules over {dg_count} device groups\n')

def write_xml_out():
    get_outfile()
    command=input('Write data to xml file? (y/n)')
    if str.lower(command)!='y':
        print(error_log)
        pritn('\nExiting now')
        sys.exit()
    try:
        print('Converting XML back to string for file writing')
        data_out=xt.tostring(my_xml, encoding='utf8', method='xml')
        print(f'Opening new file named "{outfile}"')
        f=open(outfile, 'wb+')
        print(f'Writing data to file')
        f.write(data_out)
        print('Closing')
        f.close()
    except Exception as e:
        print(f'Operation failed with error:\n{e}')
        error_log = error_log + '\n' + str(e)
        print(error_log)
        print('\nExiting now')
        sys.exit()

def mainmenu():
    while True:
        os.system('clear')
        print('Choose a function to run')
        print('1. Update zone names')
        print('2. ')
        print('3. ')
        print('4. ')
        print('5. ')
        print('6. ')
        print('7. ')
        print('8. Write changes to outfile')
        print('9. Quit')
        try:
            command=int(input('Select a number:'))
            if command==1:
                get_zonefile()
                get_zones()
                update_zones()
            if command==2:
                pass
            if command==3:
                pass
            if command==4:
                pass
            if command==5:
                pass
            if command==6:
                pass
            if command==7:
                pass
            if command==8:
                write_xml_out()
            if command==9:
                print('You chose to quit')
                quit()
            else:
                print('Please select a valid option: ')
        except (ValueError, IndexError):
            pass


def main():
    global infile
    global my_xml
    global devicegroups
    get_infile()
    get_xml()
    get_dgs()
    mainmenu()


if __name__ == "__main__":
    # main()
    pass