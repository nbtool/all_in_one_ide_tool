# coding:utf-8
import os
import sys
import subprocess

from pathlib import Path

# Parameter description:
# $1 - Demo path: apps\tuyaos_demo_ble_peripheral
# $2 - Demo name: tuyaos_demo_ble_peripheral
# $3 - Demo firmware version: 1.0.0
# $4 - Demo command: build/clean/flash_all/flash_app
# $5 - 产物包路径，如： output/dist/product1_1.0.0
# python build_app.py apps\tuyaos_demo_ble_peripheral tuyaos_demo_ble_peripheral 1.0.0 clean

print(len(sys.argv))
if len(sys.argv) < 4:
    print("Script parameter error !!!")

# Get the path to the current python interpreter
PYTHON_PATH = sys.executable

DEMO_PATH = sys.argv[1]
DEMO_NAME = sys.argv[2]
DEMO_FIRMWARE_VERSION = sys.argv[3]
DEMO_OUTPUT_PATH = "_output"

BUILD_COMMAND = 'build'

if len(sys.argv) == 5:
    BUILD_COMMAND = sys.argv[4]
if len(sys.argv) == 6:
    BUILD_COMMAND = sys.argv[4]
    DEMO_OUTPUT_PATH = sys.argv[5] 


def get_board_name(path):
    for root, dirs, files in os.walk(path):
        return dirs[0]
BOARD_NAME = get_board_name('./vendor')

print("DEMO_PATH: " + DEMO_PATH)
print("DEMO_NAME: " + DEMO_NAME)
print("DEMO_FIRMWARE_VERSION: " + DEMO_FIRMWARE_VERSION)
print("BOARD_NAME: " + BOARD_NAME)
print("BUILD_COMMAND: " + BUILD_COMMAND)



if BUILD_COMMAND == "build":
    print("build...")
    python_path = PYTHON_PATH + ' ./scripts/pre_build.py'
    para = "%s \"%s\" \"%s\" \"%s\" \"%s\""%(python_path, './', DEMO_PATH, DEMO_NAME, DEMO_FIRMWARE_VERSION)
    ret = subprocess.call(para)
    if ret != 0:
        print("prebuild.py execution failed !!!")
        sys.exit(1)

    python_path = PYTHON_PATH + ' ./vendor/'+BOARD_NAME+'/prepare.py'
    para = "%s pr-build \"%s\" \"%s\" \"%s\" \"%s\" \"%s\""%(python_path, DEMO_PATH,BOARD_NAME,DEMO_OUTPUT_PATH,DEMO_NAME,DEMO_FIRMWARE_VERSION)
    ret = subprocess.call(para)
    if ret != 0:
        print("pr-build execution failed !!!")
        sys.exit(1)
        
    para = "%s build"%(python_path)
    ret = subprocess.call(para)
    if ret != 0:
        print("build execution failed !!!")
        sys.exit(1)


if BUILD_COMMAND == "flash_user":
    print("flash user...")
    python_path = PYTHON_PATH + ' ./vendor/'+BOARD_NAME+'/prepare.py'
    para = "%s flash_user"%(python_path)
    ret = subprocess.call(para)
    if ret != 0:
        print("flash user execution failed !!!")
        sys.exit(1)
   

if BUILD_COMMAND == "flash_all":
    print("flash all...")
    python_path = PYTHON_PATH + ' ./vendor/'+BOARD_NAME+'/prepare.py'
    para = "%s flash_all"%(python_path)
    ret = subprocess.call(para)
    if ret != 0:
        print("flash all execution failed !!!")
        sys.exit(1)
    
if BUILD_COMMAND == "clean":
    print("clean...")

