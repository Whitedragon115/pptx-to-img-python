# PPTX 轉換 API - Docker 部署指南

## 🐳 Docker Compose 部署

### 快速開始

1. **建置並啟動服務**
   ```bash
   docker-compose up --build
   ```

2. **背景執行**
   ```bash
   docker-compose up -d --build
   ```

3. **停止服務**
   ```bash
   docker-compose down
   ```

### 🛠️ 配置選項

#### 基本配置
編輯 `docker-compose.yml` 中的環境變數：

```yaml
environment:
  - HOST=0.0.0.0
  - PORT=5000
  - MAX_STORAGE_GB=10
  - CLEANUP_INTERVAL_MINUTES=20
  - MAX_FILE_SIZE_MB=100
  - DEFAULT_DPI=300
```

#### 資源限制
```yaml
deploy:
  resources:
    limits:
      memory: 2G
      cpus: '1.0'
```

### 🌐 服務端點

| 服務 | 端口 | 描述 |
|------|------|------|
| API 服務器 | 5000 | 主要轉換 API |
| Nginx (可選) | 80 | 反向代理 + 前端 |

### 📂 目錄掛載

- `./docker-temp:/app/temp` - 臨時檔案存儲
- `./docker-logs:/app/logs` - 日誌檔案
- `./docker-config:/app/config` - 配置檔案

### 🔧 進階選項

#### 使用 Nginx 反向代理
```bash
docker-compose --profile with-nginx up -d
```

#### 開發模式
```bash
# 使用本地代碼掛載
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 📊 監控與日誌

#### 查看日誌
```bash
# 所有服務
docker-compose logs -f

# 特定服務
docker-compose logs -f pptx-converter
```

#### 健康檢查
```bash
# 檢查服務狀態
docker-compose ps

# 手動健康檢查
curl http://localhost:5000/health
```

### 🐛 故障排除

#### 常見問題

1. **LibreOffice 無法啟動**
   ```bash
   docker-compose exec pptx-converter libreoffice --headless --version
   ```

2. **權限問題**
   ```bash
   # 修復目錄權限
   sudo chown -R 1000:1000 docker-temp docker-logs
   ```

3. **內存不足**
   - 增加 Docker 內存限制
   - 調整 `MAX_STORAGE_GB` 環境變數

#### 重建容器
```bash
# 完全重建
docker-compose down --volumes
docker-compose build --no-cache
docker-compose up -d
```

### 🔒 安全設定

#### 生產環境建議
- 設定防火牆規則
- 使用 HTTPS (Nginx SSL)
- 限制 CORS 來源
- 定期更新基礎映像

### 📈 性能優化

#### 調整並發處理
```yaml
environment:
  - FLASK_THREADED=true
  - GUNICORN_WORKERS=4
```

#### 使用 Redis 快取 (進階)
```yaml
services:
  redis:
    image: redis:alpine
    volumes:
      - redis-data:/data

volumes:
  redis-data:
```

### 🚀 部署到生產環境

#### 使用 Docker Swarm
```bash
docker stack deploy -c docker-compose.yml pptx-converter
```

#### 使用 Kubernetes
```bash
# 生成 Kubernetes 配置
kompose convert
kubectl apply -f .
```

### 📋 系統需求

- **Docker**: >= 20.10
- **Docker Compose**: >= 2.0
- **內存**: >= 1GB (建議 2GB)
- **硬碟**: >= 5GB 可用空間
- **CPU**: >= 1 核心 (建議 2 核心)

### 🔄 更新與維護

#### 更新應用程式
```bash
git pull
docker-compose build --no-cache
docker-compose up -d
```

#### 清理舊映像
```bash
docker system prune -a
docker volume prune
```

### 📞 支援

如有問題，請檢查：
1. Docker 日誌: `docker-compose logs`
2. 健康檢查: `curl http://localhost:5000/health`
3. 系統資源: `docker stats`
