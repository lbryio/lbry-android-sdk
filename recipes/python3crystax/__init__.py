from pythonforandroid.recipe import TargetPythonRecipe
from pythonforandroid.toolchain import shprint, current_directory
from pythonforandroid.logger import info, error
from pythonforandroid.util import ensure_dir, temp_directory
from os.path import exists, join
import os
import glob
import sh
from sh import Command

# This is the content of opensslconf.h taken from
# ndkdir/build/tools/build-target-openssl.sh
OPENSSLCONF = """#if defined(__ARM_ARCH_5TE__)
#include "opensslconf_armeabi.h"
#elif defined(__ARM_ARCH_7A__) && !defined(__ARM_PCS_VFP)
#include "opensslconf_armeabi_v7a.h"
#elif defined(__ARM_ARCH_7A__) && defined(__ARM_PCS_VFP)
#include "opensslconf_armeabi_v7a_hard.h"
#elif defined(__aarch64__)
#include "opensslconf_arm64_v8a.h"
#elif defined(__i386__)
#include "opensslconf_x86.h"
#elif defined(__x86_64__)
#include "opensslconf_x86_64.h"
#elif defined(__mips__) && !defined(__mips64)
#include "opensslconf_mips.h"
#elif defined(__mips__) && defined(__mips64)
#include "opensslconf_mips64.h"
#else
#error "Unsupported ABI"
#endif
"""
LATEST_FULL_VERSION = {
    '3.5': '3.5.1',
    '3.6': '3.6.6',
    '3.7': '3.7.1',
    '3.9': '3.9.6',
    '3.10': '3.10.0'
}

def realpath(fname):
    """
    Own implementation of os.realpath which may be broken in some python versions
    Returns: the absolute path o

    """

    if not os.path.islink(fname):
        return os.path.abspath(fname)

    abs_path = os.path.abspath(fname).split(os.sep)[:-1]
    rel_path = os.readlink(fname)

    if os.path.abspath(rel_path) == rel_path:
        return rel_path

    rel_path = rel_path.split(os.sep)
    for folder in rel_path:
        if folder == '..':
            abs_path.pop()
        else:
            abs_path.append(folder)
    return os.sep.join(abs_path)

