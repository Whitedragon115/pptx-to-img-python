import os
import shutil
import subprocess
import zipfile
import xml.etree.ElementTree as ET
from pdf2image import convert_from_path
from .config import Config

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False


class PPTXConverter:
    def __init__(self):
        self.libreoffice_path = Config.LIBREOFFICE_PATH
    
    def is_libreoffice_available(self):
        if shutil.which(self.libreoffice_path):
            return True
        
        if os.path.isabs(self.libreoffice_path) and os.path.exists(self.libreoffice_path):
            return True
            
        common_paths = [
            'C:\\Program Files\\LibreOffice\\program\\soffice.exe',
            'C:\\Program Files (x86)\\LibreOffice\\program\\soffice.exe',
            '/usr/bin/libreoffice',
            '/opt/libreoffice/program/soffice'
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                self.libreoffice_path = path
                return True
                
        return False
    
    def _process_hidden_slides(self, pptx_file, output_dir):
        try:
            base_name = os.path.splitext(os.path.basename(pptx_file))[0]
            processed_file = os.path.join(output_dir, f"{base_name}_unhidden.pptx")
            shutil.copy2(pptx_file, processed_file)

            with zipfile.ZipFile(processed_file, 'r') as zin:
                file_buffer = {name: zin.read(name) for name in zin.namelist()}

            namespaces = {
                'p': 'http://schemas.openxmlformats.org/presentationml/2006/main',
                'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
            }
            ET.register_namespace('', namespaces['p'])
            ET.register_namespace('r', namespaces['r'])

            if 'ppt/presentation.xml' in file_buffer:
                presentation_root = ET.fromstring(file_buffer['ppt/presentation.xml'])
                slide_refs = presentation_root.findall('.//p:sldId', namespaces)
                for slide_ref in slide_refs:
                    if slide_ref.get('show') == '0':
                        slide_ref.set('show', '1')
                    elif slide_ref.get('show') is None:
                        slide_ref.set('show', '1')
                file_buffer['ppt/presentation.xml'] = ET.tostring(presentation_root, encoding='utf-8', xml_declaration=True)

            slide_files = [name for name in file_buffer if name.startswith('ppt/slides/slide') and name.endswith('.xml')]
            for slide_file in slide_files:
                try:
                    slide_root = ET.fromstring(file_buffer[slide_file])
                    if slide_root.tag.endswith('sld'):
                        if 'show' in slide_root.attrib and slide_root.attrib['show'] == '0':
                            slide_root.attrib['show'] = '1'
                        elif 'show' not in slide_root.attrib:
                            slide_root.attrib['show'] = '1'
                        file_buffer[slide_file] = ET.tostring(slide_root, encoding='utf-8', xml_declaration=True)
                except Exception:
                    continue

            with zipfile.ZipFile(processed_file + '.tmp', 'w', zipfile.ZIP_DEFLATED) as zout:
                for name, data in file_buffer.items():
                    zout.writestr(name, data)
            shutil.move(processed_file + '.tmp', processed_file)
            return processed_file
        except Exception:
            return None
    
    def convert_pptx_to_pdf(self, pptx_file, output_dir, include_hidden_slides=True):
        if not self.is_libreoffice_available():
            return False, "找不到 LibreOffice"

        original_file = pptx_file
        if include_hidden_slides and PPTX_AVAILABLE:
            processed_file = self._process_hidden_slides(pptx_file, output_dir)
            if processed_file:
                pptx_file = processed_file

        pptx_path = os.path.abspath(pptx_file)
        
        libreoffice_exec = shutil.which(self.libreoffice_path) or self.libreoffice_path
        
        if not os.path.exists(libreoffice_exec) and not shutil.which(libreoffice_exec):
            return False, f"LibreOffice 執行檔不存在: {libreoffice_exec}"
        
        os.makedirs(output_dir, exist_ok=True)
        
        cmd_pdf = [
            libreoffice_exec,
            "--headless",
            "--invisible",
            "--convert-to", "pdf",
            "--outdir", output_dir,
            pptx_path
        ]
        
        try:
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
            
            import time
            time.sleep(1)
            
            pdf_files = [f for f in os.listdir(output_dir) if f.endswith('.pdf')]
            
            if not pdf_files:
                return False, "找不到產生的 PDF 檔案"
            
            pdf_file = os.path.join(output_dir, pdf_files[0])
            
            if pptx_file != original_file and os.path.exists(pptx_file):
                try:
                    os.remove(pptx_file)
                except:
                    pass
            
            return True, pdf_file
            
        except subprocess.TimeoutExpired:
            return False, "轉換超時（5分鐘）"
        except Exception as e:
            return False, f"轉換過程中發生錯誤: {str(e)}"
    
    def convert_pdf_to_images(self, pdf_path, output_dir, dpi=200):
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
        result = {
            'success': False,
            'pdf_file': None,
            'image_files': [],
            'error': None,
            'total_pages': 0,
            'hidden_slides_processed': False
        }
        
        pdf_success, pdf_result = self.convert_pptx_to_pdf(pptx_file, output_dir, include_hidden_slides)
        if not pdf_success:
            result['error'] = pdf_result
            return result
        
        result['pdf_file'] = os.path.basename(pdf_result)
        result['hidden_slides_processed'] = include_hidden_slides and PPTX_AVAILABLE
        
        image_success, image_result = self.convert_pdf_to_images(pdf_result, output_dir, dpi)
        if not image_success:
            result['error'] = image_result
            result['success'] = True
            result['total_pages'] = 0
            result['image_files'] = []
            return result
        
        result['image_files'] = image_result
        result['total_pages'] = len(image_result)
        result['success'] = True
        
        return result
