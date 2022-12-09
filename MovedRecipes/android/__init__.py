from pythonforandroid.recipe import CythonRecipe, IncludedFilesBehaviour
from pythonforandroid.util import current_directory
from pythonforandroid import logger

from os.path import join


class AndroidRecipe(IncludedFilesBehaviour, CythonRecipe):
    # name = 'android'
    version = None
    url = None

    src_filename = 'src'

    depends = [('sdl2', 'genericndkbuild'), 'pyjnius']

    config_env = {}

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env.update(self.config_env)
        return env

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        ctx_bootstrap = self.ctx.bootstrap.name

        # define macros for Cython, C, Python
        tpxi = 'DEF {} = {}\n'
        th = '#define {} {}\n'
        tpy = '{} = {}\n'

        # make sure bootstrap name is in unicode
        if isinstance(ctx_bootstrap, bytes):
            ctx_bootstrap = ctx_bootstrap.decode('utf-8')
        bootstrap = bootstrap_name = ctx_bootstrap
        is_lbry = bootstrap_name in ('lbry',)
        is_sdl2 = (bootstrap_name == "sdl2")
        if bootstrap_name in ["sdl2", "webview", "service_only", "service_library", "lbry"]:
            java_ns = u'org.kivy.android'
            jni_ns = u'org/kivy/android'
        else:
            logger.error((
                'unsupported bootstrap for android recipe: {}'
                ''.format(bootstrap_name)
            ))
            exit(1)

        config = {
            'BOOTSTRAP': bootstrap,
            'IS_SDL2': int(is_sdl2),
            'PY2': 0,
            'JAVA_NAMESPACE': java_ns,
            'JNI_NAMESPACE': jni_ns,
            'ACTIVITY_CLASS_NAME': self.ctx.activity_class_name,
            'ACTIVITY_CLASS_NAMESPACE': self.ctx.activity_class_name.replace('.', '/'),
            'SERVICE_CLASS_NAME': self.ctx.service_class_name,
        }

        # create config files for Cython, C and Python
        with (
                current_directory(self.get_build_dir(arch.arch))), (
                open(join('android', 'config.pxi'), 'w')) as fpxi, (
                open(join('android', 'config.h'), 'w')) as fh, (
                open(join('android', 'config.py'), 'w')) as fpy:

            for key, value in config.items():
                fpxi.write(tpxi.format(key, repr(value)))
                fpy.write(tpy.format(key, repr(value)))

                fh.write(th.format(
                    key,
                    value if isinstance(value, int) else '"{}"'.format(value)
                ))
                self.config_env[key] = str(value)

            if is_sdl2:
                fh.write('JNIEnv *SDL_AndroidGetJNIEnv(void);\n')
                fh.write(
                    '#define SDL_ANDROID_GetJNIEnv SDL_AndroidGetJNIEnv\n'
                )
            else:
                fh.write('JNIEnv *WebView_AndroidGetJNIEnv(void);\n')
                fh.write(
                    '#define SDL_ANDROID_GetJNIEnv WebView_AndroidGetJNIEnv\n'
                )


recipe = AndroidRecipe()

'''
from pythonforandroid.recipe import CythonRecipe, IncludedFilesBehaviour
from pythonforandroid.util import current_directory
from pythonforandroid.patching import will_build
from pythonforandroid import logger

from os.path import join


class AndroidRecipe(IncludedFilesBehaviour, CythonRecipe):
    # name = 'android'
    version = None
    url = None

    src_filename = 'src'

    depends = [('pygame', 'sdl2', 'genericndkbuild'), ('python2', 'python3crystax')]

    config_env = {}

    def get_recipe_env(self, arch):
        env = super(AndroidRecipe, self).get_recipe_env(arch)
        env.update(self.config_env)
        return env

    def prebuild_arch(self, arch):
        super(AndroidRecipe, self).prebuild_arch(arch)

        tpxi = 'DEF {} = {}\n'
        th = '#define {} {}\n'
        tpy = '{} = {}\n'

        bootstrap = bootstrap_name = self.ctx.bootstrap.name
        is_sdl2 = bootstrap_name in ('sdl2', 'sdl2python3', 'sdl2_gradle')
        is_pygame = bootstrap_name in ('pygame',)
        is_webview = bootstrap_name in ('webview',)
        is_lbry = bootstrap_name in ('lbry',)

        if is_sdl2 or is_webview or is_lbry:
            if is_sdl2:
                bootstrap = 'sdl2'
            java_ns = 'org.kivy.android'
            jni_ns = 'org/kivy/android'
        elif is_pygame:
            java_ns = 'org.renpy.android'
            jni_ns = 'org/renpy/android'
        else:
            logger.error('unsupported bootstrap for android recipe: {}'.format(bootstrap_name))
            exit(1)

        config = {
            'BOOTSTRAP': bootstrap,
            'IS_SDL2': int(is_sdl2),
            'IS_PYGAME': int(is_pygame),
            'PY2': int(will_build('python2')(self)),
            'JAVA_NAMESPACE': java_ns,
            'JNI_NAMESPACE': jni_ns,
        }

        with current_directory(self.get_build_dir(arch.arch)):
            with open(join('android', 'config.pxi'), 'w') as fpxi:
                with open(join('android', 'config.h'), 'w') as fh:
                    with open(join('android', 'config.py'), 'w') as fpy:
                        for key, value in config.items():
                            fpxi.write(tpxi.format(key, repr(value)))
                            fpy.write(tpy.format(key, repr(value)))
                            fh.write(th.format(key, value if isinstance(value, int)
                                                    else '"{}"'.format(value)))
                            self.config_env[key] = str(value)

                        if is_sdl2:
                            fh.write('JNIEnv *SDL_AndroidGetJNIEnv(void);\n')
                            fh.write('#define SDL_ANDROID_GetJNIEnv SDL_AndroidGetJNIEnv\n')
                        elif is_pygame:
                            fh.write('JNIEnv *SDL_ANDROID_GetJNIEnv(void);\n')


recipe = AndroidRecipe()
'''

