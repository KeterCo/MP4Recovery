from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout,
                            QPushButton, QLabel, QListWidget, QListWidgetItem,
                            QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from pathlib import Path
from core.tmp_dir_manager import TmpDirManager

class FileItemWidget(QWidget):
    def __init__(self, filename, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        
        # 创建删除按钮，使用大边框样式
        self.delete_btn = QPushButton("移除")
        self.delete_btn.setFixedSize(60, 30)  # 增大按钮尺寸
        self.delete_btn.setStyleSheet("""
            QPushButton {
                border: 2px solid #555555;  /* 粗边框 */
                border-radius: 5px;        /* 圆角边框 */
                font-size: 14px;           /* 字体大小 */
                padding: 5px;              /* 内边距 */
                background-color: transparent; /* 透明背景 */
                color: #333333;            /* 文字颜色 */
            }
            QPushButton:hover {
                background-color: #f0f0f0; /* 悬停背景色 */
            }
            QPushButton:pressed {
                background-color: #d0d0d0; /* 按下背景色 */
            }
        """)
        self.delete_btn.setToolTip("从列表中移除")
        
        self.label = QLabel(filename)
        
        # 改变布局顺序，将删除按钮放在左边
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.label)
        layout.addStretch()  # 添加弹性空间

class ConfirmDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tmp_manager = TmpDirManager()
        self.setup_ui()
        self.center_dialog()
        self.load_preview()
        self.is_processing = False  # 添加处理标志
        
    def setup_ui(self):
        """初始化UI"""
        self.setWindowTitle("确认处理")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)  # 设置最小高度
        
        layout = QVBoxLayout(self)
        
        # 文件列表
        self.list_widget = QListWidget()
        small_font = QFont()
        small_font.setPointSize(9)  # 设置小字体
        self.list_widget.setFont(small_font)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.show_all_btn = QPushButton("显示全部")
        self.ok_btn = QPushButton("开始处理")
        self.cancel_btn = QPushButton("取消")
        
        btn_layout.addWidget(self.show_all_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        layout.addWidget(QLabel("待处理文件预览:"))
        layout.addWidget(self.list_widget)
        layout.addLayout(btn_layout)
        
        # 信号连接
        self.show_all_btn.clicked.connect(self.show_all_files)
        self.ok_btn.clicked.connect(self.start_process)
        self.cancel_btn.clicked.connect(self.reject)
        
        # 如果父窗口有clear_log方法，先清理日志再显示全部文件
        if hasattr(self.parent(), 'clear_log'):
            def on_show_all():
                #self.parent().clear_log()
                self.show_all_files()
            self.show_all_btn.clicked.disconnect()
            self.show_all_btn.clicked.connect(on_show_all)
        
    def center_dialog(self):
        """对话框居中，按屏幕比例设置大小"""
        screen = self.screen() if hasattr(self, 'screen') else self.parent().screen()
        screen_geometry = screen.availableGeometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        # 设置对话框为屏幕的40%宽、30%高
        window_width = int(screen_width * 0.4)
        window_height = int(screen_height * 0.3)
        self.resize(window_width, window_height)
        # 居中
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.move(x, y)
        
    def load_preview(self):
        """加载预览列表"""
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        if not list_file.exists():
            return
            
        with open(list_file, encoding='utf-8') as f:
            files = [line.strip() for line in f]
            
        # 使用配置的预览数量
        preview_count = self.parent().config_mgr.get('preview_count', 20)  # 默认20
        display_count = len(files) if len(files) <= preview_count else preview_count
        for file in files[:display_count]:
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            
            widget = FileItemWidget(str(file))
            item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(item, widget)
            
            # 连接删除按钮信号
            widget.delete_btn.clicked.connect(
                lambda checked, f=file: self.remove_file(f))
            
        # 更新按钮状态
        if len(files) <= preview_count:
            self.show_all_btn.setText("已经显示全部")
            self.show_all_btn.setEnabled(False)
        else:
            more_item = QListWidgetItem(f"...还有 {len(files) - preview_count} 个文件")
            more_item.setData(Qt.UserRole, "show_all")  # 标记为特殊项
            self.list_widget.addItem(more_item)
        # 绑定点击事件
        self.list_widget.itemClicked.connect(self.on_item_clicked)

    def on_item_clicked(self, item):
        # 如果是“...还有 N 个文件”这行，触发显示全部
        if item.data(Qt.UserRole) == "show_all":
            self.show_all_files()

    def show_all_files(self):
        """显示所有未被移除的视频"""
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        if not list_file.exists():
            return

        # 读取preprocesslist.txt中所有未被移除的文件
        with open(list_file, encoding='utf-8') as f:
            all_files = [line.strip() for line in f]
            
        # 清空当前列表
        self.list_widget.clear()
        
        # 显示所有文件
        for file in all_files:
            item = QListWidgetItem()
            self.list_widget.addItem(item)
            widget = FileItemWidget(str(file))
            item.setSizeHint(widget.sizeHint())
            self.list_widget.setItemWidget(item, widget)
            # 使用partial确保每个按钮都有正确的file参数
            from functools import partial
            widget.delete_btn.clicked.connect(partial(self.remove_file, file))

        # 更新UI
        self.list_widget.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.resize(self.width(), 600)
        self.show_all_btn.setText("已显示全部视频")
        self.show_all_btn.setEnabled(False)

    def remove_file(self, file_path):
        """从列表中移除文件"""
        # 从列表控件中移除
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget and hasattr(widget, 'label') and widget.label.text() == str(file_path):
                self.list_widget.takeItem(i)
                break

        # 从预处理列表文件中移除
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        if list_file.exists():
            with open(list_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            with open(list_file, 'w', encoding='utf-8') as f:
                f.writelines(line for line in lines 
                           if line.strip() != str(file_path))
                
    def start_process(self):
        """开始处理"""
        if self.is_processing:  # 如果正在处理则返回
            return
            
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        if list_file.exists():
            with open(list_file, encoding='utf-8') as f:
                files = [Path(line.strip()) for line in f]
            if files:
                orig_dirs = set(f.parent for f in files)
                try:
                    tmp_dir_map = self.tmp_manager.create_tmp_dirs(orig_dirs)
                except Exception as e:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "错误", f"临时文件夹创建失败: {e}")
                    return
                    
                self.parent().video_processor.dir_tmp_map = tmp_dir_map
                
                # 统计变量
                self._stat_total = len(files)
                self._stat_success = 0
                self._stat_failed = 0
                self._stat_failed_files = []
                self._stat_skipped_files = []
                
                # 连接统计
                def on_progress(msg, success):
                    if msg and msg.strip():
                        if '跳过' in msg:
                            # 跳过的视频
                            for line in msg.splitlines():
                                if '跳过' in line and '.mp4' in line:
                                    self._stat_skipped_files.append(line.split(':')[-1].strip())
                        elif '成功处理' in msg:
                            self._stat_success += 1
                        elif '处理失败' in msg:
                            for line in msg.splitlines():
                                if '处理失败' in line and '.mp4' in line:
                                    self._stat_failed += 1
                                    self._stat_failed_files.append(line.split(':')[-1].strip())
                
                # 设置处理标志
                self.is_processing = True
                self.parent().video_processor.progress_updated.connect(on_progress)
                worker = self.parent().video_processor.process_files(files)
                self.ok_btn.setEnabled(False)
                
                def on_finish():
                    self.is_processing = False
                    self.ok_btn.setEnabled(True)
                    self.tmp_manager.cleanup_tmp_dirs()
                    
                    # 输出统计
                    stat_msg = f"<span style='color:orange;'><b>总计: {self._stat_total} 个视频<br>成功: {self._stat_success} 个<br>失败: {self._stat_failed} 个" \
                        + (f"<br>失败的视频为：{'；'.join(self._stat_failed_files)}" if self._stat_failed_files else "") \
                        + (f"<br>跳过的视频为：{'；'.join(self._stat_skipped_files)}" if self._stat_skipped_files else "") \
                        + "</b></span>"
                    if hasattr(self.parent(), 'log_text'):
                        self.parent().log_text.append(stat_msg)
                    # 所有处理完成后再关闭对话框    
                    self.accept()
                    
                worker.finished.connect(on_finish)
                self.accept()  # 关闭确认对话框

    def preview_files(self):
        """预览按钮逻辑，清空日志输出"""
        self.parent().clear_log()  # 只清空日志
        self.load_preview()        # 重新加载预览