#!/usr/bin/env python
# coding=utf-8

from setuptools import setup, find_packages

setup(
    name='jae_log',
    version='v0.0.1',
    description=(
        '将日志打造成jae格式'
    ),
    long_description=open('README.rst').read(),
    author='suyuzhou',
    author_email='1404031711@qq.com',
    maintainer='suyuzhou',
    maintainer_email='1404031711@qq.com',
    license='BSD License',
    packages=find_packages(),
    platforms=["all"],
    url='<项目的网址，我一般都是github的url>',
    install_requires=[
        'concurrent_log_handler',
        'filelock',
        'jsonformatter'
    ],
)