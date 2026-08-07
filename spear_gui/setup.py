from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'spear_gui'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    package_data={
        package_name: ['*.png', '*.ttf'],
    },
    include_package_data=True,
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.py'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='root',
    maintainer_email='root@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'main_gui = spear_gui.main_gui:main',
            'camera_node = spear_gui.camera_node:main',
            'camera_sender_node = spear_gui.camera_sender_node:main',
            'camera_group_sender_node = spear_gui.camera_group_sender_node:main',
            'rover_camera_manager = spear_gui.rover_camera_manager:main',
            'camera_manager = spear_gui.camera_manager:main',
            'camera_streamer = spear_gui.camera_streamer:main',
            'current_motor_vals_gui = spear_gui.current_motor_vals_gui:main',
            'zedxone_streamer = spear_gui.zedxone_streamer:main',
            'zed_streamer = spear_gui.zed_streamer:main',
        ],
    },
)
