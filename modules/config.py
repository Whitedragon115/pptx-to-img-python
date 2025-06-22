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
    LIBREOFFICE_PATH = os.environ.get('LIBREOFFICE_PATH', 'libreoffice')  # Docker 中使用系統路徑
    
    # 安全配置
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500MB
    ALLOWED_EXTENSIONS = {'pptx'}
    
    # CORS 配置
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
    
    @classmethod
    def validate_config(cls):
        """驗證配置是否有效"""
        errors = []
          # 檢查 LibreOffice (在 Docker 中使用 which 命令檢查)
        import shutil
        if not shutil.which(cls.LIBREOFFICE_PATH):
            # 在非 Docker 環境中檢查具體路徑
            if not os.path.exists(cls.LIBREOFFICE_PATH):
                errors.append(f"LibreOffice 未找到: {cls.LIBREOFFICE_PATH}")
        
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
