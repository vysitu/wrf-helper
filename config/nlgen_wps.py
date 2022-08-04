import os
import json
from copy import deepcopy as dc 

from nesting import Box, Nest 
from namelist_edit import update_line, quote_wrap, list_to_str

from pathlib import Path
script_path = os.path.dirname(Path(__file__))

target_fields = [
    'max_dom',
    'start_date',
    'end_date',
    'interval_seconds',
    'opt_output_from_geogrid_path',
    'opt_output_from_metgrid_path'
]

def update_line(str_old:str, info:str):
    str_new = str_old.split('=')[0]
    str_new += '= ' + info + ',\n'
    return(str_new)

def quote_wrap(value:str):
    return('\''+value+'\'')

def interpret_wps(conf_dict, output_wps):
    template_file = os.path.join(script_path, 'nl_template_wps.txt')
    with open(template_file) as fp:
        wps_info = fp.readlines()
    
    # extract information to strings
    max_dom_int = int(conf_dict['domain_count'])
    date_start = conf_dict['date_start']
    date_end = conf_dict['date_end']
    interval_sec_int = int(int(conf_dict['interval_hours']) * 3600)
    wps_output_path = conf_dict['wps_output_path']

    # domains
    sub_doms = max_dom_int - 1
    main_box_geo = eval(conf_dict['main_box'])
    main_box = Box(geo_desc=main_box_geo, box_num=1)
    main_dx = main_box_geo[4]; main_dy = main_box_geo[5]

    parent_id_list = [1]; ratio_list = [1] 
    i_start_list = [1]; j_start_list = [1]
    e_we_list = [main_box_geo[2]]; e_sn_list = [main_box_geo[3]]
    for i in range(1, sub_doms + 1):
        sub_box_def = eval(conf_dict[f'sub_box_{i}'])
        sub_box_id = sub_box_def[5]  # id for nesting
        sub_box_ratio = sub_box_def[4]
        sub_box_geo = dc(sub_box_def[:4])
        sub_box_geo.append(int(main_dx / sub_box_ratio))
        sub_box_geo.append(int(main_dy / sub_box_ratio))
        sub_box = Box(geo_desc=sub_box_geo, box_num=sub_box_id)
        n = Nest()
        parent_id, nested_id, i_start, j_start = n.nest(main_box, sub_box)
        parent_id_list.append(parent_id)
        ratio_list.append(sub_box_ratio)
        i_start_list.append(round(i_start))
        j_start_list.append(round(j_start))
        e_we_list.append(sub_box_geo[2])
        e_sn_list.append(sub_box_geo[3])

    # update info
    for linenum, line in enumerate(wps_info):
        if '=' not in line:
            continue
        else:
            varname = line.split('=')[0]
            varname = varname.strip(' ')

        if varname == 'max_dom':
            wps_info[linenum] = update_line(line, str(max_dom_int))
        elif varname == 'start_date':
            wps_info[linenum] = update_line(line, ','.join([quote_wrap(date_start)]*max_dom_int))
        elif varname == 'end_date':
            wps_info[linenum] = update_line(line, ','.join([quote_wrap(date_end)]*max_dom_int))
        elif varname == 'interval_seconds': 
            wps_info[linenum] = update_line(line, str(interval_sec_int))
        elif varname == 'opt_output_from_geogrid_path':
            wps_info[linenum] = update_line(line, quote_wrap(wps_output_path))
        elif varname == 'opt_output_from_metgrid_path':
            wps_info[linenum] = update_line(line, quote_wrap(wps_output_path))
        elif varname == 'ref_lon':
            wps_info[linenum] = update_line(line, str(main_box_geo[0]))
        elif varname == 'ref_lat':
            wps_info[linenum] = update_line(line, str(main_box_geo[1]))
        elif varname == 'dx':
            wps_info[linenum] = update_line(line, str(main_box_geo[4]))
        elif varname == 'dy':
            wps_info[linenum] = update_line(line, str(main_box_geo[5]))

        elif varname == 'parent_id':
            wps_info[linenum] = update_line(line, list_to_str(parent_id_list))
        elif varname == 'parent_grid_ratio':
            wps_info[linenum] = update_line(line, list_to_str(ratio_list))
        elif varname == 'i_parent_start':
            wps_info[linenum] = update_line(line, list_to_str(i_start_list))
        elif varname == 'j_parent_start':
            wps_info[linenum] = update_line(line, list_to_str(j_start_list))
        elif varname == 'e_we':
            wps_info[linenum] = update_line(line, list_to_str(e_we_list))
        elif varname == 'e_sn':
            wps_info[linenum] = update_line(line, list_to_str(e_sn_list))

        
    with open(output_wps, 'w') as f:
        for line in wps_info:
            f.writelines(line)

if __name__=='__main__':
    nl_conf_default = os.path.join(script_path, 'nl.conf')
    nl_conf = input(f'Input config file. Default: {nl_conf_default} \n>>')
    if len(nl_conf) < 1:
        nl_conf = nl_conf_default 
    conf_file = open(nl_conf)
    conf_dict = json.load(conf_file)
    output_file = os.path.join(script_path, 'namelist.wps.test')
    # sub grid format:
    # lon, lat, xsize, ysize, xratio, yratio, parent_id

    interpret_wps(conf_dict, output_file)