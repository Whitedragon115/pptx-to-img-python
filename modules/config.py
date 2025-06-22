"""
配置模組
包含所有系統配置設定
"""
import os
import shutil


class Config:
    """應用程式配置類別"""
    
    # Flask 配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'pptx-converter-secret-key'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # 檔案系統配置
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    TEMP_FOLDER = os.environ.get('TEMP_FOLDER', 'temp')
    MAX_STORAGE_GB = float(os.environ.get('MAX_STORAGE_GB', 10))
    
    # 清理配置
    DEFAULT_CLEANUP_MINUTES = int(os.environ.get('DEFAULT_CLEANUP_MINUTES', 20))
    AUTO_CLEANUP_OLD_FILES_HOURS = int(os.environ.get('AUTO_CLEANUP_OLD_FILES_HOURS', 24))
      # 轉換配置
    DEFAULT_DPI = int(os.environ.get('DEFAULT_DPI', 200))
    CONVERSION_TIMEOUT_SECONDS = int(os.environ.get('CONVERSION_TIMEOUT_SECONDS', 300))
    
    # LibreOffice 配置
    # Docker 環境使用系統路徑，Windows 環境使用絕對路徑
    if os.environ.get('DOCKER_ENV') == 'true':
        LIBREOFFICE_PATH = os.environ.get('LIBREOFFICE_PATH', 'libreoffice')
    else:
        # Windows 預設路徑
        LIBREOFFICE_PATH = os.environ.get('LIBREOFFICE_PATH', 'soffice')
    
    # 安全配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB    ALLOWED_EXTENSIONS = {'pptx'}
    
    # CORS 配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    @classmethod
    def validate_config(cls):
        """驗證配置是否有效"""
        errors = []
        
        # 檢查 LibreOffice 可用性
        libreoffice_available = False
        
        # 先嘗試使用 shutil.which 檢查系統路徑
        if shutil.which(cls.LIBREOFFICE_PATH):
            libreoffice_available = True
        # 如果是絕對路徑，檢查檔案是否存在
        elif os.path.isabs(cls.LIBREOFFICE_PATH) and os.path.exists(cls.LIBREOFFICE_PATH):
            libreoffice_available = True
        # 嘗試常見的 LibreOffice 安裝路徑
        else:
            common_paths = [
                'C:\\Program Files\\LibreOffice\\program\\soffice.exe',
                'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',
                '/usr/bin/libreoffice',
                '/opt/libreoffice/program/soffice'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    cls.LIBREOFFICE_PATH = path
                    libreoffice_available = True
                    break
        
        if not libreoffice_available:
            errors.append(f"LibreOffice 未找到: {cls.LIBREOFFICE_PATH}")
            errors.append("請確認 LibreOffice 已安裝或設定正確的 LIBREOFFICE_PATH 環境變數")
        
        # 檢查目錄權限
        try:
            os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
            os.makedirs(cls.TEMP_FOLDER, exist_ok=True)
        except PermissionError as e:
            errors.append(f"目錄權限錯誤: {e}")
        
        # 檢查數值範圍
        if cls.MAX_STORAGE_GB <= 0:
            errors.append("MAX_STORAGE_GB 必須大於 0")
        
        if cls.DEFAULT_CLEANUP_MINUTES <= 0:
            errors.append("DEFAULT_CLEANUP_MINUTES 必須大於 0")
        
        return errors
    
    @classmethod
    def get_config_info(cls):
        """取得配置資訊摘要"""
        return {
            'storage': {
                'max_size_gb': cls.MAX_STORAGE_GB,
                'temp_folder': cls.TEMP_FOLDER,
                'upload_folder': cls.UPLOAD_FOLDER
            },
            'cleanup': {
                'default_minutes': cls.DEFAULT_CLEANUP_MINUTES,
                'auto_cleanup_hours': cls.AUTO_CLEANUP_OLD_FILES_HOURS
            },
            'conversion': {
                'default_dpi': cls.DEFAULT_DPI,
                'timeout_seconds': cls.CONVERSION_TIMEOUT_SECONDS,
                'max_file_size_mb': cls.MAX_CONTENT_LENGTH / (1024 * 1024)
            },            'libreoffice': {
                'path': cls.LIBREOFFICE_PATH,
                'available': shutil.which(cls.LIBREOFFICE_PATH) is not None or os.path.exists(cls.LIBREOFFICE_PATH)
            }
        }
