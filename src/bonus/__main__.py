"""入口模块: python -m bonus 或 bonus 命令调用"""

import sys

from bonus.app import BonusApp
from bonus.utils.logger import get_logger, setup_logging

logger = get_logger(__name__)


def main() -> None:
    """应用入口函数"""
    setup_logging()
    logger.info("=" * 50)
    logger.info("红利 Bonus - 因果推断智能桌面应用")
    logger.info("=" * 50)

    # 支持命令行传入配置文件路径
    config_path = None
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg.endswith(".yaml") or arg.endswith(".yml"):
            config_path = arg

    try:
        app = BonusApp(config_path=config_path)
        app.run()
    except KeyboardInterrupt:
        logger.info("用户中断，退出应用")
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        print(f"应用启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
