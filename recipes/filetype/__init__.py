from pythonforandroid.recipe import PythonRecipe


class FileTypeRecipe(PythonRecipe):

    # TODO: version
    url = 'https://github.com/h2non/filetype.py/archive/refs/tags/v1.2.0.zip'

    depends = ['setuptools']

    call_hostpython_via_targetpython = False

recipe = FileTypeRecipe()
