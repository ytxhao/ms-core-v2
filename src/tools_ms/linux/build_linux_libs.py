#!/usr/bin/env python

# Based on build_aar.py

import argparse
import logging
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile

SCRIPT_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))
SRC_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir, os.pardir))
DEPOT_TOOLS_PATH = os.path.normpath(os.path.join(SRC_DIR, 'third_party', 'depot_tools'))
DEFAULT_ARCHS = ['x86_64']
TARGETS = [
    'third_party/ms-core/sdk/linux:linux',
]

def _ParseArgs():
    parser = argparse.ArgumentParser(description='Linux SDK generator.')
    parser.add_argument(
        '--build-dir',
        type=os.path.abspath,
        help='Build dir. By default will create and use temporary dir.')
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
    cmd.extend(args)
    logging.debug('Running: %r', cmd)
    subprocess.check_call(cmd)


def _RunNinja(output_directory, args):
    cmd = [
        os.path.join(DEPOT_TOOLS_PATH, 'ninja'), '-C',
        output_directory
    ]
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


def Build(build_dir, arch, use_goma, extra_gn_args, extra_gn_switches,
          extra_ninja_switches):
    """Generates target architecture using GN and builds it using ninja."""
    logging.info('Building: %s', arch)
    output_directory = _GetOutputDirectory(build_dir, arch)
    gn_args = {
        'target_os': 'linux',
        'is_debug': False,
        'is_component_build': False,
        'rtc_include_tests': False,
        'target_cpu': _GetTargetCpu(arch),
        'use_goma': use_goma
    }
    arm_version = _GetArmVersion(arch)
    if arm_version:
        gn_args['arm_version'] = arm_version
    gn_args_str = '--args=' + ' '.join(
        [k + '=' + _EncodeForGN(v)
         for k, v in gn_args.items()] + extra_gn_args)

    gn_args_list = ['gen', output_directory, gn_args_str]
    gn_args_list.extend(extra_gn_switches)
    _RunGN(gn_args_list)

    ninja_args = TARGETS[:]
    if use_goma:
        ninja_args.extend(['-j', '200'])
    ninja_args.extend(extra_ninja_switches)
    _RunNinja(output_directory, ninja_args)


def BuildSdk(archs,
             use_goma=False,
             extra_gn_args=None,
             ext_build_dir=None,
             extra_gn_switches=None,
             extra_ninja_switches=None):
    extra_gn_args = extra_gn_args or []
    extra_gn_switches = extra_gn_switches or []
    extra_ninja_switches = extra_ninja_switches or []
    build_dir = ext_build_dir if ext_build_dir else tempfile.mkdtemp()

    for arch in archs:
        Build(build_dir, arch, use_goma, extra_gn_args, extra_gn_switches,
              extra_ninja_switches)

    if not ext_build_dir:
        shutil.rmtree(build_dir, True)


def main():
    args = _ParseArgs()
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO)

    BuildSdk(args.arch, args.use_goma, args.extra_gn_args,
             args.build_dir, args.extra_gn_switches, args.extra_ninja_switches)


if __name__ == '__main__':
    sys.exit(main())
