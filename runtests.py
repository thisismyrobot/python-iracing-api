import doctest
import glob
import os


files = glob.glob(os.path.join('tests','*.txt'))
opts = (doctest.REPORT_ONLY_FIRST_FAILURE|doctest.ELLIPSIS|
        doctest.NORMALIZE_WHITESPACE)

for f in files:
    doctest.testfile(f, optionflags=opts)