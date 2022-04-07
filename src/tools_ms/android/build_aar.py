#!/usr/bin/env python
# -*- coding:utf-8 -*-
# Copyright (c) 2017 The WebRTC project authors. All Rights Reserved.
#
# Use of this source code is governed by a BSD-style license
# that can be found in the LICENSE file in the root of the source
# tree. An additional intellectual property rights grant can be found
# in the file PATENTS.  All contributing project authors may
# be found in the AUTHORS file in the root of the source tree.
"""Script to generate libwebrtc.aar for distribution.

The script has to be run from the root src folder.
./tools_ms/android/build_aar.py

.aar-file is just a zip-archive containing the files of the library. The file
structure generated by this script looks like this:
 - AndroidManifest.xml
 - classes.jar
 - libs/
   - armeabi-v7a/
     - libms-core.so
   - x86/
     - libms-core.so
"""
# from  configparser import ConfigParser 
import argparse
# import configparser
import ConfigParser
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import re
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
SRC_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir))
CORE_DIR = os.path.normpath(os.path.join(SRC_DIR, 'third_party', 'ms-core'))
MSL_APPLICATION_DIR =  os.path.normpath(os.path.join(CORE_DIR, 'sdk','android','MSLApplication'))
DEPOT_TOOLS_PATH = os.path.normpath(os.path.join(SRC_DIR, 'third_party', 'depot_tools'))
ANDROID_NDK_ROOT_DIR = ""
ANDROID_SDK_ROOT_DIR = ""
DEFAULT_ARCHS = ['armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64']
NEEDED_SO_FILES = ['libms-core.so']
JAR_FILE = 'lib.java/third_party/core/sdk/android/libms-framework.jar'
MANIFEST_FILE = 'sdk/android/AndroidManifest.xml'
TARGETS = [
    # 'third_party/ms-core/sdk/android:libms-framework',
    'third_party/ms-core/sdk:libms-core',
]

# sys.path.append(os.path.join(SCRIPT_DIR, '..', 'libs'))
# from generate_licenses import LicenseBuilder
print("--------- SCRIPT_DIR:"+SCRIPT_DIR)
print("--------- SRC_DIR:"+SRC_DIR)
print("--------- CORE_DIR:"+CORE_DIR)
sys.path.append(os.path.join(SRC_DIR, 'build'))
# import 


def _ParseArgs():
    parser = argparse.ArgumentParser(description='libwebrtc.aar generator.')
    parser.add_argument(
        '--build-dir',
        type=os.path.abspath,
        help='Build dir. By default will create and use temporary dir.')
    parser.add_argument('--output',
                        default='libwebrtc.aar',
                        type=os.path.abspath,
                        help='Output file of the script.')
    parser.add_argument(
        '--arch',
        default=DEFAULT_ARCHS,
        nargs='*',
        help='Architectures to build. Defaults to %(default)s.')
    parser.add_argument('--use-goma',
                        action='store_true',
                        default=False,
                        help='Use goma.')
    parser.add_argument('--verbose',
                        action='store_true',
                        default=False,
                        help='Debug logging.')
    parser.add_argument(
        '--extra-gn-args',
        default=[],
        nargs='*',
        help="""Additional GN arguments to be used during Ninja generation.
              These are passed to gn inside `--args` switch and
              applied after any other arguments and will
              override any values defined by the script.
              Example of building debug aar file:
              build_aar.py --extra-gn-args='is_debug=true'""")
    parser.add_argument(
        '--extra-ninja-switches',
        default=[],
        nargs='*',
        help="""Additional Ninja switches to be used during compilation.
              These are applied after any other Ninja switches.
              Example of enabling verbose Ninja output:
              build_aar.py --extra-ninja-switches='-v'""")
    parser.add_argument(
        '--extra-gn-switches',
        default=[],
        nargs='*',
        help="""Additional GN switches to be used during compilation.
              These are applied after any other GN switches.
              Example of enabling verbose GN output:
              build_aar.py --extra-gn-switches='-v'""")
    return parser.parse_args()


