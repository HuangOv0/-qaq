import os
import json
from datetime import datetime
from config import Config

class ReportGenerator:
    def __init__(self):
        Config.init_dirs()
    
    def generate_json_report(self, result, output_path=None):
        """生成JSON格式的批改报告，返回字符串"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'original_filename': result.get('original_filename', 'unknown'),
            'reference_filename': result.get('reference_filename', 'unknown'),
            'total_score': result.get('total_score', 0),
            'is_wrong_project': result.get('is_wrong_project', False),
            'wrong_project_similarity': result.get('wrong_project_similarity', 0.0),
            'section_results': result.get('section_results', {}),
            'image_results': result.get('image_results', {}),
            'comments': result.get('comments', ''),
            'score_breakdown': {
                'structure': result.get('structure_score', 0),
                'content': result.get('content_score', 0),
                'images': result.get('image_score', 0),
                'analysis': result.get('analysis_score', 0)
            },
            'diff_summary': result.get('diff_summary', '')
        }
        
        json_str = json.dumps(report, ensure_ascii=False, indent=2)
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
        
        return json_str
    
    def generate_html_report(self, result, output_path=None):
        """生成HTML格式的批改报告"""
        html_template = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>实训报告批改结果 - {result.get('original_filename', 'unknown')}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .score-badge {{ font-size: 48px; font-weight: bold; }}
        .section {{ margin-top: 20px; padding: 15px; border: 1px solid #e0e0e0; border-radius: 8px; }}
        .section-title {{ color: #333; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .result-row {{ display: flex; justify-content: space-between; padding: 8px; border-bottom: 1px solid #f0f0f0; }}
        .result-row:last-child {{ border-bottom: none; }}
        .result-name {{ color: #666; }}
        .result-value {{ font-weight: bold; }}
        .high {{ color: #2ecc71; }}
        .medium {{ color: #f39c12; }}
        .low {{ color: #e74c3c; }}
        .comments {{ white-space: pre-wrap; line-height: 1.8; }}
        .diff-summary {{ background: #f8f9fa; padding: 15px; border-radius: 8px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>实训报告智能批改系统</h1>
        <p>批改时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <div class="section-title">基本信息</div>
        <div class="result-row"><span class="result-name">参考文件:</span><span class="result-value">{result.get('reference_filename', 'unknown')}</span></div>
        <div class="result-row"><span class="result-name">待批改文件:</span><span class="result-value">{result.get('original_filename', 'unknown')}</span></div>
    </div>
    
    <div class="section">
        <div class="section-title">总分</div>
        <div class="score-badge {'high' if result.get('total_score', 0) >= 80 else 'medium' if result.get('total_score', 0) >= 60 else 'low'}">
            {result.get('total_score', 0)}分
        </div>
        {result.get('is_wrong_project', False) and '<p style="color: #e74c3c; font-weight: bold;">⚠️ 检测到可能提交了错误的项目！</p>'}
    </div>
    
    <div class="section">
        <div class="section-title">章节评分详情</div>
        {self._generate_section_html(result.get('section_results', {}))}
    </div>
    
    <div class="section">
        <div class="section-title">图片分析</div>
        <div class="result-row"><span class="result-name">参考答案图片数:</span><span class="result-value">{result.get('image_results', {}).get('ref_count', 0)}</span></div>
        <div class="result-row"><span class="result-name">提交图片数:</span><span class="result-value">{result.get('image_results', {}).get('sub_count', 0)}</span></div>
        <div class="result-row"><span class="result-name">图片得分:</span><span class="result-value">{result.get('image_results', {}).get('score', 0)}分</span></div>
    </div>
    
    <div class="section">
        <div class="section-title">评语</div>
        <div class="comments">{result.get('comments', '')}</div>
    </div>
    
    <div class="section diff-summary">
        <div class="section-title">差异对比摘要</div>
        <p>{result.get('diff_summary', '无')}</p>
    </div>
</body>
</html>
        """
        
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(html_template)
        
        return html_template
    
    def _generate_section_html(self, section_results):
        """生成章节评分的HTML片段"""
        if not section_results or 'section_results' not in section_results:
            return '<p>无章节数据</p>'
        
        rows = []
        for section, result in section_results['section_results'].items():
            score = result.get('score', 0)
            status = 'high' if score >= 80 else 'medium' if score >= 60 else 'low'
            present = result.get('present', False)
            
            if not present:
                rows.append(f'<div class="result-row"><span class="result-name">{section}</span><span class="result-value low">缺失</span></div>')
            elif score is None:
                rows.append(f'<div class="result-row"><span class="result-name">{section}</span><span class="result-value medium">额外章节</span></div>')
            else:
                rows.append(f'<div class="result-row"><span class="result-name">{section}</span><span class="result-value {status}">{score}分</span></div>')
        
        return '\n'.join(rows)
    
    def process_batch(self, reference_path, submissions_dir, custom_rules=None):
        """批量处理文件夹中的报告"""
        from document_parser import DocumentParser
        from scoring_engine import ScoringEngine
        
        parser = DocumentParser()
        engine = ScoringEngine()
        
        ref_doc = parser.analyze_document(reference_path)
        
        results = []
        for filename in os.listdir(submissions_dir):
            if filename.startswith('.'):
                continue
            
            file_path = os.path.join(submissions_dir, filename)
            if not os.path.isfile(file_path):
                continue
            
            try:
                sub_doc = parser.analyze_document(file_path)
                
                is_wrong, similarity = engine.detect_wrong_project(ref_doc['text'], sub_doc['text'])
                
                if is_wrong:
                    result = {
                        'original_filename': filename,
                        'reference_filename': os.path.basename(reference_path),
                        'total_score': 0,
                        'is_wrong_project': True,
                        'wrong_project_similarity': similarity,
                        'comments': f"检测到提交了错误的项目，与参考答案相似度仅为{round(similarity*100)}%，建议重新检查提交的文件是否正确。"
                    }
                else:
                    section_results = engine.compare_sections(ref_doc['sections'], sub_doc['sections'])
                    image_results = engine.score_images(ref_doc['images'], sub_doc['images'], custom_rules)
                    final_score = engine.calculate_final_score(section_results, image_results['score'], custom_rules)
                    comments = engine.generate_comments(ref_doc, sub_doc, section_results, image_results, final_score)
                    
                    result = {
                        'original_filename': filename,
                        'reference_filename': os.path.basename(reference_path),
                        'total_score': final_score,
                        'is_wrong_project': False,
                        'section_results': section_results,
                        'image_results': image_results,
                        'comments': comments,
                        'diff_summary': self._generate_diff_summary(section_results, image_results)
                    }
                
                html_path = os.path.join(Config.OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_report.html")
                self.generate_html_report(result, html_path)
                
                json_path = os.path.join(Config.OUTPUT_DIR, f"{os.path.splitext(filename)[0]}_report.json")
                self.generate_json_report(result, json_path)
                
                results.append(result)
                
            except Exception as e:
                print(f"处理文件 {filename} 时出错: {str(e)}")
        
        return results
    
    def _generate_diff_summary(self, section_results, image_results):
        """生成差异对比摘要"""
        summary = []
        
        missing = [k for k, v in section_results['section_results'].items() if not v['present']]
        if missing:
            summary.append(f"缺少章节: {', '.join(missing)}")
        
        weak = [(k, round(v['similarity']*100)) for k, v in section_results['section_results'].items() if v['present'] and v['similarity'] < 0.7]
        if weak:
            summary.append(f"内容需完善的章节: {', '.join([f'{k}({s}%)' for k, s in weak])}")
        
        if image_results['difference'] != 0:
            summary.append(f"图片数量差异: 参考答案{image_results['ref_count']}张，提交{image_results['sub_count']}张")
        
        return '; '.join(summary) if summary else '报告内容与参考答案基本一致'
