from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'plex_ethercat'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*'))),
        (os.path.join('share', package_name, 'description/config'), glob(os.path.join('description/config', '*'))),
        (os.path.join('share', package_name, 'description/ros2_control'), glob(os.path.join('description/ros2_control', '*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='nathan',
    maintainer_email='nathanc54@shaw.ca',
    description='Shared SPEAR EtherCAT configuration for the PLEX arm and rover drive',
    license='Proprietary',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
        ],
    },
)
