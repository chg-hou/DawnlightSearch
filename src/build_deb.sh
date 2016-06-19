# https://docs.python.org/3/distutils/builtdist.html

python3 setup.py sdist 
python3 setup.py bdist
python3 setup.py build_ext --inplace


python3 setup.py --command-packages=stdeb.command bdist_deb


