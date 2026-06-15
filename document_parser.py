import os
import docx
from docx import Document
from PyPDF2 import PdfReader
from PIL import Image
import io

class DocumentParser:
    def __init__(self):
        self.supported_formats = ['.docx', '.pdf']
    
    def parse_document(self, file_path):
        """解析文档文件，返回文本内容和图片信息"""
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的文件格式: {ext}")
        
        if ext == '.docx':
            return self._parse_docx(file_path)
        elif ext == '.pdf':
            return self._parse_pdf(file_path)
    
    def _parse_docx(self, file_path):
        """解析docx文件"""
        doc = Document(file_path)
        content = []
        images = []
        images_with_data = []
        
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                content.append(text)
        
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                image_data = rel.target_part.blob
                try:
                    img = Image.open(io.BytesIO(image_data))
                    images.append({
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'size': len(image_data)
                    })
                    images_with_data.append({
                        'width': img.width,
                        'height': img.height,
                        'format': img.format,
                        'size': len(image_data),
                        'data': image_data
                    })
                except:
                    continue
        
        return {
            'text': '\n'.join(content),
            'paragraphs': content,
            'images': images,
            'images_with_data': images_with_data,
            'image_count': len(images),
            'format': 'docx'
        }
    
    def _parse_pdf(self, file_path):
        """解析PDF文件"""
        reader = PdfReader(file_path)
        content = []
        images = []
        images_with_data = []
        
        for page in reader.pages:
            text = page.extract_text()
            if text:
                content.append(text.strip())
            
            for img in page.images:
                try:
                    img_data = img.data
                    img_obj = Image.open(io.BytesIO(img_data))
                    images.append({
                        'width': img_obj.width,
                        'height': img_obj.height,
                        'format': img_obj.format,
                        'size': len(img_data)
                    })
                    images_with_data.append({
                        'width': img_obj.width,
                        'height': img_obj.height,
                        'format': img_obj.format,
                        'size': len(img_data),
                        'data': img_data
                    })
                except:
                    continue
        
        return {
            'text': '\n'.join(content),
            'paragraphs': [p for p in content if p],
            'images': images,
            'images_with_data': images_with_data,
            'image_count': len(images),
            'format': 'pdf'
        }
    
    def extract_sections(self, paragraphs):
        """从段落中提取章节结构"""
        from config import Config
        
        sections = {}
        current_section = None
        
        for para in paragraphs:
            matched = False
            for section_name, keywords in Config.SECTION_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in para:
                        current_section = section_name
                        sections[current_section] = []
                        matched = True
                        break
                if matched:
                    break
            
            if current_section and not matched:
                sections[current_section].append(para)
        
        return sections
    
    def analyze_document(self, file_path):
        """综合分析文档内容"""
        doc_info = self.parse_document(file_path)
        doc_info['sections'] = self.extract_sections(doc_info['paragraphs'])
        return doc_info
