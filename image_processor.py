import os
import re
from PIL import Image
import io
from config import Config

class ImageProcessor:
    def __init__(self):
        self.min_width = Config.MIN_IMAGE_WIDTH
        self.min_height = Config.MIN_IMAGE_HEIGHT
        self.max_width = Config.MAX_IMAGE_WIDTH
        self.max_height = Config.MAX_IMAGE_HEIGHT
        self.tesseract_available = False
        
        try:
            import pytesseract
            self.tesseract_available = True
            self.pytesseract = pytesseract
        except ImportError:
            pass
    
    def validate_image_size(self, width, height):
        """验证图片尺寸是否合理"""
        if width < self.min_width or height < self.min_height:
            return False, f"图片尺寸过小 ({width}x{height})"
        if width > self.max_width or height > self.max_height:
            return False, f"图片尺寸过大 ({width}x{height})"
        return True, "图片尺寸正常"
    
    def analyze_images(self, images):
        """分析图片列表"""
        results = []
        valid_count = 0
        invalid_count = 0
        
        for i, img in enumerate(images):
            is_valid, message = self.validate_image_size(img['width'], img['height'])
            result = {
                'index': i,
                'width': img['width'],
                'height': img['height'],
                'format': img.get('format', 'unknown'),
                'size_kb': round(img.get('size', 0) / 1024, 2),
                'is_valid': is_valid,
                'message': message
            }
            results.append(result)
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
        
        return {
            'total_count': len(images),
            'valid_count': valid_count,
            'invalid_count': invalid_count,
            'details': results
        }
    
    def compare_image_counts(self, ref_count, sub_count, tolerance=None):
        """比对图片数量"""
        if tolerance is None:
            tolerance = Config.IMAGE_COUNT_TOLERANCE
        
        diff = abs(ref_count - sub_count)
        is_acceptable = diff <= tolerance
        
        return {
            'reference_count': ref_count,
            'submission_count': sub_count,
            'difference': diff,
            'is_acceptable': is_acceptable,
            'tolerance': tolerance
        }
    
    def extract_image_text(self, image_data):
        """尝试从图片中提取文本（使用OCR）"""
        if not self.tesseract_available:
            return None
        
        try:
            img = Image.open(io.BytesIO(image_data))
            text = self.pytesseract.image_to_string(img, lang='eng+chi_sim')
            return text.strip()
        except Exception as e:
            return None
    
    def extract_code_from_text(self, text):
        """从文本中提取代码片段"""
        if not text:
            return []
        
        code_patterns = [
            r'```(\w+)?\n([\s\S]*?)```',
            r'`([^`]+)`',
            r'(def\s+\w+\([^)]*\)|function\s+\w+\([^)]*\)|class\s+\w+)',
            r'([a-zA-Z_][a-zA-Z0-9_]*\s*=\s*[\'"][^\'"]*[\'"]|\d+\s*[+\-*/]\s*\d+)',
            r'(import\s+\w+|from\s+\w+\s+import)',
            r'(\/\/.*|#.*)'
        ]
        
        code_snippets = []
        for pattern in code_patterns:
            matches = re.findall(pattern, text, re.MULTILINE)
            for match in matches:
                if isinstance(match, tuple):
                    code_snippets.extend([m.strip() for m in match if m.strip()])
                else:
                    code_snippets.append(match.strip())
        
        return list(set(code_snippets))
    
    def compare_image_content(self, ref_images_data, sub_images_data):
        """比对图片内容（通过OCR提取文本）"""
        ref_texts = []
        sub_texts = []
        
        for img_data in ref_images_data:
            if 'data' in img_data:
                text = self.extract_image_text(img_data['data'])
                if text:
                    ref_texts.append(text)
        
        for img_data in sub_images_data:
            if 'data' in img_data:
                text = self.extract_image_text(img_data['data'])
                if text:
                    sub_texts.append(text)
        
        ref_all_text = '\n'.join(ref_texts)
        sub_all_text = '\n'.join(sub_texts)
        
        ref_code = self.extract_code_from_text(ref_all_text)
        sub_code = self.extract_code_from_text(sub_all_text)
        
        common_code = set(ref_code) & set(sub_code)
        missing_code = set(ref_code) - set(sub_code)
        extra_code = set(sub_code) - set(ref_code)
        
        similarity = 0
        if len(ref_code) > 0:
            similarity = len(common_code) / len(ref_code)
        
        return {
            'ref_text_count': len(ref_texts),
            'sub_text_count': len(sub_texts),
            'ref_code_snippets': ref_code,
            'sub_code_snippets': sub_code,
            'common_code': list(common_code),
            'missing_code': list(missing_code),
            'extra_code': list(extra_code),
            'similarity': similarity
        }
