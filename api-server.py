"""
PPTX 轉換 API 服務器 - 重構版本
模組化設計，包含完整的檔案管理和儲存監控功能
"""
from flask import Flask
from flask_cors import CORS
import sys
import os

# 加入模組路徑
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))

from modules.config import Config
from modules.converter import PPTXConverter
from modules.file_manager import FileManager
from modules.routes import create_routes


def create_app():
    """建立 Flask 應用程式"""
    app = Flask(__name__)
    
    # 載入配置
    app.config.from_object(Config)
    
    # 設定 CORS
    CORS(app, origins=Config.CORS_ORIGINS)
    
    # 設定檔案上傳大小限制
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    
    return app


def initialize_components():
    """初始化系統組件"""
    # 驗證配置
    config_errors = Config.validate_config()
    if config_errors:
        print("配置錯誤:")
        for error in config_errors:
            print(f"  - {error}")
        return None, None, None
      # 建立組件
    converter = PPTXConverter()
    file_manager = FileManager(
        temp_base_dir=Config.TEMP_FOLDER,
        upload_dir=Config.UPLOAD_FOLDER,
        max_size_gb=int(Config.MAX_STORAGE_GB)
    )
    
    return converter, file_manager, None


def startup_cleanup(file_manager):
    """啟動時清理舊檔案"""
    print("執行啟動清理...")
    
    # 清理所有現有的臨時檔案
    cleanup_result = file_manager.cleanup_all_temp_files()
    
    if cleanup_result['success']:
        freed_mb = cleanup_result['total_freed_bytes'] / (1024 * 1024)
        print(f"啟動清理完成:")
        print(f"  - 清理的資料夾: {len(cleanup_result['cleaned_folders'])}")
        print(f"  - 釋放空間: {freed_mb:.2f} MB")
        if cleanup_result['failed_folders']:
            print(f"  - 清理失敗: {cleanup_result['failed_folders']}")
    else:
        print(f"啟動清理失敗: {cleanup_result.get('error', '未知錯誤')}")


def print_startup_info(file_manager, converter):
    """顯示啟動資訊"""
    print("=" * 60)
    print("PPTX 轉換 API 服務器 - 重構版本")
    print("=" * 60)
    
    # 系統狀態
    print("\n系統狀態:")
    print(f"  - LibreOffice: {'可用' if converter.is_libreoffice_available() else '不可用'}")
    
    # 儲存資訊
    if file_manager:
        storage_available, current_size_gb, max_size_gb = file_manager.is_storage_available()
        usage_percent = (current_size_gb / max_size_gb) * 100
        
        print(f"  - 儲存空間: {current_size_gb:.2f}GB / {max_size_gb:.2f}GB ({usage_percent:.1f}%)")
        print(f"  - 儲存狀態: {'可用' if storage_available else '已滿'}")
    
    # 配置資訊
    config_info = Config.get_config_info()
    print(f"  - 預設清理時間: {config_info['cleanup']['default_minutes']} 分鐘")
    print(f"  - 預設 DPI: {config_info['conversion']['default_dpi']}")
    print(f"  - 最大檔案大小: {config_info['conversion']['max_file_size_mb']:.0f}MB")
      # API 端點
    print("\nAPI 端點:")
    print("  - POST   /convert              - 轉換 PPTX 檔案")
    print("           參數: file (必填), include_hidden_slides (可選, 預設true), dpi (可選, 預設200)")
    print("  - GET    /download/<folder>/<file> - 下載檔案")
    print("  - GET    /status/<folder>      - 檢查資料夾狀態")
    print("  - POST   /cleanup/all          - 清理所有臨時檔案")
    print("  - POST   /cleanup/old          - 清理舊檔案")
    print("  - GET    /storage/info         - 儲存空間資訊")
    print("  - GET    /health               - 健康檢查")
    
    print(f"\n服務器將啟動在: http://{Config.HOST}:{Config.PORT}")
    print("=" * 60)


def main():
    """主函數"""
    try:
        # 建立應用程式
        app = create_app()
        
        # 初始化組件
        converter, file_manager, error = initialize_components()
        
        if error:
            print(f"初始化失敗: {error}")
            return
        
        # 執行啟動清理
        startup_cleanup(file_manager)
        
        # 建立路由
        create_routes(app, converter, file_manager)
          # 顯示啟動資訊
        print_startup_info(file_manager, converter)
        
        # 最終儲存檢查
        if file_manager:
            storage_available, current_size_gb, max_size_gb = file_manager.is_storage_available()
            if not storage_available:
                print(f"\n⚠️  警告: 儲存空間已滿 ({current_size_gb:.2f}GB/{max_size_gb:.2f}GB)")
                print("服務器將拒絕新的轉換請求，直到清理檔案")
        
        # 啟動服務器
        print("\n🚀 服務器啟動中...")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n\n服務器已停止")
    except Exception as e:
        print(f"\n服務器啟動失敗: {e}")


if __name__ == '__main__':
    main()
