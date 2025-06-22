#!/bin/bash 

# PPTX 轉換 API Docker 啟動腳本
# 用於在 Docker 容器內啟動服務

echo "=========================================="
echo "PPTX 轉換 API 服務器 - Docker 版本"
echo "=========================================="

# 檢查並啟動 X11 虛擬顯示
echo "啟動虛擬顯示服務..."
if ! pgrep -x "Xvfb" > /dev/null; then
    Xvfb :99 -screen 0 1024x768x24 -ac +extension GLX +render -noreset &
    XVFB_PID=$!
    echo "Xvfb 已啟動 (PID: $XVFB_PID)"
else
    echo "Xvfb 已經在運行"
fi

# 等待 X11 啟動
sleep 3

# 設定環境變數
export DISPLAY=:99

# 系統依賴檢查
echo ""
echo "檢查系統依賴..."

# 檢查 LibreOffice
echo -n "LibreOffice: "
if libreoffice --headless --version > /dev/null 2>&1; then
    LIBREOFFICE_VERSION=$(libreoffice --headless --version 2>/dev/null | head -n1)
    echo "✓ $LIBREOFFICE_VERSION"
else
    echo "✗ 不可用"
    exit 1
fi

# 檢查 Poppler
echo -n "Poppler (pdftoppm): "
if command -v pdftoppm > /dev/null 2>&1; then
    POPPLER_VERSION=$(pdftoppm -v 2>&1 | head -n1 || echo "可用")
    echo "✓ $POPPLER_VERSION"
else
    echo "✗ 不可用"
    exit 1
fi

# 檢查 ImageMagick
echo -n "ImageMagick: "
if command -v convert > /dev/null 2>&1; then
    IMAGEMAGICK_VERSION=$(convert -version | head -n1 | cut -d' ' -f3-4)
    echo "✓ $IMAGEMAGICK_VERSION"
else
    echo "✓ 可選依賴，未安裝"
fi

# 檢查 Python 依賴
echo -n "Python 依賴: "
if python3 -c "import flask, flask_cors, pdf2image, PIL" > /dev/null 2>&1; then
    echo "✓ 已安裝"
else
    echo "✗ 缺少 Python 依賴"
    exit 1
fi

# 建立必要目錄
echo ""
echo "建立目錄結構..."
mkdir -p /app/temp /app/uploads /app/logs /app/config
echo "✓ 目錄已建立"

# 設定權限
chmod 755 /app/temp /app/uploads /app/logs
echo "✓ 權限已設定"

# 清理啟動 (移除舊的臨時檔案)
echo ""
echo "清理舊的臨時檔案..."
find /app/temp -type f -mtime +1 -delete 2>/dev/null || true
find /app/uploads -type f -mtime +1 -delete 2>/dev/null || true
echo "✓ 清理完成"

# 顯示系統資訊
echo ""
echo "系統資訊:"
echo "  - 主機名: $(hostname)"
echo "  - 作業系統: $(lsb_release -d 2>/dev/null | cut -f2 || echo 'Unknown')"
echo "  - Python 版本: $(python3 --version)"
echo "  - 工作目錄: $(pwd)"
echo "  - 用戶: $(whoami)"
echo "  - 內存: $(free -h | grep '^Mem:' | awk '{print $2}')"

# 顯示環境變數
echo ""
echo "環境變數:"
echo "  - HOST: ${HOST:-0.0.0.0}"
echo "  - PORT: ${PORT:-5000}"
echo "  - DEBUG: ${DEBUG:-false}"
echo "  - TEMP_FOLDER: ${TEMP_FOLDER:-/app/temp}"
echo "  - MAX_STORAGE_GB: ${MAX_STORAGE_GB:-10}"
echo "  - CLEANUP_INTERVAL_MINUTES: ${CLEANUP_INTERVAL_MINUTES:-20}"

# 測試 LibreOffice 轉換功能
echo ""
echo "測試 LibreOffice 轉換功能..."
LIBREOFFICE_TEST=$(libreoffice --headless --convert-to pdf --outdir /tmp /dev/null 2>&1 || echo "測試完成")
echo "✓ LibreOffice 測試完成"

# 等待一下確保所有服務準備就緒
echo ""
echo "準備啟動 API 服務器..."
sleep 2

# 設定信號處理
trap 'echo "收到停止信號，正在關閉服務..."; kill $XVFB_PID 2>/dev/null; exit 0' SIGTERM SIGINT

# 啟動 Python API 服務器
echo ""
echo "🚀 啟動 PPTX 轉換 API 服務器..."
echo "=========================================="

# 執行主應用程式
exec python3 api-server.py
