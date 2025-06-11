from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QCheckBox, QTextEdit,
                            QFileDialog, QMessageBox,QApplication,QLineEdit)
from PyQt5.QtCore import Qt, QThread
from pathlib import Path
import logging
from .confirm_dialog import ConfirmDialog

logger = logging.getLogger('mp4recovery')

class MainWindow(QMainWindow):
    def __init__(self, config_mgr, video_processor):
        super().__init__()
        self.config_mgr = config_mgr
        self.video_processor = video_processor
        self.setup_ui()
        self.load_config()
        self.center_window()
        
        # 连接视频处理器信号
        self.video_processor.progress_updated.connect(self.on_progress_update)
        
        self.is_programmatic_change = False  # 添加标志
        
    def setup_ui(self):
        """初始化UI"""
        self.setWindowTitle("MP4元数据复原工具（批量复原视频到真实时长）")
        self.setMinimumSize(800, 600)
        
        # 中心部件
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # 顶部控件
        top_layout = QHBoxLayout()
        
        # 目录选择部分
        dir_layout = QHBoxLayout()
        self.path_label = QLabel("未选择目录")
        self.path_label.setMinimumWidth(300)
        self.path_label.setToolTip(self.config_mgr.get('last_directory', '未选择目录'))
        self.select_btn = QPushButton("选择目录")
        dir_layout.addWidget(self.path_label)
        dir_layout.addWidget(self.select_btn)
        
        # 后缀设置部分
        suffix_layout = QHBoxLayout()
        suffix_label = QLabel("处理后文件名后缀：")
        self.suffix_edit = QLineEdit()
        self.suffix_edit.setMaximumWidth(100)
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_edit)
        suffix_layout.addStretch()
        
        # 正则过滤设置部分
        regex_layout = QHBoxLayout()
        regex_label = QLabel("跳过匹配正则表达式的视频：")
        self.regex_edit = QLineEdit()
        self.regex_edit.setMinimumWidth(200)
        self.reset_regex_btn = QPushButton("恢复默认设置")
        self.reset_regex_btn.setToolTip("重置为默认正则表达式和默认视频后缀")
        
        regex_layout.addWidget(regex_label)
        regex_layout.addWidget(self.regex_edit)
        regex_layout.addWidget(self.reset_regex_btn)
        regex_layout.addStretch()
        
        # 递归选项
        self.recursive_cb = QCheckBox("递归处理子文件夹")
        
        # 同步文件选项
        sync_layout = QHBoxLayout()
        self.sync_ass_cb = QCheckBox("同步更名同名.ass字幕文件")
        self.sync_xml_cb = QCheckBox("同步更名同名.xml配置文件")
        self.delete_original_cb = QCheckBox("处理成功后删除原视频")
        
        sync_layout.addWidget(self.sync_ass_cb)
        sync_layout.addWidget(self.sync_xml_cb)
        sync_layout.addWidget(self.delete_original_cb)
        sync_layout.addStretch()
        
        # 组合布局
        top_layout.addLayout(dir_layout)
        top_layout.addLayout(suffix_layout)
        top_layout.addLayout(regex_layout)
        top_layout.addWidget(self.recursive_cb)
        
        # 日志区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        
        # 处理按钮
        self.process_btn = QPushButton("开始处理")
        self.process_btn.setEnabled(False)
        
        # 布局添加
        layout.addLayout(top_layout)
        layout.addLayout(sync_layout)
        layout.addWidget(self.log_text)
        layout.addWidget(self.process_btn)
        
        # 信号连接
        self.select_btn.clicked.connect(self.select_directory)
        self.process_btn.clicked.connect(self.start_process)
        self.recursive_cb.stateChanged.connect(self.on_recursive_changed)
        self.suffix_edit.editingFinished.connect(self.on_suffix_changed)
        self.regex_edit.editingFinished.connect(self.on_regex_changed)
        self.reset_regex_btn.clicked.connect(self.reset_defaults)

        # 添加信号连接
        self.delete_original_cb.stateChanged.connect(self.on_delete_original_changed)
        self.sync_ass_cb.stateChanged.connect(self.on_sync_ass_changed)
        self.sync_xml_cb.stateChanged.connect(self.on_sync_xml_changed)

    def center_window(self):
        """窗口居中并按屏幕比例设置大小"""
        # 获取屏幕几何信息
        screen = QApplication.desktop().availableGeometry()
        screen_width = screen.width()
        screen_height = screen.height()
        
        # 设置窗口为屏幕的75%大小
        window_width = int(screen_width * 0.56)
        window_height = int(screen_height * 0.5)
        
        # 确保窗口不小于最小尺寸
        window_width = max(window_width, 800)
        window_height = max(window_height, 600)
        
        # 设置窗口大小
        self.resize(window_width, window_height)
        
        # 计算居中位置
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        # 移动窗口到居中位置
        self.move(x, y)
        
    def load_config(self):
        """加载配置"""
        # 先加载删除原视频选项
        self.delete_original_cb.setChecked(self.config_mgr.get('delete_original', True))
        
        # 根据删除原视频选项状态设置同步选项
        delete_original = self.config_mgr.get('delete_original', True)
        self.sync_ass_cb.setEnabled(delete_original)
        self.sync_xml_cb.setEnabled(delete_original)
        
        if delete_original:
            # 使用缓存的选择状态
            self.sync_ass_cb.setChecked(self.config_mgr.get('cache_chosen_ass', True))
            self.sync_xml_cb.setChecked(self.config_mgr.get('cache_chosen_xml', False))
        else:
            self.sync_ass_cb.setChecked(False)
            self.sync_xml_cb.setChecked(False)
        
        # 加载其他配置
        self.recursive_cb.setChecked(self.config_mgr.get('recursive', True))
        last_dir = self.config_mgr.get('last_directory')
        if last_dir:
            self.path_label.setText(last_dir)
            self.process_btn.setEnabled(True)
            
        # 加载后缀设置
        suffix = self.config_mgr.get('output_suffix')
        if suffix is None:
            self.suffix_edit.setPlaceholderText("配置读取失败")
        else:
            self.suffix_edit.setText(suffix)

        # 加载正则表达式设置
        pattern = self.config_mgr.get('skip_pattern')
        if pattern is None:
            self.regex_edit.setPlaceholderText("配置读取失败")
        else:
            self.regex_edit.setText(pattern)

    def select_directory(self):
        """选择目录"""
        path = QFileDialog.getExistingDirectory(
            self,
            "选择目录",
            self.path_label.text()
        )
        if path:
            self.path_label.setText(path)
            self.config_mgr.set('last_directory', path)
            self.process_btn.setEnabled(True)
            
    def on_recursive_changed(self, state):
        """递归选项改变"""
        self.config_mgr.set('recursive', bool(state))
        
    def on_progress_update(self, message, success):
        """处理进度更新"""
        color = "green" if success else "red"
        self.log_text.append(f'<span style="color: {color};">{message}</span>')
        
    def on_suffix_changed(self):
        """处理后缀更改"""
        suffix = self.suffix_edit.text()
        
        # 清理后缀
        clean_suffix = self.config_mgr.sanitize_suffix(suffix)
        
        # 更新UI和配置
        self.suffix_edit.setText(clean_suffix)
        self.config_mgr.set('output_suffix', clean_suffix)

    def on_regex_changed(self):
        """处理正则表达式更改"""
        pattern = self.regex_edit.text()
        if not pattern:  # 如果为空，使用默认值
            pattern = self.config_mgr.DEFAULT_SKIP_PATTERN
        
        if self.config_mgr.validate_regex(pattern):
            self.config_mgr.set('skip_pattern', pattern)
            self.regex_edit.setStyleSheet("")
        else:
            self.regex_edit.setStyleSheet("background-color: #FFE4E1;")  # 无效正则表达式显示淡红色背景

    def reset_defaults(self):
        """重置为默认正则表达式和默认视频后缀"""
        # 重置正则表达式
        self.regex_edit.setText(self.config_mgr.DEFAULT_SKIP_PATTERN)
        self.on_regex_changed()
        # 重置视频后缀
        default_suffix = getattr(self.config_mgr, 'DEFAULT_SUFFIX', '')
        self.suffix_edit.setText(default_suffix)
        self.on_suffix_changed()

    def start_process(self):
        """开始处理"""
        path = self.path_label.text()
        if not path:
            return
        
        # 1. 先清理旧的临时目录和映射，防止多次处理时残留
        #self.parent().video_processor.created_tmp_dirs.clear()
        #self.parent().video_processor.dir_tmp_map.clear()
        
        # 扫描文件
        files = self.video_processor.scan_directory(
            path,
            self.recursive_cb.isChecked()
        )
        
        if not files:
            QMessageBox.warning(self, "警告", "未找到MP4文件")
            return
            
        # 显示确认对话框
        dlg = ConfirmDialog(self)
        dlg.exec_()
        # if dlg.exec_():
        #     # 异步处理文件
        #     #worker = self.video_processor.process_files(files)
        #     # 禁用开始按钮，直到处理完成
        #     self.process_btn.setEnabled(False)
        #     worker.finished.connect(lambda: self.process_btn.setEnabled(True))
        
        # 4. 处理完成后清理临时目录
        #self.parent().video_processor.cleanup_tmp_dirs()

    def clear_log(self):
        """清空日志输出"""
        self.log_text.clear()

    def on_delete_original_changed(self, state):
        """删除原视频选项改变"""
        value = bool(state)
        self.config_mgr.set('delete_original', value)
        #logger.info(f"更新配置：处理成功后删除原视频 = {value}")
        
        self.is_programmatic_change = True  # 设置标志
        if not value:
            # 取消勾选时，保存当前状态到缓存
            self.config_mgr.set('cache_chosen_ass', self.sync_ass_cb.isChecked())
            self.config_mgr.set('cache_chosen_xml', self.sync_xml_cb.isChecked())
            # 禁用并取消勾选同步选项
            self.sync_ass_cb.setChecked(False)
            self.sync_xml_cb.setChecked(False)
            self.sync_ass_cb.setEnabled(False)
            self.sync_xml_cb.setEnabled(False)
        else:
            # 重新勾选时，从缓存恢复状态
            self.sync_ass_cb.setEnabled(True)
            self.sync_xml_cb.setEnabled(True)
            self.sync_ass_cb.setChecked(self.config_mgr.get('cache_chosen_ass', True))
            self.sync_xml_cb.setChecked(self.config_mgr.get('cache_chosen_xml', False))
        self.is_programmatic_change = False  # 重置标志

    def on_sync_ass_changed(self, state):
        """同步.ass选项改变"""
        value = bool(state)
        self.config_mgr.set('sync_ass', value)
        
        # 只有是用户操作且删除原视频选项被勾选时才更新缓存
        if not self.is_programmatic_change and self.delete_original_cb.isChecked():
            self.config_mgr.set('cache_chosen_ass', value)

    def on_sync_xml_changed(self, state):
        """同步.xml选项改变"""
        value = bool(state)
        self.config_mgr.set('sync_xml', value)
        
        # 只有是用户操作且删除原视频选项被勾选时才更新缓存
        if not self.is_programmatic_change and self.delete_original_cb.isChecked():
            self.config_mgr.set('cache_chosen_xml', value)