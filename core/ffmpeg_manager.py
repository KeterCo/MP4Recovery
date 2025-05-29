from pathlib import Path
import shutil
import logging

logger = logging.getLogger('mp4recovery')

class FFmpegManager:
    def __init__(self, app_dir):
        self.user_dir = app_dir
        self.ff = self.user_dir/'ffmpeg.exe'
        
    def ensure_ffmpeg(self):
        """确保FFmpeg可执行文件存在于用户目录"""
        self.user_dir.mkdir(exist_ok=True)
        
        if not self.ff.exists():
            try:
                # 先从tools目录复制
                tools_ff = Path(__file__).parent.parent/'tools'/'ffmpeg.exe'
                if tools_ff.exists():
                    shutil.copy(tools_ff, self.ff)
                    logger.info(f"已从tools目录复制FFmpeg到: {self.ff}")
                else:
                    logger.error("tools目录下未找到ffmpeg.exe")
                    return False
            except Exception as e:
                logger.error(f"复制FFmpeg时出错: {str(e)}")
                return False
                
        # 清理临时目录
        temp_dir = Path(__file__).parent/'temp'
        if temp_dir.exists():
            try:
                temp_ff = temp_dir/'ffmpeg.exe'
                if temp_ff.exists():
                    temp_ff.unlink()
                    logger.info("已清理临时目录的FFmpeg")
            except Exception as e:
                logger.error(f"清理临时文件时出错: {str(e)}")
                
        logger.info(f"使用FFmpeg路径: {self.ff}")    
        return True

    def get_ffmpeg_path(self):
        """获取FFmpeg可执行文件路径"""
        return str(self.ff) if self.ff.exists() else None