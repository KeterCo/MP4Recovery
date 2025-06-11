from PyQt5.QtCore import QObject, pyqtSignal, QThread
from pathlib import Path
import subprocess
import logging
import re
import tempfile
import shutil
import time
import random

logger = logging.getLogger('mp4recovery')  # UI和文件都输出
file_logger = logging.getLogger('mp4recovery.fileonly')  # 只输出到文件

class ProcessWorker(QThread):
    progress = pyqtSignal(str, bool)
    finished = pyqtSignal()
    
    def __init__(self, processor, files):
        super().__init__()
        self.processor = processor
        self.files = files
        
    def run(self):
        for file in self.files:
            result = self.processor.process_video(file)
            # 处理结果已经通过processor的信号发出
        #self.processor.cleanup_tmp_dirs()  # 清理临时目录
        #self.tmp_manager.cleanup_tmp_dirs()  # 清理临时目录
        self.finished.emit()

class VideoProcessor(QObject):
    # 信号定义
    progress_updated = pyqtSignal(str, bool)  # 处理进度信号(消息, 是否成功)
    process_completed = pyqtSignal()  # 处理完成信号
    
    def __init__(self, ffmpeg_mgr, config_mgr, app_dir):
        super().__init__()
        self.ffmpeg_mgr = ffmpeg_mgr
        self.config_mgr = config_mgr
        self.user_dir = app_dir
        # self.created_tmp_dirs = []  # 移除
        # self.dir_tmp_map = {}       # 由外部传入

    def scan_directory(self, directory: str, recursive: bool = True) -> list:
        """扫描目录获取MP4文件列表"""
        directory = Path(directory)
        if not directory.exists() or not directory.is_dir():
            logger.error(f"目录不存在: {directory}")
            return []
        pattern = '**/*.mp4' if recursive else '*.mp4'
        
        all_files = list(directory.glob(pattern))
        skip_pattern = self.config_mgr.get('skip_pattern', '^.*meta$')
        
        try:
            regex = re.compile(skip_pattern)
            # 过滤掉匹配正则表达式的文件
            files = [f for f in all_files if not regex.search(f.stem)]
            
            # 记录跳过的文件
            skipped = [f for f in all_files if regex.search(f.stem)]
            for f in skipped:
                logger.info(f"跳过了匹配正则表达式的视频: {f}")
                #self.progress_updated.emit(f"跳过: {f.name}", True)
        except re.error as e:
            logger.error(f"正则表达式无效: {str(e)}")
            files = all_files
        
        logger.info(f"找到 {len(files)} 个需要处理的MP4文件")
        
        # 保存文件列表
        list_file = self.user_dir/'preprocesslist.txt'
        try:
            with open(list_file, 'w', encoding='utf-8') as f:
                for file in files:
                    f.write(str(file) + '\n')
        except Exception as e:
            logger.error(f"保存文件列表失败: {str(e)}")
            return []
            
        return files
        
    def process_video(self, input_file: Path, tmp_dir: Path = None):
        """处理单个视频文件，所有输出先写到tmp目录"""
        self.progress_updated.emit("\n---------------------------------------------------------------------------------------------------------------------", True)
        input_file = Path(input_file)
        suffix = self.get_output_suffix()
        orig_dir = input_file.parent

        # 只为每个目录使用外部传入的tmp
        if tmp_dir is None:
            if hasattr(self, 'dir_tmp_map') and orig_dir in self.dir_tmp_map:
                tmp_dir = self.dir_tmp_map[orig_dir]
            else:
                raise Exception("未找到临时目录映射，请检查处理流程")
        tmp_output = tmp_dir / (input_file.stem + (suffix or '') + '.mp4')
        ffmpeg_path = self.ffmpeg_mgr.get_ffmpeg_path()

        try:
            logger = logging.getLogger('mp4recovery')
            msg1 = f"原视频路径: {input_file}"
            #logger.info(msg1)
            self.progress_updated.emit(msg1, True)
            msg2 = f"正在处理: {input_file}"
            #logger.info(msg2)
            self.progress_updated.emit(msg2, True)

            # 关键：防止ffmpeg弹出cmd窗口
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            cmd = [ffmpeg_path, '-i', str(input_file), '-map_metadata', '0', '-c', 'copy', str(tmp_output)]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',  # 指定编码为UTF-8
                startupinfo=startupinfo
            )
            if result.returncode != 0:
                logger.error(f"FFmpeg错误: {result.stderr}")
                self.progress_updated.emit(f"FFmpeg错误: {result.stderr}", False)
            if not tmp_output.exists():
                msg3 = f"输出文件未生成: {input_file}"
                #logger.info(msg3)
                self.progress_updated.emit(msg3, False)
            orig_size = input_file.stat().st_size
            new_size = tmp_output.stat().st_size
            # 仅当原视频大于100MB时才判断大小差异
            if orig_size > 100 * 1024 * 1024:
                size_diff = abs(new_size - orig_size) / orig_size
                if size_diff > 0.25:
                    msg = (f"处理失败（原视频保留）: 视频大小差距过大，超过25%（原视频大于100MB才判断差距）\n"
                          f"原视频：{input_file} ({orig_size:,} 字节)\n"
                          f"生成视频：{tmp_output} ({new_size:,} 字节)")
                    tmp_output.unlink()
                    logger.error(msg)
                    self.progress_updated.emit(msg, False)
                    return False
            final_output = orig_dir / tmp_output.name
            # 如果后缀为空，直接覆盖原视频，不删除input_file
            if suffix == '':
                shutil.move(str(tmp_output), str(input_file))
                msg4 = f"成功处理，处理后视频路径: {input_file}"
                #logger.info(msg4)
                self.progress_updated.emit(msg4, True)
            else:
                shutil.move(str(tmp_output), str(final_output))
                msg5 = f"成功处理，处理后视频路径: {final_output}"
                #logger.info(msg5)
                self.progress_updated.emit(msg5, True)
                # 同步处理关联文件和删除原视频
                if self.config_mgr.get('delete_original', True):
                    if self.config_mgr.get('sync_ass', True):
                        self._sync_associated_file(input_file, suffix, '.ass')
                    if self.config_mgr.get('sync_xml', False):
                        self._sync_associated_file(input_file, suffix, '.xml')
                    input_file.unlink()
                    file_logger.info(f"删除原视频: {input_file}")
            
            return True
        except Exception as e:
            msg = f"处理失败（原视频保留）: {input_file}，错误: {str(e)}"
            logger.error(msg)
            self.progress_updated.emit(msg, False)
            if tmp_output.exists():
                tmp_output.unlink()
            return False
    
    def process_files(self, files):
        """异步处理文件列表"""
        self.worker = ProcessWorker(self, files)
        self.worker.start()
        return self.worker
    
    def get_output_suffix(self):
        """获取输出文件后缀"""
        suffix = self.config_mgr.get('output_suffix')
        if suffix is None:
            suffix = ''  # 默认后缀
        return suffix
    def _sync_associated_file(self, video_file: Path, suffix: str, ext: str):
        """同步处理关联文件"""
        associated_file = video_file.with_suffix(ext)
        if associated_file.exists():
            try:
                # 构建新文件名
                new_file = video_file.with_name(video_file.stem + suffix + ext)
                
                # 重命名关联文件
                associated_file.rename(new_file)
                file_logger.info(f"同步处理{ext}文件: {associated_file} -> {new_file}")
                logger.info(f"成功同步{ext}文件: {new_file.name}")
                
            except Exception as e:
                error_msg = f"同步处理{ext}文件失败: {str(e)}"
                logger.error(error_msg)
                file_logger.error(error_msg)
                self.progress_updated.emit(error_msg, False)

