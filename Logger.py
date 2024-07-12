import logging
import os

class SystemLogger:
    _logger = None

    @staticmethod
    def initialize_logger():
        """初始化日志配置的方法，创建一个日志实例。"""
        logger = logging.getLogger('AppLogger')
        logger.setLevel(logging.DEBUG)

        # 确保日志目录存在
        log_directory = "logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)
        log_file_path = os.path.join(log_directory, 'app.log')

        # 设置日志文件处理器
    # 设置日志文件处理器，指定编码为 utf-8
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)

        # 设置控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # 设置格式
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 添加处理器到 logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger

    @staticmethod
    def get_logger():
        """获取已经配置好的日志实例，确保全局只有一个实例"""
        if SystemLogger._logger is None:
            SystemLogger._logger = SystemLogger.initialize_logger()
        return SystemLogger._logger

    @staticmethod
    def debug(msg):
        SystemLogger.get_logger().debug(msg)

    @staticmethod
    def info(msg1, msg2=None):
        if msg2 is not None:
            msg = f'{msg1}{msg2}'
        else:
            msg = msg1
        SystemLogger.get_logger().info(msg)


    @staticmethod
    def warning(msg):
        SystemLogger.get_logger().warning(msg)

    @staticmethod
    def error(msg):
        SystemLogger.get_logger().error(msg)

    @staticmethod
    def critical(msg):

        SystemLogger.get_logger().critical(msg)

# 使用示例
if __name__ == "__main__":
    SystemLogger.debug('This is a debug message')
    SystemLogger.info('This is an info message')
    SystemLogger.warning('This is a warning message')
    SystemLogger.error('This is an error message')
    SystemLogger.critical('This is a critical message')
