from setuptools import setup, find_packages

setup(
    name="grievance-schema",
    version="1.0.0",
    description="UCO contract — shared schema for grievance system services",
    packages=find_packages(),
    install_requires=["pydantic>=2.0"],
    python_requires=">=3.10",
)
