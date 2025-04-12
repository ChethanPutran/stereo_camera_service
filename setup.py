from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="stereo_camera_service",
    version="0.1.0",
    author="Chethan",  # Update as needed
    author_email="chethansputran222@gmail.com",
    description="A Python package for interfacing Raspberry Pi with Waveshare Binocular Camera and enabling remote stereo vision services.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ChethanPutran/stereo_camera_service",  
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering :: Image Recognition",
        "Topic :: Software Development :: Embedded Systems",
    ],
    python_requires='>=3.9',
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "stereo_camera=server.camera_server:main",  
        ],
    },
)
