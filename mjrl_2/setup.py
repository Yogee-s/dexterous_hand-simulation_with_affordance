import os
import sys
from setuptools import setup, find_packages


# Add the directory to sys.path
sys.path.append('/home/xiaoyu/Desktop/yogee/dex-affordance/mjrl_2')

if sys.version_info.major != 3:
    print("This Python is only compatible with Python 3, but you are running "
          "Python {}. The installation will likely fail.".format(sys.version_info.major))
    
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name='mjrl_2',
    version='0.1.1',
    packages=find_packages(),
    description='RL algorithms for environments in MuJoCo',
    long_description=read('README.md'),
    url='https://github.com/MovementControl/mjrl.git',
    author='Aravind Rajeswaran',
)
