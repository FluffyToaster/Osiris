# alternative to running osiris without console, in case issues need to be found
import os
rootdir = os.path.dirname(os.path.realpath(__file__)) + "/"
os.chdir(rootdir)
exec(open("osiris.pyw").read(-1))
