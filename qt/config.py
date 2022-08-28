import logging
import os
from pathlib import Path  # noqa
# 默认的日志文件夹,如果不写明磁盘名，则是项目代码所在磁盘的根目录下的logs
# LOG_PATH = '/logs'
LOG_PATH = Path(__file__).absolute().parent / Path("logs")
# if os.name == 'posix':  # linux非root用户和mac用户无法操作 /pythonlogs 文件夹，没有权限，默认修改为   home/[username]  下面了。例如你的linux用户名是  xiaomin，那么默认会创建并在 /home/xiaomin/pythonlogs文件夹下写入日志文件。
#     home_path = os.environ.get("HOME", '/')  # 这个是获取linux系统的当前用户的主目录，不需要亲自设置
#     LOG_PATH = Path(home_path) / Path('pythonlogs')
# 如果不存在则创建
# if not os.path.exists(LOG_PATH):
#     os.makedirs(LOG_PATH, exist_ok=True)
LOG_FILE_HANDLER_TYPE = 2
# 对同一个日志文件，默认最多备份几个文件，超过就删除了
LOG_FILE_BACKUP_COUNT = 3
# 默认日志级别，低于此级别的日志不记录了。例如设置为INFO，那么logger.debug的不会记录，只会记录logger.info以上级别的。
LOG_LEVEL_FILTER = logging.WARN
# 单位是M,每个文件的切片大小，超过多少后就自动切割
LOG_FILE_SIZE = 1024
# 使用背景颜色
DISPLAY_BACKGROUD_COLOR_IN_CONSOLE = False
# 是否默认同时将日志记录到记log文件记事本中。
DEFAULT_ADD_MULTIPROCESSING_SAFE_ROATING_FILE_HANDLER = True
# 是否默认使用有彩的日志。
DEFAULUT_USE_COLOR_HANDLER = True
# 模板字典
FORMATTER_DICT = {
    1: logging.Formatter('%(asctime)s|%(levelname)s|thread:%(thread)d|logger:%(name)s|mdc:{}|others:{fuc: %(funcName)s, line: "%(pathname)s:%(lineno)d"}|message:%(message)s',
                          "%Y-%m-%d %H:%M:%S")
}
# 如果get_logger不指定日志模板，则默认选择第几个模板
FORMATTER_KIND = 1