from pythonforandroid.recipe import NDKRecipe
from pythonforandroid.toolchain import shprint, shutil, current_directory
from os.path import join, exists
import sh

class Sqlite3Recipe(NDKRecipe):
    version = '3.36.0'
    # Don't forget to change the URL when changing the version
    url = 'https://www.sqlite.org/2021/sqlite-amalgamation-3360000.zip'
    generated_libraries = ['sqlite3']

    def should_build(self, arch):
        return not self.has_libs(arch, 'libsqlite3.a')

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        # Copy the Android make file
        sh.mkdir('-p', join(self.get_build_dir(arch.arch), 'jni'))
        shutil.copyfile(join(self.get_recipe_dir(), 'Android.mk'),
                        join(self.get_build_dir(arch.arch), 'jni/Android.mk'))

    def build_arch(self, arch, *extra_args):
        super().build_arch(arch)
        # Copy the static library
        # (which doesn't get placed in the libs folder for some reason so we force that to happen)
        sh.mkdir('-p', join(self.get_build_dir(arch.arch), 'libs', arch.arch))
        shutil.copyfile(join(self.get_build_dir(arch.arch), 'obj', 'local', arch.arch, 'libsqlite3.a'),
                        join(self.get_build_dir(arch.arch), 'libs', arch.arch, 'libsqlite3.a'))
        shutil.copyfile(join(self.get_build_dir(arch.arch), 'libs', arch.arch, 'libsqlite3.a'),
                        join(self.ctx.get_libs_dir(arch.arch), 'libsqlite3.a'))

    def get_recipe_env(self, arch):
        env = super().get_recipe_env(arch)
        env['NDK_PROJECT_PATH'] = self.get_build_dir(arch.arch)
        return env


recipe = Sqlite3Recipe()