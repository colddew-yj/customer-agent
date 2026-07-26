"""pytest 自动配置：把仓库根目录注入 sys.path，所有 test_* 文件不用手写。"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))