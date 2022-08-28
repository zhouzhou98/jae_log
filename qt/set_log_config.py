# -*- coding: utf-8 -*-
# @Author  : suyuzhou
# @Time    : 2022-08-20
import sys
import time
import importlib
from pathlib import Path
from shutil import copyfile
from qt.jae_print import stdout_write, stderr_write, is_main_process
from qt import config
def jae_print(*args, sep=' ', end='\n', file=None):
    args = (str(arg) for arg in args)  # REMIND 防止是数字不能被join
    if file == sys.stderr:
        stderr_write(sep.join(args))  # 如 threading 模块第926行，打印线程错误，希望保持原始的红色错误方式，不希望转成蓝色。
    else:
        # 获取被调用函数在被调用时所处代码行数
        line = sys._getframe().f_back.f_lineno
        # 获取被调用函数所在模块文件名
        file_name = sys._getframe(1).f_code.co_filename
        if config.DISPLAY_BACKGROUD_COLOR_IN_CONSOLE:
            stdout_write(
                f'\033[0;34m{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   \033[0;37;44m{sep.join(args)}\033[0m{end} \033[0m')  # 36  93 96 94
        else:
            stdout_write(
                f'\033[0;34m{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {sep.join(args)} {end} \033[0m')  # 36  93 96 94

jae_print(
    f'当前项目的根目录是：\n {sys.path[1]}')
def show_config():
    jae_print('显示log 包的默认的低优先级的配置参数')
    for var_name in dir(config):
        jae_print(var_name, getattr(config, ':', var_name))
    print('\n')


# noinspection PyProtectedMember
def use_config_form_config_module():
    line = sys._getframe().f_back.f_lineno
    file_name = sys._getframe(1).f_code.co_filename
    try:
        m = importlib.import_module('config')
        importlib.reload(m)  # 这行是防止用户在导入框架之前，写了 from config import xx 这种，导致 m.__dict__.items() 不包括所有配置变量了。
        msg = f'jae_log包 读取到\n "{m.__file__}:1" 文件里面的变量作为优先配置了\n'
        if is_main_process():
            stdout_write(f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {msg} \n \033[0m')
        for var_namex, var_valuex in m.__dict__.items():
            if var_namex.isupper():
                setattr(config, var_namex, var_valuex)
    except ModuleNotFoundError:
        auto_creat_config_file_to_project_root_path()
        msg = f'''在你的项目根目录下生成了 \n "{Path(sys.path[1]) / Path('config.py')}:1" 的jae_log包的日志配置文件，快去看看并修改一些自定义配置吧'''
        stdout_write(f'{time.strftime("%H:%M:%S")}  "{file_name}:{line}"   {msg} \n \033[0m')


def auto_creat_config_file_to_project_root_path():
    if Path(sys.path[1]).as_posix() == Path(__file__).parent.parent.absolute().as_posix():
        pass
        jae_print(f'不希望在本项目 {sys.path[1]} 里面创建 config.py')
        return
    if '/lib/python' in sys.path[1] or r'\lib\python' in sys.path[1] or '.zip' in sys.path[1]:
        raise EnvironmentError('')
    copyfile(Path(__file__).parent / Path('config.py'), Path(sys.path[1]) / Path('config.py'))
use_config_form_config_module()
