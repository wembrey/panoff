#!/usr/bin/env python
import xml.etree.ElementTree as xt
import sys

error_log=''
infile=input('Enter the name of the XML file you want to work from in the same directory as this script\nExample "file.xml" in current directory: ')
outfile=input('Enter the name for the output file eg: "outfile.xml": ')
try:
    f=open(infile, 'r')
    my_data=f.read()
    my_xml=xt.fromstring(my_data)
    print(f'XML successfully file loaded as {my_xml}')
except Exception as e:
    print(f'File open failed with error:\n{e}')
    error_log = error_log + str(e)
    sys.exit()

# get the list of old to new zone mappings
zone_dict={}
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
    except:
        print(f'Unable to find rulebase in {dg_name}\n')
        error_log = error_log + '\nFailed to find rulebase for' + dg_name + str(e)
        continue
    try:
        for rule_set in rulebase:
            #print(rule_set) - security, nat, app override etc.
            if not bool(rule_set[0]):
                print(f'Skipping rule set {rule_set.tag} in {dg_name} as there are no entries\n')
                continue
            rule_set_name=rule_set.tag
            for rule in rule_set[0]:
                rule_name = rule.items()[0][1]
                fromzone = rule.find('from')
                try:
                    tozone = rule.find('to')
                except:
                    print(f'Unable to map tp-zone for rule {rule_name} in {rule_set_name} - {dg_name}')
                #print(f'Device Group: {dg_name} - Rule: {rule_name:>20} - From Zone: {fromzone[0].text} - To Zone: {tozone[0].text}')
                #print(f'To Zone: {tozone[0].text:>20}')
                if fromzone[0].text in zone_dict:
                    print(f'Found entry fromzone {fromzone[0].text} that needs updating to {zone_dict[fromzone[0].text]} in {rule_name}:{dg_name} ')
                    fromzone[0].text=zone_dict[fromzone[0].text]
                if tozone[0].text in zone_dict:
                    print(f'Found entry tozone {tozone[0].text} that needs updating to {zone_dict[tozone[0].text]} in {rule_name}:{dg_name} ')
                    tozone[0].text=zone_dict[tozone[0].text]
            rule_name='None'
            # end of rule
        rule_set_name='None'
        # End of rule_set
    except Exception as e:
        print(f'Failed operation for rule "{rule_name}" for rule set "{rule_set_name}" in DeviceGroup "{dg_name}" with error\n{e}')
        error_log = error_log + '\n' + 'Failed operation for rule' + rule_name + ' in rule set ' + rule_set_name + ' in DeviceGroup ' + str(dg_name) + ' with error\n' + str(e)
    print(f'Device Group {dg_name} finished\n')
    dg_name='None'
    # end of devicegroup

print('Finished operation\n')
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
