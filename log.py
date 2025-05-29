import logging
from pathlib import Path
from PyQt5.QtCore import QObject, pyqtSignal
from datetime import datetime

class Signaller(QObject):
    signal = pyqtSignal(str, bool)

class QtHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.signaller = Signaller()
        
    def emit(self, record):
        msg = self.format(record)
        # Error级别的日志标记为失败
        success = record.levelno < logging.ERROR
        self.signaller.signal.emit(msg, success)

def setup_logger(app_dir: Path):
    """配置日志系统"""
    # 创建主日志记录器
    logger = logging.getLogger('mp4recovery')
    logger.setLevel(logging.INFO)
    
    # 文件处理器
    log_file = app_dir/'log.log'
    fh = logging.FileHandler(log_file, encoding='utf-8', mode='a')  # 使用追加模式
    formatter = logging.Formatter('[%(asctime)s] %(message)s')
    fh.setFormatter(formatter)
    
    # 创建一个不带Qt处理器的文件记录器
    file_logger = logging.getLogger('mp4recovery.fileonly')
    file_logger.setLevel(logging.INFO)
    file_logger.propagate = False  # 阻止日志向上传播到父记录器
    file_logger.addHandler(fh)  # 只添加文件处理器
    
    # 主记录器添加文件和Qt处理器
    logger.addHandler(fh)
    qt_handler = QtHandler()
    qt_handler.setFormatter(formatter)
    logger.addHandler(qt_handler)
    
    return qt_handler.signaller.signal