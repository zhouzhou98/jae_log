import json
import typing
from functools import lru_cache
from logging import FileHandler
from logging.handlers import WatchedFileHandler

from qt import config  # noqa
from qt.handlers import *
def revision_call_handlers(self, record):
    c = self
    found = 0
    hdlr_type_set = set()

    while c:
        for hdlr in c.handlers:
            hdlr_type = type(hdlr)
            if hdlr_type == logging.StreamHandler:  # REMIND 因为很多handler都是继承自StreamHandler，包括filehandler，直接判断会逻辑出错。
                hdlr_type = ColorHandler
            found = found + 1
            if record.levelno >= hdlr.level:
                if hdlr_type not in hdlr_type_set:
                    hdlr.handle(record)
                hdlr_type_set.add(hdlr_type)
        if not c.propagate:
            c = None  # break out
        else:
            c = c.parent
    # noinspection PyRedundantParentheses
    if (found == 0):
        if logging.lastResort:
            if record.levelno >= logging.lastResort.level:
                logging.lastResort.handle(record)
        elif logging.raiseExceptions and not self.manager.emittedNoHandlerWarning:
            sys.stderr.write("No handlers could be found for logger"
                             " \"%s\"\n" % self.name)
            sys.stderr.flush()
            self.manager.emittedNoHandlerWarning = True


# noinspection PyProtectedMember
def revision_add_handler(self, hdlr):  # 从添加源头阻止同一个logger添加同类型的handler。
    logging._acquireLock()  # noqa

    try:
        hdlrx_type_set = set()
        for hdlrx in self.handlers:
            hdlrx_type = type(hdlrx)
            if hdlrx_type == logging.StreamHandler:  # REMIND 因为很多handler都是继承自StreamHandler，包括filehandler，直接判断会逻辑出错。
                hdlrx_type = ColorHandler
            hdlrx_type_set.add(hdlrx_type)

        hdlr_type = type(hdlr)
        if hdlr_type == logging.StreamHandler:
            hdlr_type = ColorHandler
        if hdlr_type not in hdlrx_type_set:
            self.handlers.append(hdlr)
    finally:
        logging._releaseLock()  # noqa


logging.Logger.callHandlers = revision_call_handlers
logging.Logger.addHandler = revision_add_handler

class DataClassBase:
    """
    使用类实现的
    相比与字典，数据类在ide下补全犀利。
    """

    def __new__(cls, **kwargs):
        self = super().__new__(cls)
        self.__dict__ = copy.deepcopy({k: v for k, v in cls.__dict__.items() if not k.startswith('__')})
        return self

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __call__(self, ) -> dict:
        return self.get_dict()

    def get_dict(self):
        return {k: v.get_dict() if isinstance(v, DataClassBase) else v for k, v in self.__dict__.items()}

    def get_json(self):
        return json.dumps(self.get_dict(), ensure_ascii=False, indent=4)

    def __str__(self):
        return f"{self.__class__}    {self.get_json()}"

    def __getitem__(self, item):
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self, key, value)

