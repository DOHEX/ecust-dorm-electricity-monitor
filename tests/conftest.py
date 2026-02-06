"""测试配置文件"""

import pytest


@pytest.fixture
def test_data_dir(tmp_path):
    """创建临时数据目录"""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    return data_dir


@pytest.fixture
def test_csv_path(test_data_dir):
    """测试 CSV 文件路径"""
    return test_data_dir / "test_electricity.csv"


@pytest.fixture
def sample_config():
    """示例配置"""
    return {
        "sysid": "test_sysid",
        "roomid": "test_roomid",
        "areaid": "test_areaid",
        "buildid": "test_buildid",
    }
