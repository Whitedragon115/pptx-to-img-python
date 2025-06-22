# 使用 Ubuntu 基礎映像
FROM ubuntu:22.04

# 設定環境變數
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# 設定工作目錄
WORKDIR /app

# 更新套件列表並安裝系統依賴
RUN apt-get update && apt-get install -y \
    # Python 相關
    python3 \
    python3-pip \
    python3-venv \
    # LibreOffice (完整版本)
    libreoffice \
    libreoffice-writer \
    libreoffice-calc \
    libreoffice-impress \
    # Poppler 工具 (PDF 處理)
    poppler-utils \
    # 圖像處理
    imagemagick \
    # 字型支援
    fonts-liberation \
    fonts-dejavu-core \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    # X11 虛擬顯示 (LibreOffice 無頭模式需要)
    xvfb \
    # 其他工具
    curl \
    wget \
    unzip \
    # 清理
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 升級 pip
RUN python3 -m pip install --upgrade pip

# 複製 requirements 檔案
COPY requirements.txt .

# 安裝 Python 依賴
RUN pip3 install --no-cache-dir -r requirements.txt

# 複製應用程式代碼和模組
COPY api-server.py .
COPY modules/ ./modules/
COPY start_docker.sh .

# 建立必要的目錄
RUN mkdir -p /app/temp /app/uploads /app/logs

# 設定權限
RUN chmod +x /app/start_docker.sh

# 暴露端口
EXPOSE 5000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1

# 啟動命令
CMD ["/app/start_docker.sh"]