def _RunGN(args):
    cmd = [
        sys.executable,
        os.path.join(DEPOT_TOOLS_PATH, 'gn.py')
    ]
    logging.info('_RunGN  yuhaoo args:%s', args)
    cmd.extend(args)
    logging.info('_RunGN  yuhaoo cmd:%s', cmd)
    logging.debug('Running: %r', cmd)
    subprocess.check_call(cmd)


def _RunNinja(output_directory, args):
    cmd = [
        os.path.join(DEPOT_TOOLS_PATH, 'ninja'),'-v', '-C',
        output_directory
        # '-t', 'query', 'all'
    ]
    logging.info('_RunNinja  yuhaoo args:%s', args)
    logging.info('_RunNinja  yuhaoo cmd:%s', cmd)
    cmd.extend(args)
    logging.debug('Running: %r', cmd)
    subprocess.check_call(cmd)


def _EncodeForGN(value):
    """Encodes value as a GN literal."""
    if isinstance(value, str):
        return '"' + value + '"'
    elif isinstance(value, bool):
        return repr(value).lower()
    else:
        return repr(value)


def _GetOutputDirectory(build_dir, arch):
    """Returns the GN output directory for the target architecture."""
    return os.path.join(build_dir, arch)


def _GetTargetCpu(arch):
    """Returns target_cpu for the GN build with the given architecture."""
    if arch in ['armeabi', 'armeabi-v7a']:
        return 'arm'
    elif arch == 'arm64-v8a':
        return 'arm64'
    elif arch == 'x86':
        return 'x86'
    elif arch == 'x86_64':
        return 'x64'
    else:
        raise Exception('Unknown arch: ' + arch)


def _GetArmVersion(arch):
    """Returns arm_version for the GN build with the given architecture."""
    if arch == 'armeabi':
        return 6
    elif arch == 'armeabi-v7a':
        return 7
    elif arch in ['arm64-v8a', 'x86', 'x86_64']:
        return None
    else:
        raise Exception('Unknown arch: ' + arch)


def Build(build_dir, arch, extra_gn_args, extra_gn_switches,
          extra_ninja_switches):
    """Generates target architecture using GN and builds it using ninja."""
    logging.info('Building: %s', arch)
    output_directory = _GetOutputDirectory(build_dir, arch)
    logging.info('Building output_directory: %s', output_directory)
    logging.info('Building extra_gn_args: %s', extra_gn_args)
    gn_args = {
        'target_os': 'android',
        'is_debug': False,
        'is_component_build': False,
        'target_cpu': _GetTargetCpu(arch),
    }
    logging.info('Building gn_args: %s', gn_args)
    arm_version = _GetArmVersion(arch)
    logging.info('Building arm_version: %s', arm_version)
    if arm_version:
        gn_args['arm_version'] = arm_version
    gn_args_str = '--args=' + ' '.join(
        [k + '=' + _EncodeForGN(v)
         for k, v in gn_args.items()] + extra_gn_args)
    logging.info('Building gn_args_str: %s', gn_args_str)

    config = ConfigParser.ConfigParser()
    config_path = os.path.normpath(os.path.join(SRC_DIR, 'tools_ms','android', 'config.ini'))
    config.read(filenames = config_path)
    android_ndk_root = config.get("config", "android_ndk_root")
    android_ndk_version = config.get("config", "android_ndk_version")
    android_ndk_major_version = config.get("config", "android_ndk_major_version")
    android_sdk_root = config.get("config", "android_sdk_root")

    print("=======android_ndk_root:"+android_ndk_root)
    print("=======android_ndk_version:"+android_ndk_version)
    print("=======android_ndk_major_version:"+android_ndk_major_version)
    print("=======android_sdk_root:"+android_sdk_root)
    global ANDROID_NDK_ROOT_DIR
    ANDROID_NDK_ROOT_DIR = android_ndk_root
    global ANDROID_SDK_ROOT_DIR
    ANDROID_SDK_ROOT_DIR = android_sdk_root
    android_config_dict={}
    android_config_dict["default_android_ndk_root"]=android_ndk_root
    android_config_dict["default_android_ndk_version"]=android_ndk_version
    android_config_dict["default_android_ndk_major_version"]=android_ndk_major_version
    android_config_dict["default_android_sdk_root"]=android_sdk_root
    gn_args_str=gn_args_str +" "+ ' '.join([k + '=' + _EncodeForGN(v)
         for k, v in android_config_dict.items()])
    print(android_config_dict)
    print("=========gn_args_str"+gn_args_str)
    gn_args_list = ['gen', output_directory, gn_args_str]
    gn_args_list.extend(extra_gn_switches)
    _RunGN(gn_args_list)

    ninja_args = TARGETS[:]
    ninja_args.extend(extra_ninja_switches)
    _RunNinja(output_directory, ninja_args)


