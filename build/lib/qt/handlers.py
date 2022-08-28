# noinspection PyMissingOrEmptyDocstring
import atexit
import copy
import multiprocessing
import queue
import re
import sys
import os
import traceback
import time
from pathlib import Path
from queue import Queue, Empty
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler
from filelock import FileLock
from jsonformatter import JsonFormatter
from qt import config
from threading import Lock, Thread
from qt.jae_print import jae_print
os_name = os.name

very_jae_print = jae_print

class ColorHandler(logging.Handler):
    """
    根据日志严重级别，显示成五彩控制台日志。
    强烈建议使用pycharm的 monokai主题颜色，这样日志的颜色符合常规的交通信号灯颜色指示，色彩也非常饱和鲜艳。
    设置方式为 打开pycharm的settings -> Editor -> Color Scheme -> Console Font 选择monokai
    """

    terminator = '\r\n' if os_name == 'nt' else '\n'
    bule = 96 if os_name == 'nt' else 36
    yellow = 93 if os_name == 'nt' else 33

    def __init__(self, stream=None, ):
        """
        Initialize the handler.

        If stream is not specified, sys.stderr is used.
        """
        logging.Handler.__init__(self)
        if stream is None:
            stream = sys.stdout  # stderr无彩。
        self.stream = stream
        self._display_method = 7 if os_name == 'posix' else 0

    def flush(self):
        """
        Flushes the stream.
        """
        self.acquire()
        try:
            if self.stream and hasattr(self.stream, "flush"):
                self.stream.flush()
        finally:
            self.release()

    def __build_color_msg_with_backgroud_color(self, record_level, assist_msg, effective_information_msg):
        if record_level == 10:
            msg_color = f'\033[0;32m{assist_msg}\033[0m \033[0;37;42m{effective_information_msg}\033[0m'  # 绿色
        elif record_level == 20:
            msg_color = f'\033[0;36m{assist_msg}\033[0m \033[0;37;46m{effective_information_msg}\033[0m'
        elif record_level == 30:
            msg_color = f'\033[0;33m{assist_msg}\033[0m \033[0;37;43m{effective_information_msg}\033[0m'
        elif record_level == 40:
            msg_color = f'\033[0;35m{assist_msg}\033[0m \033[0;37;45m{effective_information_msg}\033[0m'
        elif record_level == 50:
            msg_color = f'\033[0;31m{assist_msg}\033[0m \033[0;37;41m{effective_information_msg}\033[0m'
        else:
            msg_color = f'{assist_msg}  {effective_information_msg}'
        return msg_color
    def __build_color_msg_with_no_backgroud_color(self, record_level, record_copy: logging.LogRecord, ):
        complete_msg = self.format(record_copy)
        if record_level == 10:
            # msg_color = ('\033[0;32m%s\033[0m' % msg)  # 绿色
            # print(msg1)
            msg_color = f'\033[0;32m{complete_msg}\033[0m'  # 绿色
        elif record_level == 20:
            # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.bule, msg))  # 青蓝色 36    96
            msg_color = f'\033[0;36m{complete_msg}\033[0m'
        elif record_level == 30:
            # msg_color = ('\033[%s;%sm%s\033[0m' % (self._display_method, self.yellow, msg))
            msg_color = f'\033[0;33m{complete_msg}\033[0m'
        elif record_level == 40:
            # msg_color = ('\033[%s;35m%s\033[0m' % (self._display_method, msg))  # 紫红色
            msg_color = f'\033[0;31m{complete_msg}\033[0m'

        elif record_level == 50:
            # msg_color = ('\033[%s;31m%s\033[0m' % (self._display_method, msg))  # 血红色
            msg_color = f'\033[0;35m{complete_msg}\033[0m'
        else:
            msg_color = f'{complete_msg}'
        return msg_color
    def emit(self, record: logging.LogRecord):
        try:
            stream = self.stream
            msg_color = self.__build_color_msg_with_no_backgroud_color(record.levelno, copy.copy(record))
            stream.write(msg_color + self.terminator)
        except Exception as e:
            very_jae_print(e)
            very_jae_print(traceback.format_exc())
    @staticmethod
    def __spilt_msg(log_level, msg: str):
        split_text = '- 级别 -'
        if log_level == 10:
            split_text = '- DEBUG -'
        elif log_level == 20:
            split_text = '- INFO -'
        elif log_level == 30:
            split_text = '- WARNING -'
        elif log_level == 40:
            split_text = '- ERROR -'
        elif log_level == 50:
            split_text = '- CRITICAL -'
        msg_split = msg.split(split_text, maxsplit=1)
        return msg_split[0] + split_text, msg_split[-1]

    def __repr__(self):
        level = logging.getLevelName(self.level)
        name = getattr(self.stream, 'name', '')
        if name:
            name += ' '
        return '<%s %s(%s)>' % (self.__class__.__name__, name, level)


