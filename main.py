import sys
import os
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from ui.main_window import MainWindow
from core.config_manager import ConfigManager
from core.ffmpeg_manager import FFmpegManager
from core.video_processor import VideoProcessor
import log

def get_app_data_dir():
    """获取应用数据目录，兼容Windows，定位到当前用户AppData/Local/Mp4recovery"""
    if os.name == 'nt':
        local_appdata = os.environ.get('LOCALAPPDATA')
        if not local_appdata:
            # 兼容极端情况
            local_appdata = str(Path.home() / 'AppData' / 'Local')
        return Path(local_appdata) / 'Mp4recovery'
    else:
        # 其他系统放在用户主目录下的隐藏文件夹
        return Path.home() / '.Mp4recovery'

def main():
    app = QApplication(sys.argv)
    
    # 确保应用数据目录存在
    app_dir = get_app_data_dir()
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # 初始化日志
    log_signal = log.setup_logger(app_dir)
    
    # 初始化各个管理器
    ffmpeg_mgr = FFmpegManager(app_dir)
    if not ffmpeg_mgr.ensure_ffmpeg():
        return
        
    config_mgr = ConfigManager(app_dir)
    video_processor = VideoProcessor(ffmpeg_mgr, config_mgr, app_dir)
    
    # 创建主窗口
    window = MainWindow(config_mgr, video_processor)
    window.show()
    
    # 连接日志信号
    log_signal.connect(window.on_progress_update)
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()