class JaeLogManager(object):
    """
       一个日志管理类，用于创建logger和添加handler，支持将日志打印到控制台打印和写入日志文件。
       """
    logger_name_list = []
    logger_list = []
    preset_name__level_map = dict()

    def __init__(self, logger_name: typing.Union[str, None] = 'log_default_namespace'):
        self._logger_name = logger_name
        self.logger = logging.getLogger(logger_name)

    def preset_log_level(self, log_level_int=20):
        """
        提前设置锁定日志级别，当之后再设置该命名空间日志的级别的时候，按照提前预设的级别，无视之后设定的级别。
        主要是针对动态初始化的日志，在生成日志之后再去设置日志级别不方便。
        :param log_level_int:
        :return:
        """
        self.preset_name__level_map[self._logger_name] = log_level_int

    def get_logger_and_add_handlers(self, *,
                                    log_filename=None,
                                    log_path=None,
                                    log_file_handler_type: int = None):

        do_not_use_color_handler = not config.DEFAULUT_USE_COLOR_HANDLER
        log_file_size = config.LOG_FILE_SIZE
        if log_path is None:
            # print(nb_log_config_default.LOG_PATH)
            log_path = config.LOG_PATH or './logs'
        formatter_template = config.FORMATTER_KIND
        log_level_int = config.LOG_LEVEL_FILTER
        self._logger_level = log_level_int * 10 if log_level_int < 10 else log_level_int
        if log_filename is None and config.DEFAULT_ADD_MULTIPROCESSING_SAFE_ROATING_FILE_HANDLER:
            log_filename = f'{self._logger_name}{self._logger_level}.log'
        if self._logger_name in self.preset_name__level_map:
            self._logger_level2 = (self.preset_name__level_map[self._logger_name])
        else:
            self._logger_level2 = self._logger_level
        self._is_add_stream_handler = True
        self._do_not_use_color_handler = do_not_use_color_handler
        self._log_path = log_path
        self._log_filename = log_filename
        self._log_file_size = log_file_size
        if log_file_handler_type not in (None, 2, 3, 4, 1):
            raise ValueError("log_file_handler_type的值必须设置为 1 2 3 4这四个数字")
        self._log_file_handler_type = log_file_handler_type or config.LOG_FILE_HANDLER_TYPE
        self._formatter = config.FORMATTER_DICT[formatter_template]
        self.logger.setLevel(self._logger_level2)
        self.__add_handlers()
        return self.logger

    def get_logger_without_handlers(self):
        return self.logger


    def look_over_all_handlers(self):
        very_jae_print(f'{self._logger_name}名字的日志的所有handlers是--> {self.logger.handlers}')

    def remove_all_handlers(self):
        self.logger.handlers = []

    def remove_handler_by_handler_class(self, handler_class: type):

        if handler_class not in (
                logging.StreamHandler, ColorHandler, ConcurrentRotatingFileHandler):
            raise TypeError('设置的handler类型不正确')
        all_handlers = copy.copy(self.logger.handlers)
        for handler in all_handlers:
            if isinstance(handler, handler_class):
                self.logger.removeHandler(handler)  # noqa

    def __add_a_hanlder(self, handlerx: logging.Handler):
        handlerx.setLevel(10)
        handlerx.setFormatter(self._formatter)
        self.logger.addHandler(handlerx)

    def _judge_logger_has_handler_type(self, handler_type: type):
        for hr in self.logger.handlers:
            if isinstance(hr, handler_type):
                return True

    def __add_handlers(self):
        pass

        # REMIND 添加控制台日志
        if not (self._judge_logger_has_handler_type(ColorHandler) or self._judge_logger_has_handler_type(
                logging.StreamHandler)) and self._is_add_stream_handler:
            handler = ColorHandler() if not self._do_not_use_color_handler else logging.StreamHandler()
            handler.setLevel(self._logger_level2)
            self.__add_a_hanlder(handler)

        # REMIND 添加多进程安全切片的文件日志
        if not (self._judge_logger_has_handler_type(ConcurrentRotatingFileHandler) or
                self._judge_logger_has_handler_type(ConcurrentDayRotatingFileHandler) or
                self._judge_logger_has_handler_type(FileHandler) or
                self._judge_logger_has_handler_type(ConcurrentRotatingFileHandler)
        ) and all([self._log_path, self._log_filename]):
            if not os.path.exists(self._log_path):
                os.makedirs(self._log_path)
            log_file = os.path.join(self._log_path, self._log_filename)
            file_handler = None

            if self._log_file_handler_type == 1:
                file_handler = WatchedFileHandler(log_file)
            elif self._log_file_handler_type == 2:
                file_handler = ConcurrentDayRotatingFileHandler(self._log_filename, self._log_path,
                                                                back_count=config.LOG_FILE_BACKUP_COUNT)
            elif self._log_file_handler_type == 3:
                file_handler = FileHandler(log_file, mode='a', encoding='utf-8')
            elif self._log_file_handler_type == 4:
                file_handler = ConcurrentRotatingFileHandler(log_file,
                                                             maxBytes=self._log_file_size * 1024 * 1024,
                                                             backupCount=config.LOG_FILE_BACKUP_COUNT,
                                                             encoding="utf-8")
            file_handler.setLevel(self._logger_level2)
            self.__add_a_hanlder(file_handler)

    @lru_cache()  # LogManager 本身也支持无限实例化
    def get_logger(name: typing.Union[str, None], *, log_level_int: int = None, is_add_stream_handler=True,
                   do_not_use_color_handler=None, log_path=None,
                   log_filename=None, log_file_size: int = None,
                   log_file_handler_type: int = None,
                   formatter_template: int = None) -> logging.Logger:

        locals_copy = copy.copy(locals())
        locals_copy.pop('name')
        return JaeLogManager(name).get_logger_and_add_handlers(**locals_copy)

    @lru_cache()
    def get_logger_with_filehanlder(name: str) -> logging.Logger:
        """
        默认添加color handler  和 文件日志。
        :param name:
        :return:
        """
        return JaeLogManager(name).get_logger_and_add_handlers(log_filename=name + '.log')