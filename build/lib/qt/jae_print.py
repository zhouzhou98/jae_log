# -*- coding: utf-8 -*-
# @Author  : suyuzhou
# @Time    : 2022-08-20
import multiprocessing
import sys
import time
import traceback
print_raw = print

# print的另一种表达方式，添加flush
# https://blog.csdn.net/hwj_wayne/article/details/104068061?spm=1001.2101.3001.6650.1&utm_medium=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-1-104068061-blog-77680058.pc_relevant_multi_platform_whitelistv4&depth_1-utm_source=distribute.pc_relevant.none-task-blog-2%7Edefault%7ECTRLIST%7ERate-1-104068061-blog-77680058.pc_relevant_multi_platform_whitelistv4&utm_relevant_index=2
def stdout_write(msg: str):
    sys.stdout.write(msg)
    sys.stdout.flush()

# 错误的输出方式
def stderr_write(msg: str):
    sys.stderr.write(msg)
    sys.stderr.flush()

def jae_print(*args, sep=' ', end='\n', file=None, flush=True):
    args = (str(arg) for arg in args)  # REMIND 防止是数字不能被join
    if file == sys.stderr:
        stderr_write(sep.join(args))  # 如 threading 模块第926行，打印线程错误，希望保持原始的红色错误方式，不希望转成蓝色。
    elif file in [sys.stdout, None]:
        # 获取被调用函数在被调用时所处代码行数
        line = sys._getframe().f_back.f_lineno
        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename
        stdout_write(
            f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {sep.join(args)} {end}')  # 36  93 96 94
    else:  # 例如traceback模块的print_exception函数 file的入参是   <_io.StringIO object at 0x00000264F2F065E8>，必须把内容重定向到这个对象里面，否则exception日志记录不了错误堆栈。
        print_raw(*args, sep=sep, end=end, file=file)

def jae_exception(etype, value, tb, limit=None, file=None, chain=True):
    if file is None:
        file = sys.stderr
    for line in traceback.TracebackException(
        type(value), value, tb, limit=limit).format(chain=chain):
        if file != sys.stderr:
            stderr_write(f'{line} \n')
        else:
            stdout_write(f'{line} \n')

# https://blog.csdn.net/pansaky/article/details/90675290
def jae_patch_print():
    try:
        __builtins__.print = jae_print
    except AttributeError:
        __builtins__['print'] = jae_print

def common_print(*args, sep=' ', end='\n', file=None):
    args = (str(arg) for arg in args)
    if file == sys.stderr:
        stderr_write(sep.join(args) + end)
    else:
        stdout_write(sep.join(args) + end)

def reverse_patch_print():
    try:
        __builtins__.print = print_raw
    except AttributeError:
        __builtins__['print'] = print_raw

def is_main_process():
    return multiprocessing.process.current_process().name == 'MainProcess'

def only_print_on_main_process(*args, sep=' ', end='\n', file=None, flush=True):
    # 获取被调用函数在被调用时所处代码行数
    if is_main_process():
        args = (str(arg) for arg in args)  # REMIND 防止是数字不能被join
        if file == sys.stderr:
            stderr_write(sep.join(args))  # 如 threading 模块第926行，打印线程错误，希望保持原始的红色错误方式，不希望转成蓝色。
        elif file in [sys.stdout, None]:
            # 获取被调用函数在被调用时所处代码行数
            line = sys._getframe().f_back.f_lineno
            # 获取被调用函数所在模块文件名
            file_name = sys._getframe(1).f_code.co_filename
            stdout_write(
                    f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {sep.join(args)} {end}')  # 36  93 96 94
        else:
            print_raw(*args, sep=sep, end=end, file=file)

if __name__ == '__main__':
    print('before patch')
    print(0)
    jae_print(123, 'abc')
    print(456, 'def')
    print('http://www.baidu.com')

    reverse_patch_print()
    common_print('hi')

    import logging

    try:
        1 / 0
    except Exception as e:
        logging.exception(e)