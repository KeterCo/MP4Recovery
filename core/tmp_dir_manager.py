from pathlib import Path
import random

class TmpDirManager:
    def __init__(self):
        self.created_tmp_dirs = []  # 记录创建的tmp文件夹
        self.dir_tmp_map = {}       # 目录到tmp的映射

    def create_tmp_dirs(self, orig_dirs):
        """
        为每个原始目录创建唯一的临时目录，返回目录到临时目录的映射。
        orig_dirs: 可迭代的Path对象
        """
        self.created_tmp_dirs.clear()
        self.dir_tmp_map.clear()
        tmp_dir_map = {}
        for d in orig_dirs:
            tmp_dir = self._get_unique_tmp_dir(d)
            tmp_dir_map[d] = tmp_dir
        self.dir_tmp_map = tmp_dir_map
        return tmp_dir_map

    def _get_unique_tmp_dir(self, base_dir):
        base_dir = Path(base_dir)
        tried = set()
        while len(tried) < 100:
            rand_num = random.randint(1, 1000)
            tmp_name = f"tmp{rand_num}"
            tmp_dir = base_dir / tmp_name
            if tmp_dir.exists():
                if tmp_dir.is_dir() and not any(tmp_dir.iterdir()):
                    if tmp_dir not in self.created_tmp_dirs:
                        self.created_tmp_dirs.append(tmp_dir)
                    return tmp_dir
            else:
                tmp_dir.mkdir()
                self.created_tmp_dirs.append(tmp_dir)
                return tmp_dir
            tried.add(rand_num)
        raise Exception("无法创建临时目录")

    def cleanup_tmp_dirs(self):
        """清理所有已创建的临时目录（仅删除空目录）"""
        for tmp_dir in self.created_tmp_dirs:
            try:
                if tmp_dir.exists() and not any(tmp_dir.iterdir()):
                    tmp_dir.rmdir()
            except Exception:
                pass
        self.created_tmp_dirs.clear()
        self.dir_tmp_map.clear()
