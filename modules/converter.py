"""
PPTX 轉換器模組
處理 PPTX 到 PDF 和圖片的轉換
"""
import os
import shutil
import subprocess
from pdf2image import convert_from_path
from .config import Config


class PPTXConverter:
    def __init__(self):
        self.libreoffice_path = Config.LIBREOFFICE_PATH
    
    def is_libreoffice_available(self):
        """檢查 LibreOffice 是否可用"""
        # 使用 shutil.which 檢查系統路徑中的命令
        if shutil.which(self.libreoffice_path):
            return True
        # 如果是絕對路徑，檢查檔案是否存在
        if os.path.isabs(self.libreoffice_path):
            return os.path.exists(self.libreoffice_path)
        return False
    
    def convert_pptx_to_pdf(self, pptx_file, output_dir, include_hidden_slides=True):
        """
        使用 LibreOffice 將 PPTX 轉換為 PDF
        
        Args:
            pptx_file (str): PPTX 檔案路徑
            output_dir (str): 輸出目錄
            include_hidden_slides (bool): 是否包含隱藏的投影片，預設為 True
            
        Returns:
            tuple: (success: bool, result: str)
        """
        if not self.is_libreoffice_available():
            return False, "找不到 LibreOffice"
        
        pptx_path = os.path.abspath(pptx_file)
        
        # 取得 LibreOffice 實際執行檔路徑
        libreoffice_exec = shutil.which(self.libreoffice_path) or self.libreoffice_path
        
        # 根據是否包含隱藏頁面來構建命令
        if include_hidden_slides:
            cmd_pdf = [
                libreoffice_exec,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                "--infilter=impress_pdf_Export",
                "--filter-options=ExportHiddenSlides=true",
                pptx_path
            ]
        else:
            cmd_pdf = [
                libreoffice_exec,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", output_dir,
                pptx_path
            ]
        
        try:
            # 根據作業系統設定編碼
            encoding = 'cp950' if os.name == 'nt' else 'utf-8'
            
            result = subprocess.run(
                cmd_pdf, 
                capture_output=True, 
                text=True, 
                encoding=encoding, 
                errors='ignore',
                timeout=Config.CONVERSION_TIMEOUT_SECONDS
            )
            
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                return False, f"PDF 轉換失敗: {error_msg}"
            
            # 找到 PDF 檔案
            pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
            if not pdf_files:
                return False, "找不到產生的 PDF 檔案"
            
            pdf_file = os.path.join(output_dir, pdf_files[0])
            return True, pdf_file
            
        except subprocess.TimeoutExpired:
            return False, "轉換超時（5分鐘）"
        except Exception as e:
            return False, f"轉換過程中發生錯誤: {str(e)}"
    
    def convert_pdf_to_images(self, pdf_path, output_dir, dpi=200):
        """
        將 PDF 轉換為圖片
        
        Args:
            pdf_path (str): PDF 檔案路徑
            output_dir (str): 輸出目錄
            dpi (int): 圖片解析度
            
        Returns:
            tuple: (success: bool, result: list or str)
        """
        try:
            pages = convert_from_path(pdf_path, dpi=dpi)
            image_paths = []
            
            for idx, page in enumerate(pages):
                image_filename = f"page_{idx+1:03d}.jpg"
                image_path = os.path.join(output_dir, image_filename)
                page.save(image_path, "JPEG", quality=85)
                image_paths.append(image_filename)
            
            return True, image_paths
            
        except Exception as e:
            return False, f"圖片轉換失敗: {str(e)}"
    
    def convert_pptx_to_all(self, pptx_file, output_dir, dpi=200, include_hidden_slides=True):
        """
        完整轉換流程：PPTX -> PDF -> 圖片
        
        Args:
            pptx_file (str): PPTX 檔案路徑
            output_dir (str): 輸出目錄
            dpi (int): 圖片解析度
            include_hidden_slides (bool): 是否包含隱藏的投影片，預設為 True
            
        Returns:
            dict: 轉換結果
        """
        result = {
            'success': False,
            'pdf_file': None,
            'image_files': [],
            'error': None,
            'total_pages': 0
        }
        
        # 步驟 1: 轉換為 PDF
        pdf_success, pdf_result = self.convert_pptx_to_pdf(pptx_file, output_dir, include_hidden_slides)
        if not pdf_success:
            result['error'] = pdf_result
            return result
        
        result['pdf_file'] = os.path.basename(pdf_result)
        
        # 步驟 2: 轉換為圖片
        image_success, image_result = self.convert_pdf_to_images(pdf_result, output_dir, dpi)
        if not image_success:
            result['error'] = image_result
            return result
        
        result['image_files'] = image_result
        result['total_pages'] = len(image_result)
        result['success'] = True
        
        return result
