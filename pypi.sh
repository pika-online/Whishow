python setup.py check
python setup.py bdist_wheel --universal
twine upload dist/*