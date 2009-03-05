# setup.py
from distutils.core import setup
import py2exe

import matplotlib
setup(console=["run_browser.py"],
        options={'py2exe':{
                'includes' :['dynos', 'Numeric'],
                'packages' :['matplotlib','pytz'],
                'dll_excludes':['wxmsw26uh_vc.dll']}
                },
        data_files=[matplotlib.get_py2exe_datafiles()])
