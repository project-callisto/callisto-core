# example taken from
# https://coderwall.com/p/qawuyq/use-markdown-readme-s-in-python-modules

import os
import pandoc

doc = pandoc.Document()
doc.markdown = open('README.md').read()
f = open('README.txt', 'w+')
f.write(doc.rst)
f.close()
os.system('python setup.py register')
os.remove('README.txt')
