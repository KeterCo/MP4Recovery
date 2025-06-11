import os
import string
import re
from pathlib import Path
import json
import logging

logger = logging.getLogger('mp4recovery')

def get_desktop_dir():
    """
    返回当前用户的桌面目录路径（适用于 Windows）。
    """
    return os.path.join(os.path.expanduser("~"), "Desktop")

class ConfigManager:
    DEFAULT_SUFFIX = '_meta'
    DEFAULT_SKIP_PATTERN = '^.*meta$'
    DEFAULT_PREVIEW_COUNT = 20  # 添加默认预览数量
    VALID_CHARS = f"-_.{string.ascii_letters}{string.digits}"
    
    DEFAULT_CONFIG = {
        'recursive': True,
        'last_directory': str(get_desktop_dir()),
        'output_suffix': DEFAULT_SUFFIX,
        'skip_pattern': DEFAULT_SKIP_PATTERN,
        'delete_original': True,  # 默认删除原视频
        'sync_ass': True,  # 默认同步处理.ass文件
        'sync_xml': True,  # 默认同步处理.xml文件
        'cache_chosen_ass': True,  # 新增：记忆用户选择的ass同步状态
        'cache_chosen_xml': True,  # 新增：记忆用户选择的xml同步状态
        'preview_count': DEFAULT_PREVIEW_COUNT  # 添加预览数量配置项
    }
    
    def __init__(self, app_dir):
        self.user_dir = app_dir
        self.config_file = self.user_dir/'config.json'
        self.config = self._ensure_config()
        
    def _ensure_config(self):
        """确保配置文件存在并包含所需配置项"""
        default_config = self.DEFAULT_CONFIG
        
        if not self.config_file.exists():
            self.config = default_config
            self.save_config()
            logger.info("创建默认配置文件")
            logger.info("初始化默认配置完成")
            return self.config
            
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            # 确保所有必需的配置项都存在
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {str(e)}")
            return default_config
            
    def load_config(self):
        """加载配置"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info("配置加载成功")
        except Exception as e:
            logger.error(f"加载配置失败: {str(e)}")
            self.config = {'recursive': True, 'last_directory': str(Path.home())}
            
    def save_config(self):
        """保存配置"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            #logger.info("配置保存成功")
        except Exception as e:
            logger.error(f"保存配置失败: {str(e)}")
            
    def get(self, key, default=None):
        """获取配置项"""
        return self.config.get(key, default)
        
    def set(self, key, value):
        """设置配置项"""
        self.config[key] = value
        self.save_config()
        
    def sanitize_suffix(self, suffix: str) -> str:
        """清理后缀字符串
        
        规则:
        1. 空格或空字符串返回空字符串
        2. 只允许字母、数字、中日韩文字等常规字符
        3. 过滤掉特殊字符
        """
        # 处理空格和空字符串
        if not suffix or suffix.isspace():
            return ""
            
        # 使用正则表达式保留允许的字符
        # \w: 字母数字下划线
        # \u4e00-\u9fff: 中文
        # \u3040-\u30ff: 日文
        # \uac00-\ud7af: 韩文
        import re
        pattern = r'[^\w\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]'
        clean = re.sub(pattern, '', suffix)
        
        return clean
    
    def validate_regex(self, pattern: str) -> bool:
        """验证正则表达式的有效性"""
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False