# noinspection PyPep8Naming
class ConcurrentDayRotatingFileHandlerLinux(logging.Handler):
    def __init__(self, file_name: str, file_path: str, back_count=None):
        super().__init__()
        self.file_name = file_name
        self.file_path = file_path
        self.backupCount = back_count or config.LOG_FILE_BACKUP_COUNT
        self.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
        self.extMatch2 = re.compile(r"^\d{2}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
        time_str = time.strftime('%Y-%m-%d-%H')
        self.time_str = time_str
        self._lock = multiprocessing.Lock()

    def _get_fp(self, name):
        with self._lock:
            time_str = time.strftime('%Y-%m-%d-%H')
            if time_str != self.time_str:
                try:
                    self.fp.close()
                except Exception as e:
                    logging.error(e)
                new_file_name = self.file_name + '.' + name + '.log.' + time_str
                path_obj = Path(self.file_path) / Path(new_file_name)
                path_obj.touch(exist_ok=True)
                self.fp = open(path_obj, 'a', encoding='utf-8')

    def emit(self, record: logging.LogRecord):
        name = record.levelname
        try:
            msg = self.format(record)
            time_str = time.strftime('%Y-%m-%d-%H')
            new_file_name = self.file_name + '.' + name + '.log.' + time_str
            path_obj = Path(self.file_path) / Path(new_file_name)
            path_obj.touch(exist_ok=True)
            self.fp = open(path_obj, 'a', encoding='utf-8')
            self.fp.write(msg + '\n')
        except Exception:
            self.handleError(record)
        finally:
            self._get_fp(name)
            self.fp.close()

class ConcurrentSecondRotatingFileHandlerLinux(logging.Handler):
    """ 按秒切割的多进程安全文件日志，方便测试验证"""
    def __init__(self, file_name: str, file_path: str, back_count=None):
        super().__init__()
        self.file_name = file_name
        self.file_path = file_path
        self.backupCount = back_count or config.LOG_FILE_BACKUP_COUNT
        self.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
        self.extMatch2 = re.compile(r"^\d{2}-\d{2}-\d{2}(\.\w+)?$", re.ASCII)
        time_str = time.strftime('%H-%M-%S')  # 方便测试用的，方便观察。
        new_file_name = self.file_name + '.' + time_str
        path_obj = Path(self.file_path) / Path(new_file_name)
        path_obj.touch(exist_ok=True)
        self.fp = open(path_obj, 'a', encoding='utf-8')
        self.time_str = time_str
        self._lock = multiprocessing.Lock()

    def _get_fp(self, name):
        with self._lock:
            time_str = time.strftime('%Y-%m-%d-%H')
            if time_str != self.time_str:
                try:
                    self.fp.close()
                except Exception as e:
                    print(e)
                new_file_name = self.file_name + '.' + name + '.log.' + time_str
                path_obj = Path(self.file_path) / Path(new_file_name)
                path_obj.touch(exist_ok=True)
                self.fp = open(path_obj, 'a', encoding='utf-8')

    def emit(self, record: logging.LogRecord):
        name = record.levelname
        try:
            msg = self.format(record)
            time_str = time.strftime('%Y-%m-%d-%H')
            new_file_name = self.file_name + '.' + name + '.log.' + time_str
            path_obj = Path(self.file_path) / Path(new_file_name)
            path_obj.touch(exist_ok=True)
            self.fp = open(path_obj, 'a', encoding='utf-8')
            self.fp.write(msg + '\n')
        except Exception as e:
            logging.error(e)
            self.handleError(record)
        finally:
            self._get_fp(name)
            self.fp.close()
ConcurrentDayRotatingFileHandler = ConcurrentDayRotatingFileHandlerLinux
