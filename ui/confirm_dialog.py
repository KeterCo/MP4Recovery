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
        
        # 创建删除按钮，使用系统标准的关闭图标
        self.delete_btn = QPushButton("删除")
        #self.delete_btn.setIcon(self.style().standardIcon(self.style().SP_TitleBarCloseButton))
        self.delete_btn.setFixedSize(40, 20)
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
        # 预览按钮逻辑：每次点击先清空日志再加载预览
        if hasattr(self.parent(), 'clear_log'):
            self.show_all_btn.clicked.disconnect()
            self.show_all_btn.clicked.connect(self.preview_files)
        
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
            
        # 显示所有文件（如果少于20个）或前20个
        display_count = len(files) if len(files) <= 20 else 20
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
        if len(files) <= 20:
            self.show_all_btn.setText("已经显示全部")
            self.show_all_btn.setEnabled(False)
        else:
            self.list_widget.addItem(f"...还有 {len(files) - 20} 个文件")
            
    def show_all_files(self):
        """显示所有文件"""
        self.list_widget.clear()
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        
        if not list_file.exists():
            return
            
        with open(list_file, encoding='utf-8') as f:
            for line in f:
                self.list_widget.addItem(line.strip())
                
        # 调整窗口大小
        self.resize(self.width(), 600)  # 增加高度到600
        self.show_all_btn.setText("已显示全部")
        self.show_all_btn.setEnabled(False)
        
    def remove_file(self, file_path):
        """从列表中移除文件"""
        # 从列表控件中移除
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            widget = self.list_widget.itemWidget(item)
            if widget.label.text() == str(file_path):
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
        list_file = self.parent().video_processor.user_dir/'preprocesslist.txt'
        if list_file.exists():
            with open(list_file, encoding='utf-8') as f:
                files = [Path(line.strip()) for line in f]
            if files:
                # 1. 统一创建所有临时目录
                orig_dirs = set(f.parent for f in files)
                try:
                    tmp_dir_map = self.tmp_manager.create_tmp_dirs(orig_dirs)
                except Exception as e:
                    from PyQt5.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "错误", f"临时文件夹创建失败: {e}")
                    return
                # 2. 将映射传递给video_processor
                self.parent().video_processor.dir_tmp_map = tmp_dir_map
                # 3. 开始处理
                worker = self.parent().video_processor.process_files(files)
                self.ok_btn.setEnabled(False)
                def on_finish():
                    self.ok_btn.setEnabled(True)
                    # 4. 处理完成后清理临时目录
                    self.tmp_manager.cleanup_tmp_dirs()
                worker.finished.connect(on_finish)
                self.accept()  # 关闭确认对话框

    def preview_files(self):
        """预览按钮逻辑，清空日志输出"""
        self.parent().clear_log()  # 只清空日志
        self.load_preview()        # 重新加载预览