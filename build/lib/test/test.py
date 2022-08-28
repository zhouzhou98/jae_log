from qt.manger import JaeLogManager

logger = JaeLogManager('test_nb_log_conccreent').get_logger_and_add_handlers(
                                                                              log_filename='test_nb_log_conccreent55', log_file_handler_type=2,
                                                                          )

logger.warning('xxxx')
logger.info(123456)
logger.error('434wr')