def CollectCommon(aar_file, build_dir, arch):
    """Collects architecture independent files into the .aar-archive."""
    logging.info('Collecting common files.')
    output_directory = _GetOutputDirectory(build_dir, arch)
    aar_file.write(os.path.join(CORE_DIR, MANIFEST_FILE), 'AndroidManifest.xml')
    aar_file.write(os.path.join(output_directory, JAR_FILE), 'classes.jar')


def Collect(aar_file, build_dir, arch):
    """Collects architecture specific files into the .aar-archive."""
    logging.info('Collecting: %s', arch)
    output_directory = _GetOutputDirectory(build_dir, arch)

    abi_dir = os.path.join('jni', arch)
    for so_file in NEEDED_SO_FILES:
        aar_file.write(os.path.join(output_directory, so_file),
                       os.path.join(abi_dir, so_file))


# def GenerateLicenses(output_dir, build_dir, archs):
#     builder = LicenseBuilder(
#         [_GetOutputDirectory(build_dir, arch) for arch in archs], TARGETS)
#     builder.GenerateLicenseText(output_dir)


def BuildAar(archs,
             output_file,
             extra_gn_args=None,
             ext_build_dir=None,
             extra_gn_switches=None,
             extra_ninja_switches=None):
    extra_gn_args = extra_gn_args or []
    extra_gn_switches = extra_gn_switches or []
    extra_ninja_switches = extra_ninja_switches or []
    build_dir = ext_build_dir if ext_build_dir else tempfile.mkdtemp()
    logging.info('BuildAar  yuhaoo archs:%s', archs)
    logging.info('BuildAar  yuhaoo output_file:%s', output_file)
    logging.info('BuildAar  yuhaoo extra_gn_args:%s', extra_gn_args)
    logging.info('BuildAar  yuhaoo ext_build_dir:%s', ext_build_dir)
    logging.info('BuildAar  yuhaoo extra_gn_switches:%s', extra_gn_switches)
    logging.info('BuildAar  yuhaoo extra_ninja_switches:%s', extra_ninja_switches)
    logging.info('BuildAar  yuhaoo build_dir:%s', build_dir)
    for arch in archs:
        Build(build_dir, arch, extra_gn_args, extra_gn_switches,
              extra_ninja_switches)
        output_directory = _GetOutputDirectory(build_dir, arch)
        
        logging.info('BuildAar  yuhaoo output_directory:%s', output_directory)
        # sdk/android/MSLApplication/msl-core/src/main/libs
        for so_file in NEEDED_SO_FILES:
            output_file = os.path.normpath(os.path.join(output_directory, so_file))
            logging.info('BuildAar  yuhaoo output_file:%s', output_file)
            dist_lib_dir = os.path.normpath(os.path.join(MSL_APPLICATION_DIR,'msl-core','src','main','libs',arch))
            logging.info('BuildAar  yuhaoo dist_dir:%s', dist_lib_dir)
            shutil.copy(output_file, dist_lib_dir)
        dist_include_dir = os.path.normpath(os.path.join(MSL_APPLICATION_DIR,'msl-core','src','main','cpp','msl','include'))
        src_include_dir = os.path.normpath(os.path.join(CORE_DIR,'sdk','src'))
        print("========src_include_dir:"+src_include_dir)
        for root, dirs, files in os.walk(src_include_dir):
            for file_path in files:
                file_name = os.path.join(root, file_path)
                # file_name = file_path
                print("========1file_name:"+file_name)
                str=r'.*\.h'
                match_obj = re.match(str,file_name)
                if match_obj:
                     print("========2file_name:"+file_name)
                     shutil.copy(file_name, dist_include_dir)
                
        # shutil.copy(output_file, dist_include_dir)
    # with zipfile.ZipFile(output_file, 'w') as aar_file:
    #     # Architecture doesn't matter here, arbitrarily using the first one.
    #     CollectCommon(aar_file, build_dir, archs[0])
    #     for arch in archs:
    #         Collect(aar_file, build_dir, arch)

    #
    print("===========build so finish")
    # 拷贝so到Android工程，目录为 third_party/ms-core/sdk/android/MSLApplication/msl-core/src/main/libs


    # 通过gradl编译msl工程生成aar
    # ' '.join(
    #     [k + '=' + _EncodeForGN(v)
    #      for k, v in extra_gn_args.items()])
    for i in extra_gn_args:
        print("index:%s value:%s" % (extra_gn_args.index(i), _EncodeForGN(i)))
    args_dic = {}
    for i, val in enumerate(extra_gn_args):
        print('=====:%d %s' % (i, val))
        arg_list = val.split('=')
        for j, item in enumerate(arg_list):
            if j % 2 == 0:
                args_dic[item] = arg_list[j + 1]
        # print(val.split('='))
    print(args_dic)
    gradle_arg=''
    if bool(args_dic['is_debug']):
        gradle_arg=':msl-core:assembleDebug'
    else:
        gradle_arg=':msl-core:assembleRelease'

    os.chdir(MSL_APPLICATION_DIR)
    cmd = "export ANDROID_SDK_ROOT={0};{1} {2} -PmslAbiFilters={3} -PmslNdkPath={4}".format(
            ANDROID_SDK_ROOT_DIR,
            './gradlew',
            gradle_arg,
            ','.join(archs),
            ANDROID_NDK_ROOT_DIR)
    logging.info('cmd:%s', cmd)
    # subprocess.call('export ANDROID_SDK_ROOT=/Volumes/kingston/workspace/Library/Android/sdk', shell=True)
    subprocess.call(cmd, shell=True)
    os.chdir(SRC_DIR)
    # 拷贝aar到相应的目录
    if bool(args_dic['is_debug']):
        aar_file_name = "msl-core-debug.aar"
    else:
        aar_file_name = "msl-core-release.aar"
    src_aar_file = os.path.normpath(os.path.join(MSL_APPLICATION_DIR,'msl-core','build','outputs','aar', aar_file_name))
    dist_aar_file = os.path.normpath(os.path.join(build_dir,'msl-core.aar'))
    shutil.copyfile(src_aar_file, dist_aar_file)    #复制并重命名文件
    if not ext_build_dir:
        shutil.rmtree(build_dir, True)


def main():
    args = _ParseArgs()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)
    # logging.info("SCRIPT_DIR:%s", SCRIPT_DIR)
    logging.info("SRC_DIR:%s", SRC_DIR)
    # logging.info("WEBRTC_DIR:%s", WEBRTC_DIR)
    # logging.info("DEFAULT_ARCHS:%s", DEFAULT_ARCHS)
    # logging.info("NEEDED_SO_FILES:%s", NEEDED_SO_FILES)
    # logging.info("JAR_FILE:%s", JAR_FILE)
    # logging.info("MANIFEST_FILE:%s", MANIFEST_FILE)
    # logging.info('info  yuhaoo args:%s', args)
    
    BuildAar(args.arch, args.output, args.extra_gn_args,
             args.build_dir, args.extra_gn_switches, args.extra_ninja_switches)

if __name__ == '__main__':
    sys.exit(main())
