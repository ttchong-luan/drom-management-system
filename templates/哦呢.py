# 方式1：Python代码查看版本
import sqlalchemy
print("SQLAlchemy 版本：", sqlalchemy.__version__)

# 方式2：终端命令查看（推荐）
# pip list | grep sqlalchemy  # Linux/Mac
# pip list | findstr sqlalchemy  # Windows