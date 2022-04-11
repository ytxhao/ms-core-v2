#!/usr/bin/env python

import argparse
import os
import shutil
import logging
import subprocess
import sys
import time
import platform
import filecmp


SRC_DIR = SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_SRC_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir))
PROJECT_ROOT_DIR = os.path.normpath(os.path.join(PROJECT_SRC_DIR, os.pardir))

ZORRO_DIR = os.path.join(SRC_DIR, 'zorro')
OUTPUT_DIR = os.path.join(SRC_DIR, 'out')
ENABLED_ARCHS = ['arm64', 'arm', 'x64']
DEFAULT_ARCHS = ['arm64', 'arm']
IOS_SDK_BUILD_SCRIPT = SRC_DIR + "/tools_ms/ios/build_ios_libs.sh"
ANDROID_SDK_BUILD_SCRIPT = SRC_DIR + "/tools_ms/android/build_aar.sh"
LINUX_SDK_BUILD_SCRIPT = SRC_DIR + "/tools_ms/linux/build_linux_libs.sh"

def clean_artifacts(output_dir):
    if os.path.isdir(output_dir):
        print('Deleting ' + output_dir)
        shutil.rmtree(output_dir)

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '-o',
        '--os',
        choices=['a', 'i', 'l'],
        help='The os config can be IGNORED, and decided by os info, or can be "a (Android)", '
             '"i (iOS)", "l (linux)". Defaults to "a (Android)".')
    parser.add_argument(
        '-c',
        '--clean',
        action='store_true',
        default=False,
        help='Removes the previously generated build output, if any.')
    parser.add_argument(
        '--arch',
        nargs='+',
        default=DEFAULT_ARCHS,
        choices=ENABLED_ARCHS,
        help='Architectures to build. Defaults to %(default)s. iOS suppports x64; '
             'Linux only supports x64, will ignore this argument.')
    parser.add_argument(
        '--build',
        default='d',
        choices=['d', 'r'],
        help='The build config. Can be "d (debug)" or "r (release)". '
             'Defaults to "d (debug)".')
    parser.add_argument(
        '--symbol-level', type=str,
        help='Symbol level: 0, 1, 2.')
    parser.add_argument('--verbose',
                    action='store_true',
                    default=False,
                    help='Debug logging.')
    return parser.parse_args()

def chmod(directory):
    cmd = "chmod 777 " + directory
    subprocess.call(cmd, shell=True)

def get_build_args(args):
    build_arg_list = []
    if args.os == "a":    # Android
        # build_arg_list.append('clang_use_chrome_plugins=false')
        build_arg_list.append('is_debug=false' if args.build == 'r' else 'is_debug=true')
    elif args.os == "i":  # iOS
        build_arg_list.append('rtc_use_metal_rendering=false')
        if args.symbol_level:
            build_arg_list.append('symbol_level=' + args.symbol_level)
        else:
            build_arg_list.append('symbol_level=0' if args.build == 'r' else 'symbol_level=2')
    elif args.os == "l":  # Linux
        # build_arg_list.append('rtc_use_x11=false')
        # build_arg_list.append('is_chrome_branded=true')
        build_arg_list.append('openh264_dec=true')
        # build_arg_list.append('clang_use_chrome_plugins=false')
        build_arg_list.append('is_debug=false' if args.build == 'r' else 'is_debug=true')

    build_args = " ".join(i for i in build_arg_list)
    return build_args

def main():
    
    print("\033[32m SRC_DIR: \033[0m" + SRC_DIR)
    print("\033[32m PROJECT_SRC_DIR: \033[0m" + PROJECT_SRC_DIR)
    print("\033[32m PROJECT_ROOT_DIR: \033[0m" + PROJECT_ROOT_DIR)
    print("\033[32m ZORRO_DIR: \033[0m" + ZORRO_DIR)
    print("\033[32m OUTPUT_DIR: \033[0m" + OUTPUT_DIR)
    start_sec = time.time()
    args = parse_args()
    print(args)

    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    level1=logging.DEBUG if args.verbose else logging.INFO
    print(level1)
    if args.clean:
        clean_artifacts(OUTPUT_DIR)
    
    if args.build == "r":
        build_config = "release"
    else:
        build_config = "debug"
    build_dir = os.path.join(OUTPUT_DIR, build_config)
    logging.info('args.os:%s',args.os)
    if not args.os:
        if platform.system() == "Darwin":
            args.os = "i"
        elif platform.system() == "Linux":
            args.os = "a"
    elif args.os == 'l':
        if platform.system() != "Linux":
            print("\033[31mCompiled in a wrong system.\n\033[0m")
            return
    logging.info('args.os:%s',args.os)
    build_args = get_build_args(args)
    if args.os == "a":
        archs = list(args.arch)
        architectures = ""
        for arch in archs:
            if arch == "arm":
                arch = "armeabi-v7a"
            if arch == "arm64":
                arch = "arm64-v8a"
            architectures = architectures + " " + arch
        
        out_sdk = os.path.join(build_dir, "ms-core.aar")
        logging.info('architectures:%s out_sdk:%s', architectures, out_sdk)
        cmd = "{0} --output {1} --build-dir {2} --extra-gn-args {3} --arch {4}".format(
            ANDROID_SDK_BUILD_SCRIPT,
            out_sdk,
            build_dir,
            build_args,
            architectures)
        logging.info('cmd:%s', cmd)
        subprocess.call(cmd, shell=True)

        chmod(OUTPUT_DIR)
        chmod(build_dir)
        arch_str = architectures.split()
        for arch in arch_str:
            arch_dir = os.path.join(build_dir, arch)
            chmod(arch_dir)
            dir_list = os.listdir(arch_dir)
            for i in range(0, len(dir_list)):
                path = os.path.join(arch_dir, dir_list[i])
                if os.path.isdir(path):
                    chmod(path)

    if args.os == "i":
        architectures = ' '.join(list(args.arch))
        cmd = "{0} --build_config {1} --output-dir {2} --extra-gn-args {3} --arch {4}".format(
            IOS_SDK_BUILD_SCRIPT,
            build_config,
            build_dir,
            build_args,
            architectures)
        print("=============ios cmd:"+cmd)
        subprocess.call(cmd, shell=True)


if __name__ == '__main__':
    sys.exit(main())