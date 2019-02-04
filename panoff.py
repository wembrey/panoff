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

# Clear the screen
os.system('clear')

infile=input('Enter the name of the XML file you want to work from in the same directory as this script\nExample "infile.xml" in current directory: ')
if not bool(infile):
    infile='infile.xml'
    print(f"\nYou didn't enter an input file name. We will use 'infile.xml' as the input file.")
outfile=input('\nEnter the name for the output file eg: "outfile.xml": ')
if not bool(outfile):
    outfile='outfile.xml'
    print(f"\nYou didn't enter an output file name. We will use 'outfile.xml' as the output file.")
zonefile=input('\nEnter the file name for zone conversions: "zones.txt": ')
if not bool(zonefile):
    zonefile='zones.txt'
    print(f"\nYou didn't enter a zone file name. We will use 'zones.txt' as the zone file.")

# Open the input file and convert to XML tree
try:
    f=open(infile, 'r')
    my_data=f.read()
    my_xml=xt.fromstring(my_data)
    print(f'\nXML successfully file loaded as {my_xml}')
    f.close()
except Exception as e:
    print(f'\nFile open failed with error:\n{e}')
    error_log = error_log + str(e)
    sys.exit()


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
    # get the list of old to new zone mappings

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



# my_xml - top level file element <config>
# getchildren[1] = <devices>
# getchildren[0] = <entry name=localhost.localdomain>
# getchildren[3] = <device-group>
# devicegroup 0  = myxml[1][0][3][0]
#rulebase = my_xml[1][0][3][25].find('pre-rulebase')
#rule = rulebase[0][0][0]
#fromzone = rule.find('from')
# rulebase = devicegroups[25].find('pre-rulebase')

try:
    devicegroups = my_xml[1][0][3][:]
except Exception as e:
    print(f'Get device groups failed with error:\n')
    error_log = error_log + '\n' + str(e)
    sys.exit()

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
                        if fromzone[0].text in zone_dict:
                            print(f'Found entry fromzone {fromzone[0].text} that needs updating to {zone_dict[fromzone[0].text]} in {rule_name}:{dg_name} ')
                            fromzone[0].text=zone_dict[fromzone[0].text]
                            update=True
                        if tozone[0].text in zone_dict:
                            print(f'Found entry tozone {tozone[0].text} that needs updating to {zone_dict[tozone[0].text]} in {rule_name}:{dg_name} ')
                            tozone[0].text=zone_dict[tozone[0].text]
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
