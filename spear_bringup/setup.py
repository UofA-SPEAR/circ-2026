from glob import glob
import os

from setuptools import find_packages, setup


package_name = "spear_bringup"

setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml"]),
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="UAlberta SPEAR",
    maintainer_email="software@spearrobotics.ca",
    description="Reproducible CIRC rover and base-station bringup",
    license="Proprietary",
    entry_points={
        "console_scripts": [
            "bounded_recorder = spear_bringup.bounded_recorder:main",
            "validate_competition_config = spear_bringup.config_validator:main",
        ],
    },
    extras_require={"test": ["pytest"]},
)