class Python3Recipe(TargetPythonRecipe):
    version = '3.10'
    url = ''
    name = 'python3crystax'

    depends = ['hostpython3crystax', 'sqlite3', 'openssl']
    conflicts = ['python2', 'python3']

    from_crystax = True

    def download_if_necessary(self):
        if 'openssl' in self.ctx.recipe_build_order or self.version in ('3.6', '3.7', '3.9', '3.10'):
            full_version = LATEST_FULL_VERSION[self.version]
            version_suffix = 'rc1'
            version_params = full_version.split('.')
            version_params.append(version_suffix)
            Python3Recipe.url = 'https://www.python.org/ftp/python/{0}.{1}.{2}/Python-{0}.{1}.{2}{3}.tgz'.format(*version_params)
            super(Python3Recipe, self).download_if_necessary()

    def get_dir_name(self):
        name = super(Python3Recipe, self).get_dir_name()
        name += '-version{}'.format(self.version)
        return name

    def copy_include_dir(self, source, target):
        ensure_dir(target)
        for fname in os.listdir(source):
            sh.ln('-sf', realpath(join(source, fname)), join(target, fname))

    def _patch_dev_defaults(self, fp, target_ver):
        for line in fp:
            if 'OPENSSL_VERSIONS=' in line:
                versions = line.split('"')[1].split(' ')
                if versions[0] == target_ver:
                    raise ValueError('Patch not needed')

                if target_ver in versions:
                    versions.remove(target_ver)

                versions.insert(0, target_ver)

                yield 'OPENSSL_VERSIONS="{}"\n'.format(' '.join(versions))
            else:
                yield line

    def patch_dev_defaults(self, ssl_recipe):
        def_fname = join(self.ctx.ndk_dir, 'build', 'tools', 'dev-defaults.sh')
        try:
            with open(def_fname, 'r') as fp:
                s = ''.join(self._patch_dev_defaults(fp,
                                                       str(ssl_recipe.version)))
            with open(def_fname, 'w') as fp:
                fp.write(s)

        except ValueError:
            pass

    def include_root(self, arch_name):
        return join(self.ctx.ndk_dir, 'sources', 'python', self.major_minor_version_string,
                    'include', 'python')

    def link_root(self, arch_name):
        return join(self.ctx.ndk_dir, 'sources', 'python', self.major_minor_version_string,
                    'libs', arch_name)

    def check_for_sqlite3so(self, sqlite_recipe, arch):
        dynlib_dir = join(self.ctx.ndk_dir, 'sources', 'python', self.version,
                          'libs', arch.arch, 'modules')

        if os.path.exists(join(dynlib_dir, 'libsqlite3.so')):
            return 10, 'Shared object exists in ndk'

        major_version = sqlite_recipe.version.split('.')[0]
        # find out why _ssl.so is missin
        source_dir = join(self.ctx.ndk_dir, 'sources', 'sqlite', major_version)
        if not os.path.exists(source_dir):
            return 0, 'sqlite3 version not present'

        # these two path checks are lifted straight from:
        # crystax-ndk/build/tools/build-target-python.sh
        if not os.path.exists(join(source_dir, 'Android.mk')):
            return 1.1, 'Android.mk is missing in sqlite3 source'

        include_dir = join(source_dir, 'include')
        if not os.path.exists(join(include_dir, 'sqlite3.h')):
            return 1.2, 'sqlite3 include dir missing'

        # lastly a check to see whether shared objects for the correct arch
        # is present in the ndk
        if not os.path.exists(join(source_dir, 'libs', arch.arch, 'libsqlite3.a')):
            return 2, 'sqlite3 libs for this arch is missing in ndk'

        return 5, 'Ready to recompile python'


    def check_for_sslso(self, ssl_recipe, arch):
        # type: (Recipe, str)
        dynlib_dir = join(self.ctx.ndk_dir, 'sources', 'python', self.version,
                          'libs', arch.arch, 'modules')

        if os.path.exists(join(dynlib_dir, '_ssl.so')):
            return 10, 'Shared object exists in ndk'

        # find out why _ssl.so is missing
        source_dir = join(self.ctx.ndk_dir, 'sources', 'openssl', ssl_recipe.version)
        if not os.path.exists(source_dir):
            return 0, 'Openssl version not present'

        # these two path checks are lifted straight from:
        # crystax-ndk/build/tools/build-target-python.sh
        if not os.path.exists(join(source_dir, 'Android.mk')):
            return 1.1, 'Android.mk is missing in openssl source'

        include_dir = join(source_dir, 'include','openssl')
        if not os.path.exists(join(include_dir,  'opensslconf.h')):
            return 1.2, 'Openssl include dir missing'

        under_scored_arch = arch.arch.replace('-', '_')
        if not os.path.lexists(join(include_dir,
                                   'opensslconf_{}.h'.format(under_scored_arch))):
            return 1.3, 'Opensslconf arch header missing from include'

        # lastly a check to see whether shared objects for the correct arch
        # is present in the ndk
        if not os.path.exists(join(source_dir, 'libs', arch.arch)):
                return 2, 'Openssl libs for this arch is missing in ndk'

        return 5, 'Ready to recompile python'

    def find_Android_mk(self):
        openssl_dir = join(self.ctx.ndk_dir, 'sources', 'openssl')
        for version in os.listdir(openssl_dir):
            mk_path = join(openssl_dir, version, 'Android.mk')
            if os.path.exists(mk_path):
                return mk_path

    def find_sqlite3_Android_mk(self):
        sqlite_dir = join(self.ctx.ndk_dir, 'sources', 'sqlite')
        for version in os.listdir(sqlite_dir):
            mk_path = join(sqlite_dir, version, 'Android.mk')
            if os.path.exists(mk_path):
                return mk_path

    def prebuild_arch(self, arch):
        super(Python3Recipe, self).prebuild_arch(arch)
        if self.version in ('3.6', '3.7', '3.9', '3.10'):
            patches = ['remove_android_api_check{}'.format('_3.10' if self.version == '3.10' else '')]
            if self.version in ('3.6', '3.7'):
                patches += [
                    'patch_python3.6',
                    'selectors'
                ]

            if self.version in ('3.9', '3.10'):
                if self.version == '3.9':
                    patches += ['strdup']

                if self.version == '3.10':
                    patches += ['py3.10.0_posixmodule']

                patches += [
                    'patch_python3.9',
                    'platlibdir',

                    # from https://github.com/kivy/python-for-android/blob/develop/pythonforandroid/recipes/python3/__init__.py#L63
                    'pyconfig_detection',
                    'reproducible-buildinfo',
                    'py3.8.1'
                ]

                if sh.which('lld') is not None:
                    patches += ['py3.8.1_fix_cortex_a8']


            Python3Recipe.patches = []
            for patch_name in patches:
                Python3Recipe.patches.append('patch/{}.patch'.format(patch_name))

            build_dir = self.get_build_dir(arch.arch)

            # copy bundled libffi to _ctypes
            sh.cp("-r", join(self.get_recipe_dir(), 'libffi'), join(build_dir, 'Modules', '_ctypes'))

            shprint(sh.ln, '-sf',
                           realpath(join(build_dir, 'Lib/site-packages/README.txt')),
                           join(build_dir, 'Lib/site-packages/README'))
            python_build_files = ['android.mk', 'config.c', 'interpreter.c']
            ndk_build_tools_python_dir = join(self.ctx.ndk_dir, 'build', 'tools', 'build-target-python')
            for python_build_file in python_build_files:
                shprint(sh.cp, join(self.get_recipe_dir(), '{}.{}'.format(python_build_file, self.version)),
                               join(ndk_build_tools_python_dir, '{}.{}'.format(python_build_file, self.version)))
            ndk_sources_python_dir = join(self.ctx.ndk_dir, 'sources', 'python')
            if not os.path.exists(join(ndk_sources_python_dir, self.version)):
                os.mkdir(join(ndk_sources_python_dir, self.version))
            sh.sed('s#3.5#{}#'.format(self.version),
                   join(ndk_sources_python_dir, '3.5/Android.mk'),
                   _out=join(ndk_sources_python_dir, '{}/Android.mk.tmp'.format(self.version)))
            sh.sed('s#{}m#{}#'.format(self.version, self.version),
                   join(ndk_sources_python_dir, '{}/Android.mk.tmp'.format(self.version)),
                   _out=join(ndk_sources_python_dir, '{}/Android.mk'.format(self.version)))
            shprint(sh.rm, '-f', join(ndk_sources_python_dir, '{}/Android.mk.tmp'.format(self.version)))

    def build_arch(self, arch):
        rebuild = False

        if self.from_crystax and 'sqlite3' in self.ctx.recipe_build_order:
            info('checking sqlite3 in crystax-python')
            sqlite_recipe = self.get_recipe('sqlite3', self.ctx)
            stage, msg = self.check_for_sqlite3so(sqlite_recipe, arch)
            major_version = sqlite_recipe.version.split('.')[0]
            info(msg)
            sqlite3_build_dir = sqlite_recipe.get_build_dir(arch.arch)
            sqlite3_ndk_dir = join(self.ctx.ndk_dir, 'sources', 'sqlite', major_version)

            if stage < 2:
                info('copying sqlite3 Android.mk to ndk')
                ensure_dir(sqlite3_ndk_dir)
                if stage < 1.2:
                    # copy include folder and Android.mk to ndk
                    mk_path = self.find_sqlite3_Android_mk()
                    if mk_path is None:
                        raise IOError('Android.mk file could not be found in '
                                      'any versions in ndk->sources->sqlite')
                    shprint(sh.cp, '-f', mk_path, sqlite3_ndk_dir)

                include_dir = join(sqlite3_build_dir, 'include')
                if stage < 1.3:
                    ndk_include_dir = join(sqlite3_ndk_dir, 'include')
                    ensure_dir(sqlite3_ndk_dir)
                    shprint(sh.cp, '-f', join(sqlite3_build_dir, 'sqlite3.h'), join(ndk_include_dir, 'sqlite3.h'))
                    shprint(sh.cp, '-f', join(sqlite3_build_dir, 'sqlite3ext.h'), join(ndk_include_dir, 'sqlite3ext.h'))

            if stage < 3:
                info('copying sqlite3 libs to ndk')
                arch_ndk_lib = join(sqlite3_ndk_dir, 'libs', arch.arch)
                ensure_dir(arch_ndk_lib)
                shprint(sh.ln, '-sf',
                               realpath(join(sqlite3_build_dir, 'libsqlite3')),
                               join(sqlite3_build_dir, 'libsqlite3.a'))
                libs = ['libs/{}/libsqlite3.a'.format(arch.arch)]
                cmd = [join(sqlite3_build_dir, lib) for lib in libs] + [arch_ndk_lib]
                shprint(sh.cp, '-f', *cmd)

            if stage < 10:
                rebuild = True

        # If openssl is needed we may have to recompile cPython to get the
        # ssl.py module working properly
        if self.from_crystax and 'openssl' in self.ctx.recipe_build_order:
            info('openssl and crystax-python combination may require '
                 'recompilation of python...')
            ssl_recipe = self.get_recipe('openssl', self.ctx)
            stage, msg = self.check_for_sslso(ssl_recipe, arch)
            stage = 0 if stage < 5 else stage
            info(msg)
            openssl_build_dir = ssl_recipe.get_build_dir(arch.arch)
            openssl_ndk_dir = join(self.ctx.ndk_dir, 'sources', 'openssl', ssl_recipe.version)

            if stage < 2:
                info('Copying openssl headers and Android.mk to ndk')
                ensure_dir(openssl_ndk_dir)
                if stage < 1.2:
                    # copy include folder and Android.mk to ndk
                    mk_path = self.find_Android_mk()
                    if mk_path is None:
                        raise IOError('Android.mk file could not be found in '
                                      'any versions in ndk->sources->openssl')
                    shprint(sh.cp, mk_path, openssl_ndk_dir)

                include_dir = join(openssl_build_dir, 'include')
                if stage < 1.3:
                    ndk_include_dir = join(openssl_ndk_dir, 'include', 'openssl')
                    self.copy_include_dir(join(include_dir, 'openssl'), ndk_include_dir)

                    target_conf = join(openssl_ndk_dir, 'include', 'openssl',
                                   'opensslconf.h')
                    shprint(sh.rm, '-f', target_conf)
                    # overwrite opensslconf.h
                    with open(target_conf, 'w') as fp:
                        fp.write(OPENSSLCONF)

                if stage < 1.4:
                    # move current conf to arch specific conf in ndk
                    under_scored_arch = arch.arch.replace('-', '_')
                    shprint(sh.ln, '-sf',
                            realpath(join(include_dir, 'openssl', 'opensslconf.h')),
                            join(openssl_ndk_dir, 'include', 'openssl',
                                 'opensslconf_{}.h'.format(under_scored_arch))
                            )

            if stage < 3:
                info('Copying openssl libs to ndk')
                arch_ndk_lib = join(openssl_ndk_dir, 'libs', arch.arch)
                ensure_dir(arch_ndk_lib)
                shprint(sh.ln, '-sf',
                               realpath(join(openssl_build_dir, 'libcrypto{}.so'.format(ssl_recipe.version))),
                               join(openssl_build_dir, 'libcrypto.so'))
                shprint(sh.ln, '-sf',
                               realpath(join(openssl_build_dir, 'libssl{}.so'.format(ssl_recipe.version))),
                               join(openssl_build_dir, 'libssl.so'))
                libs = ['libcrypto.a', 'libcrypto.so', 'libssl.a', 'libssl.so']
                cmd = [join(openssl_build_dir, lib) for lib in libs] + [arch_ndk_lib]
                shprint(sh.cp, '-f', *cmd)

            if stage < 10:
                rebuild = True

        if rebuild:
            info('Recompiling python-crystax')
            self.patch_dev_defaults(ssl_recipe)
            build_script = join(self.ctx.ndk_dir, 'build', 'tools',
                                'build-target-python.sh')

            shprint(Command(build_script),
                    '--ndk-dir={}'.format(self.ctx.ndk_dir),
                    '--abis={}'.format(arch.arch),
                    '-j5', '--verbose',
                    self.get_build_dir(arch.arch))

        info('Extracting CrystaX python3 from NDK package')
        dirn = self.ctx.get_python_install_dir()
        ensure_dir(dirn)
        self.ctx.hostpython = 'python{}'.format(self.version)

recipe = Python3Recipe()
