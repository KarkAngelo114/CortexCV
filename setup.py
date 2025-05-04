from setuptools import setup, find_packages

setup(
    name="CortexCV",
    version="0.0.1",
    description="CortexCV is an AI-powered python library designed to abstract away the complexities of implementing computer vision and testing your trained models to simulate real time inference prediction to new, unseen data from camera live feed",
    author="Kark Angelo",
    author_email="karkangelovaronapada@gmail.com",
    url="https://github.com/KarkAngelo114/CorteCV",
    packages=find_packages(),
    include_package_data=True,
    install_requires = [
        'opencv-python',
        'tensorflow',
        'keras',
        'psutil',
        'onnxruntime',
        'numpy',
        'pillow'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8.10",
)