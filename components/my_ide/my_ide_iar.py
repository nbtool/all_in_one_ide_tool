#!/usr/bin/env python3
# coding=utf-8
import json
import os
from pickle import TRUE
import sys
import threading
import time
from tokenize import group

import lxml.etree as ET

from my_ide.my_ide_base import my_ide_base

current_file_dir = os.path.dirname(__file__)  # 当前文件所在的目录
template_dir = current_file_dir+'/../../template'
sys.path.append(current_file_dir+'/../components')
from my_file.my_file import *
from my_file.my_file_scatter import my_file_scatter
from my_exe.my_exe import my_exe_simple, my_exe_get_install_path

class my_ide_iar(my_ide_base):
    ide_kind = 'iar'
    uvprojx_path = ''
    uv4_path = ''
    insert_group_num = 0   
    counter = 0

    def tmake(self):
        my_ide_base.tmake(self,'..')
        
        IAR_PATH = my_exe_get_install_path('$IAR_PATH')   
        self.uv4_path = IAR_PATH+'/IarBuild.exe'

    def tbuild(self):
        print('\nBUILD')
        cmd = 'IarBuild.exe ./.log/Demo.ewp -build * -log all'
        print('> [cmd]:'+cmd)
        print('> wait about 2 min ...')
        my_exe_simple(cmd,1,self.uv4_path,None)

        DEMO_NAME = self.output['fw']['name']
        DEMO_FIRMWARE_VERSION =  self.output['fw']['ver']

        cmd = 'python3 ./.log/postbuild.py %s "%s"'%(DEMO_NAME, DEMO_FIRMWARE_VERSION)
        my_exe_simple(cmd,1,None,None)

        my_ide_base.tbuild(self)

    def _tlib(self,libs_path,incs_path,comp_path,log_path):
        print('# 3.Create libs...')
        evn = my_file_get_abs_path_and_formart(self.cmd['bin_path'])
        libs = self.output['sdk']['libs']
        print('-> to libs:',libs)
        
        CURR_PATH = os.getcwd()
        os.chdir('.log')
        
        for k,v in self.output['sdk']['components'].items():
            if k in libs:
                print('    ->[Y]',k)
                # create lib
                cur_lib = '../'+libs_path+'/lib'+k+'.lib' 
                
                sdk_uvprojx_path = '../.log/SdkDemo.uvprojx'
                my_file_copy_file_to_file('../.log/Demo.uvprojx',sdk_uvprojx_path)

                # print('    ->[LIB]:',cur_lib)
                self.__delete_group_in_iar(sdk_uvprojx_path)
                self.__insert_file_to_iar(sdk_uvprojx_path,'.c',v['c_files'],'sdk')
                self.__insert_file_to_iar(sdk_uvprojx_path,'.h',v['h_dir'],'')
                self.__make_iar_output_lib(sdk_uvprojx_path,cur_lib)
                
                cmd = 'UV4.exe -j0 -b SdkDemo.uvprojx'
                my_exe_simple(cmd,1,self.uv4_path,None)
                
                my_file_rm_file(sdk_uvprojx_path)
                
                # copy .h to include
                my_file_copy_one_kind_files_to(v['h_dir'],'.h','../'+incs_path+'/components/'+k+'/include') 
            else:
                print('    ->[N]',k)
                # copy .c to src
                my_file_copy_files_to(v['c_files'], '../'+comp_path+'/'+k+'/src')
                # copy .h to include
                my_file_copy_one_kind_files_to(v['h_dir'],'.h', '../'+comp_path+'/'+k+'/include')
        
        # 清除掉生成 lib 时产生的中间文件
        for root, dirs, files in os.walk('../'+libs_path):
            for file in files:
                if not file.endswith('.lib'):
                    my_file_rm_file(os.path.join(root,file))
            break        
        
        os.chdir(CURR_PATH)
    
    def _create_subgroup(self,KIND,LIST,GROUP_NAME):
        my_ide_base._create_subgroup(self,KIND,LIST,GROUP_NAME)
        if len(LIST) == 0:
            return
        
        if self.uvprojx_path == '':
            # copy iar to output
            iar_path         =  self.cmd['bin_path'][1:] # ../vendor -> ./vendor
            build_path        =  '.log'
            my_file_copy_dir_contents_to(iar_path,build_path)
        
            self.uvprojx_path =  build_path+'/Demo.ewp' 

        self.__insert_file_to_iar(self.uvprojx_path,KIND,LIST,GROUP_NAME)
       
       
    ###########################################################
    # IAR 操作内部函数
    ###########################################################
    # 将 iar 工程中的 Groups 下增加的 .c、.lib 全部删除
    def __delete_group_in_iar(self,uvprojx_path):
        tree = ET.parse(uvprojx_path)
        root = tree.getroot()
        
        Groups = root.find("Targets").find("Target").find("Groups")
        Groups.clear()
        
        ET.indent(tree) # format        
        tree.write(uvprojx_path, encoding='utf-8', xml_declaration=True)
        
    # 将 iar 工程切换为输出 lib 库模式
    def __make_iar_output_lib(self,uvprojx_path,output_lib):
        tree = ET.parse(uvprojx_path)
        root = tree.getroot()
        
        TargetCommonOption = root.find("Targets").find("Target").find("TargetOption").find("TargetCommonOption")
        
        AfterMake = TargetCommonOption.find("AfterMake")
        RunUserProg1 = AfterMake.find("RunUserProg1")
        RunUserProg2 = AfterMake.find("RunUserProg2")

        RunUserProg1.text = '0'
        RunUserProg2.text = '0'
        
        CreateExecutable = TargetCommonOption.find("CreateExecutable")
        CreateLib = TargetCommonOption.find("CreateLib")
        OutputDirectory = TargetCommonOption.find("OutputDirectory")
        OutputName = TargetCommonOption.find("OutputName")
        
        CreateExecutable.text = '0'
        CreateLib.text = '1'   
        OutputDirectory.text = os.path.dirname(output_lib).replace('/','\\')+'\\'
        OutputName.text = os.path.basename(output_lib)
        
        ET.indent(tree) # format
        tree.write(uvprojx_path, encoding='utf-8', xml_declaration=True)
    
    # 将相应文件插入到 iar 工程
    def __insert_file_to_iar(self,uvprojx_path,KIND,LIST,GROUP_NAME):
        tree = ET.parse(uvprojx_path)
        root = tree.getroot()

        if KIND == '.c' or KIND == '.lib' or KIND == '.s' or KIND == '.a':
            if KIND == '.lib':
                KIND = '.a'
                
            group = ET.SubElement(root, 'group')
            group_name = ET.SubElement(group, 'name')
            group_name.text = GROUP_NAME

            for file_dir in LIST:
                if file_dir.endswith(KIND):
                    file = ET.SubElement(group, 'file')
                    file_name = ET.SubElement(file, 'name')
                    file_name.text = '$PROJ_DIR$/' + file_dir
            
            ET.indent(tree) # format
            tree.write(uvprojx_path, encoding='utf-8', xml_declaration=True)

        elif KIND == '.h':
            for ele in root.find('configuration').iter("option"):
                name = ele.find('name')
                if name != None and name.text == 'CCIncludePath2':
                    for path in set(LIST):
                        state = ET.SubElement(ele, 'state')
                        state.text = '$PROJ_DIR$/' + path
                    
                    ET.indent(tree) # format
                    tree.write(uvprojx_path, encoding='utf-8', xml_declaration=True)
                    break

        else:
            print("KIND INPUT ERROR")
        