'''
from pythonforandroid.recipe import CythonRecipe, Recipe, IncludedFilesBehaviour
from pythonforandroid.util import current_directory
from pythonforandroid.patching import will_build
from pythonforandroid import logger

from os.path import join


class AndroidRecipe(IncludedFilesBehaviour, CythonRecipe):
    # name = 'android'
    version = None
    url = None

    src_filename = 'src'

    depends = [('pygame', 'sdl2', 'genericndkbuild'), ('python2', 'python3crystax')]

    call_hostpython_via_targetpython = False

    config_env = {}

    def get_recipe_env(self, arch):
        env = super(AndroidRecipe, self).get_recipe_env(arch)
        env.update(self.config_env)

        target_python = Recipe.get_recipe('python2', self.ctx).get_build_dir(arch.arch)
        env['PYTHON_ROOT'] = join(target_python, 'python-install')
        env['CFLAGS'] += ' -I' + env['PYTHON_ROOT'] + '/include/python2.7'
        env['LDFLAGS'] += ' -L' + env['PYTHON_ROOT'] + '/lib' + ' -lpython2.7'

        return env

    def prebuild_arch(self, arch):
        super(AndroidRecipe, self).prebuild_arch(arch)

        tpxi = 'DEF {} = {}\n'
        th = '#define {} {}\n'
        tpy = '{} = {}\n'

        bootstrap = bootstrap_name = self.ctx.bootstrap.name
        is_sdl2 = bootstrap_name in ('sdl2', 'sdl2python3')
        is_pygame = bootstrap_name in ('pygame',)
        is_webview = bootstrap_name in ('webview')
        is_lbry = bootstrap_name in ('lbry')

        if is_sdl2 or is_webview or is_lbry:
            if is_sdl2:
                bootstrap = 'sdl2'
            java_ns = 'org.kivy.android'
            jni_ns = 'org/kivy/android'
        elif is_pygame:
            java_ns = 'org.renpy.android'
            jni_ns = 'org/renpy/android'
        else:
            logger.error('unsupported bootstrap for android recipe: {}'.format(bootstrap_name))
            exit(1)

        config = {
            'BOOTSTRAP': bootstrap,
            'IS_SDL2': int(is_sdl2),
            'IS_PYGAME': int(is_pygame),
            'PY2': int(will_build('python2')(self)),
            'JAVA_NAMESPACE': java_ns,
            'JNI_NAMESPACE': jni_ns,
        }

        with current_directory(self.get_build_dir(arch.arch)):
            with open(join('android', 'config.pxi'), 'w') as fpxi:
                with open(join('android', 'config.h'), 'w') as fh:
                    with open(join('android', 'config.py'), 'w') as fpy:
                        for key, value in config.items():
                            fpxi.write(tpxi.format(key, repr(value)))
                            fpy.write(tpy.format(key, repr(value)))
                            fh.write(th.format(key, value if isinstance(value, int)
                                                    else '"{}"'.format(value)))
                            self.config_env[key] = str(value)

                        if is_sdl2:
                            fh.write('JNIEnv *SDL_AndroidGetJNIEnv(void);\n')
                            fh.write('#define SDL_ANDROID_GetJNIEnv SDL_AndroidGetJNIEnv\n')
                        elif is_pygame:
                            fh.write('JNIEnv *SDL_ANDROID_GetJNIEnv(void);\n')


recipe = AndroidRecipe()
'''