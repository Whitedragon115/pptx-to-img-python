"""
API 路由模組
定義所有 API 端點
"""
from flask import request, jsonify, send_file
from datetime import datetime
import os
import time


def create_routes(app, converter, file_manager):
    """
    建立所有 API 路由
    
    Args:
        app: Flask 應用程式實例
        converter: PPTXConverter 實例
        file_manager: FileManager 實例
    """
    
    @app.route('/convert', methods=['POST'])
    def convert_pptx():
        """
        API 端點：轉換 PPTX 檔案
        """
        request_time = datetime.now()
        
        # 檢查儲存空間
        storage_available, current_size_gb, max_size_gb = file_manager.is_storage_available()
        if not storage_available:
            return jsonify({
                'error': f'儲存空間不足，目前使用 {current_size_gb:.2f}GB，超過限制 {max_size_gb:.2f}GB',
                'current_size_gb': current_size_gb,
                'max_size_gb': max_size_gb,
                'suggestion': '請使用 /cleanup/all 清理所有臨時檔案'
            }), 507  # Insufficient Storage
        
        # 檢查是否有檔案上傳
        if 'file' not in request.files:
            return jsonify({'error': '沒有檔案上傳'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '沒有選擇檔案'}), 400
        
        if not file.filename or not file.filename.lower().endswith('.pptx'):
            return jsonify({'error': '檔案必須是 PPTX 格式'}), 400
        
        try:
            # 建立臨時資料夾
            temp_folder_name, temp_folder_path = file_manager.create_temp_folder()
            
            # 儲存上傳的檔案
            timestamp = int(time.time() * 1000)
            pptx_filename = f"input_{timestamp}.pptx"
            pptx_path = os.path.join(temp_folder_path, pptx_filename)
            file.save(pptx_path)
            
            # 進行轉換
            conversion_result = converter.convert_pptx_to_all(pptx_path, temp_folder_path)
            
            if not conversion_result['success']:
                file_manager.cleanup_folder(temp_folder_path)
                return jsonify({'error': conversion_result['error']}), 500
            
            # 安排 20 分鐘後清理
            file_manager.schedule_cleanup(temp_folder_path, 20)
            
            done_time = datetime.now()
            
            # 建構回應
            response_data = {
                'request_time': request_time.isoformat(),
                'done_time': done_time.isoformat(),
                'total_pages': conversion_result['total_pages'],
                'pdf_download_url': f'/download/{temp_folder_name}/{conversion_result["pdf_file"]}',
                'image_download_urls': [
                    f'/download/{temp_folder_name}/{img}' for img in conversion_result['image_files']
                ],
                'temp_folder': temp_folder_name,
                'cleanup_scheduled': '20 minutes from request time',
                'storage_info': file_manager.get_cleanup_status()
            }
            
            return jsonify(response_data), 200
            
        except Exception as e:
            if 'temp_folder_path' in locals():
                file_manager.cleanup_folder(temp_folder_path)
            return jsonify({'error': f'處理過程中發生錯誤: {str(e)}'}), 500
    
    @app.route('/download/<folder_name>/<filename>')
    def download_file(folder_name, filename):
        """
        下載檔案端點
        """
        try:
            file_path = os.path.join(file_manager.temp_base_dir, folder_name, filename)
            
            if not os.path.exists(file_path):
                return jsonify({'error': '檔案不存在或已被清理'}), 404
            
            return send_file(file_path, as_attachment=True)
            
        except Exception as e:
            return jsonify({'error': f'下載失敗: {str(e)}'}), 500
    
    @app.route('/status/<folder_name>')
    def check_status(folder_name):
        """
        檢查臨時資料夾狀態
        """
        folder_path = os.path.join(file_manager.temp_base_dir, folder_name)
        
        if not os.path.exists(folder_path):
            return jsonify({
                'exists': False,
                'message': '資料夾不存在或已被清理'
            }), 404
        
        # 列出資料夾中的檔案
        try:
            files = os.listdir(folder_path)
            pdf_files = [f for f in files if f.endswith('.pdf')]
            image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            return jsonify({
                'exists': True,
                'folder_name': folder_name,
                'pdf_files': pdf_files,
                'image_files': image_files,
                'total_files': len(files),
                'cleanup_scheduled': folder_path in file_manager.cleanup_tasks,
                'folder_size_bytes': file_manager.get_directory_size(folder_path)
            }), 200
            
        except Exception as e:
            return jsonify({'error': f'無法讀取資料夾: {str(e)}'}), 500
    
    @app.route('/cleanup/all', methods=['POST'])
    def cleanup_all():
        """
        清理所有臨時檔案
        """
        try:
            result = file_manager.cleanup_all_temp_files()
            
            if result['success']:
                return jsonify({
                    'message': '所有臨時檔案已清理',
                    'cleaned_folders': result['cleaned_folders'],
                    'failed_folders': result['failed_folders'],
                    'total_freed_mb': round(result['total_freed_bytes'] / (1024 * 1024), 2),
                    'storage_info': file_manager.get_cleanup_status()
                }), 200
            else:
                return jsonify({
                    'error': '清理過程中發生錯誤',
                    'details': result['error']
                }), 500
                
        except Exception as e:
            return jsonify({'error': f'清理失敗: {str(e)}'}), 500
    
    @app.route('/cleanup/old', methods=['POST'])
    def cleanup_old():
        """
        清理超過 24 小時的舊檔案
        """
        try:
            max_age_hours = 24
            if request.is_json and request.json:
                max_age_hours = request.json.get('max_age_hours', 24)
            result = file_manager.cleanup_old_files(max_age_hours)
            
            if result['success']:
                return jsonify({
                    'message': f'已清理超過 {max_age_hours} 小時的舊檔案',
                    'cleaned_folders': result['cleaned_folders'],
                    'storage_info': file_manager.get_cleanup_status()
                }), 200
            else:
                return jsonify({
                    'error': '清理過程中發生錯誤',
                    'details': result['error']
                }), 500
                
        except Exception as e:
            return jsonify({'error': f'清理失敗: {str(e)}'}), 500
    
    @app.route('/storage/info')
    def storage_info():
        """
        取得儲存空間資訊
        """
        try:
            info = file_manager.get_cleanup_status()
            available, current_size_gb, max_size_gb = file_manager.is_storage_available()
            
            info.update({
                'storage_available': available,
                'warning': current_size_gb > max_size_gb * 0.8,  # 80% 警告
                'critical': not available
            })
            
            return jsonify(info), 200
            
        except Exception as e:
            return jsonify({'error': f'無法取得儲存資訊: {str(e)}'}), 500
    
    @app.route('/health')
    def health_check():
        """
        健康檢查端點
        """
        try:
            storage_available, current_size_gb, max_size_gb = file_manager.is_storage_available()
            
            return jsonify({
                'status': 'healthy' if storage_available else 'storage_full',
                'libreoffice_available': converter.is_libreoffice_available(),
                'storage_info': {
                    'available': storage_available,
                    'current_size_gb': round(current_size_gb, 2),
                    'max_size_gb': round(max_size_gb, 2),
                    'usage_percentage': round((current_size_gb / max_size_gb) * 100, 1)
                },
                'temp_folders': len(file_manager.cleanup_tasks),
                'timestamp': datetime.now().isoformat()
            }), 200
            
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }), 500
