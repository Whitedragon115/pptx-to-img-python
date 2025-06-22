"""
檔案管理模組
處理臨時檔案的建立、清理和監控
"""
import os
import shutil
import time
import threading
from datetime import datetime, timedelta


class FileManager:
    def __init__(self, temp_base_dir='temp', upload_dir='uploads', max_size_gb=10):
        self.temp_base_dir = temp_base_dir
        self.upload_dir = upload_dir
        self.max_size_bytes = max_size_gb * 1024 * 1024 * 1024  # 轉換為 bytes
        self.cleanup_tasks = {}
        
        # 確保目錄存在
        os.makedirs(self.temp_base_dir, exist_ok=True)
        os.makedirs(self.upload_dir, exist_ok=True)
    
    def get_directory_size(self, directory):
        """
        計算目錄大小（bytes）
        
        Args:
            directory (str): 目錄路徑
            
        Returns:
            int: 目錄大小（bytes）
        """
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except (OSError, IOError):
            pass
        return total_size
    
    def get_total_temp_size(self):
        """
        取得所有臨時檔案的總大小
        
        Returns:
            tuple: (size_bytes: int, size_gb: float)
        """
        size_bytes = self.get_directory_size(self.temp_base_dir)
        size_gb = size_bytes / (1024 * 1024 * 1024)
        return size_bytes, size_gb
    
    def is_storage_available(self):
        """
        檢查儲存空間是否可用（未超過 10GB 限制）
        
        Returns:
            tuple: (available: bool, current_size_gb: float, max_size_gb: float)
        """
        size_bytes, size_gb = self.get_total_temp_size()
        max_size_gb = self.max_size_bytes / (1024 * 1024 * 1024)
        return size_bytes < self.max_size_bytes, size_gb, max_size_gb
    
    def create_temp_folder(self):
        """
        建立唯一的臨時資料夾
        
        Returns:
            tuple: (folder_name: str, folder_path: str)
        """
        timestamp = int(time.time() * 1000)
        folder_name = f"temp_{timestamp}"
        folder_path = os.path.join(self.temp_base_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return folder_name, folder_path
    
    def cleanup_folder(self, folder_path):
        """
        清理指定的資料夾
        
        Args:
            folder_path (str): 要清理的資料夾路徑
            
        Returns:
            bool: 清理是否成功
        """
        try:
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                print(f"已清理資料夾: {folder_path}")
                
                # 從清理任務列表中移除
                if folder_path in self.cleanup_tasks:
                    del self.cleanup_tasks[folder_path]
                
                return True
        except Exception as e:
            print(f"清理資料夾失敗 {folder_path}: {e}")
            return False
        
        return False
    
    def schedule_cleanup(self, folder_path, delay_minutes=20):
        """
        安排資料夾清理任務
        
        Args:
            folder_path (str): 要清理的資料夾路徑
            delay_minutes (int): 延遲清理時間（分鐘）
        """
        def cleanup_task():
            time.sleep(delay_minutes * 60)
            self.cleanup_folder(folder_path)
        
        # 取消現有的清理任務（如果有）
        if folder_path in self.cleanup_tasks:
            self.cleanup_tasks[folder_path].cancel()
        
        # 建立新的清理任務
        cleanup_thread = threading.Timer(delay_minutes * 60, cleanup_task)
        cleanup_thread.daemon = True
        cleanup_thread.start()
        
        self.cleanup_tasks[folder_path] = cleanup_thread
        print(f"已安排 {delay_minutes} 分鐘後清理: {folder_path}")
    
    def cleanup_all_temp_files(self):
        """
        清理所有臨時檔案
        
        Returns:
            dict: 清理結果
        """
        result = {
            'success': False,
            'cleaned_folders': [],
            'failed_folders': [],
            'total_freed_bytes': 0,
            'error': None
        }
        
        try:
            # 取消所有清理任務
            for task in self.cleanup_tasks.values():
                if hasattr(task, 'cancel'):
                    task.cancel()
            self.cleanup_tasks.clear()
            
            # 記錄清理前的大小
            before_size = self.get_directory_size(self.temp_base_dir)
            
            # 清理所有臨時資料夾
            if os.path.exists(self.temp_base_dir):
                for item in os.listdir(self.temp_base_dir):
                    item_path = os.path.join(self.temp_base_dir, item)
                    if os.path.isdir(item_path):
                        if self.cleanup_folder(item_path):
                            result['cleaned_folders'].append(item)
                        else:
                            result['failed_folders'].append(item)
            
            # 計算釋放的空間
            after_size = self.get_directory_size(self.temp_base_dir)
            result['total_freed_bytes'] = before_size - after_size
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def cleanup_old_files(self, max_age_hours=24):
        """
        清理超過指定時間的舊檔案
        
        Args:
            max_age_hours (int): 最大檔案年齡（小時）
            
        Returns:
            dict: 清理結果
        """
        result = {
            'success': False,
            'cleaned_folders': [],
            'error': None
        }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
            
            if os.path.exists(self.temp_base_dir):
                for item in os.listdir(self.temp_base_dir):
                    item_path = os.path.join(self.temp_base_dir, item)
                    if os.path.isdir(item_path):
                        # 檢查資料夾建立時間
                        folder_time = datetime.fromtimestamp(os.path.getctime(item_path))
                        if folder_time < cutoff_time:
                            if self.cleanup_folder(item_path):
                                result['cleaned_folders'].append(item)
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def get_cleanup_status(self):
        """
        取得清理任務狀態
        
        Returns:
            dict: 狀態資訊
        """
        size_bytes, size_gb = self.get_total_temp_size()
        available, current_size, max_size = self.is_storage_available()
        
        return {
            'temp_folders_count': len(self.cleanup_tasks),
            'scheduled_cleanups': len(self.cleanup_tasks),
            'total_size_bytes': size_bytes,
            'total_size_gb': round(size_gb, 2),
            'max_size_gb': round(max_size, 2),
            'storage_available': available,
            'usage_percentage': round((current_size / max_size) * 100, 1)
        }
