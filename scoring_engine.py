import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from config import Config

class ScoringEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english', max_features=5000)
    
    def calculate_text_similarity(self, text1, text2):
        """计算两段文本的相似度"""
        if not text1 or not text2:
            return 0.0
        
        try:
            tfidf_matrix = self.vectorizer.fit_transform([text1, text2])
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            return float(similarity)
        except:
            return 0.0
    
    def compare_sections(self, ref_sections, sub_sections):
        """比对章节内容"""
        results = {}
        total_score = 0.0
        section_count = 0
        
        for ref_section, ref_content in ref_sections.items():
            ref_text = '\n'.join(ref_content)
            
            if ref_section in sub_sections:
                sub_text = '\n'.join(sub_sections[ref_section])
                similarity = self.calculate_text_similarity(ref_text, sub_text)
                results[ref_section] = {
                    'present': True,
                    'similarity': similarity,
                    'score': min(100, similarity * 100),
                    'ref_length': len(ref_text),
                    'sub_length': len(sub_text)
                }
                total_score += similarity
                section_count += 1
            else:
                results[ref_section] = {
                    'present': False,
                    'similarity': 0.0,
                    'score': 0,
                    'ref_length': len(ref_text),
                    'sub_length': 0
                }
        
        for sub_section in sub_sections:
            if sub_section not in ref_sections:
                results[sub_section] = {
                    'present': True,
                    'similarity': None,
                    'score': None,
                    'ref_length': 0,
                    'sub_length': len('\n'.join(sub_sections[sub_section])),
                    'note': '参考答案中不存在此章节'
                }
        
        avg_score = total_score / section_count if section_count > 0 else 0.0
        return {
            'section_results': results,
            'average_similarity': avg_score,
            'matched_sections': section_count,
            'total_sections': len(ref_sections)
        }
    
    def detect_wrong_project(self, ref_text, sub_text, threshold=0.25):
        """检测是否提交了错误的项目"""
        similarity = self.calculate_text_similarity(ref_text, sub_text)
        return similarity < threshold, similarity
    
    def score_images(self, ref_images, sub_images, custom_rules=None, ref_images_data=None, sub_images_data=None):
        """对图片部分进行评分"""
        processor = __import__('image_processor').ImageProcessor()
        img_processor = processor.ImageProcessor()
        
        ref_analysis = img_processor.analyze_images(ref_images)
        sub_analysis = img_processor.analyze_images(sub_images)
        
        count_compare = img_processor.compare_image_counts(
            ref_analysis['total_count'],
            sub_analysis['total_count']
        )
        
        if custom_rules:
            return self._apply_custom_rules(ref_images, sub_images, rules=custom_rules, 
                                           ref_images_data=ref_images_data, 
                                           sub_images_data=sub_images_data)
        
        base_score = 100 if count_compare['is_acceptable'] else 0
        
        if count_compare['difference'] == 0:
            image_score = 100
        elif count_compare['difference'] <= 2:
            image_score = max(70, 100 - count_compare['difference'] * 15)
        else:
            image_score = max(0, 100 - count_compare['difference'] * 20)
        
        valid_ratio = sub_analysis['valid_count'] / max(sub_analysis['total_count'], 1)
        image_score = int(image_score * valid_ratio)
        
        return {
            'score': image_score,
            'ref_count': ref_analysis['total_count'],
            'sub_count': sub_analysis['total_count'],
            'ref_valid_count': ref_analysis['valid_count'],
            'sub_valid_count': sub_analysis['valid_count'],
            'difference': count_compare['difference'],
            'is_acceptable': count_compare['is_acceptable']
        }
    
    def _apply_custom_rules(self, ref_images, sub_images, rules, ref_images_data=None, sub_images_data=None):
        """应用自定义评分规则"""
        score = 0
        total_rules = len(rules)
        results = []
        
        processor = __import__('image_processor').ImageProcessor()
        img_processor = processor.ImageProcessor()
        
        for rule in rules:
            rule_type = rule.get('type')
            expected = rule.get('expected', 0)
            weight = rule.get('weight', 1.0)
            
            if rule_type == 'rectangle_detection':
                if sub_images:
                    score += 100 * weight / total_rules
                    results.append(f"✓ 检测到图片（行人检测规则）")
                else:
                    results.append(f"✗ 未检测到图片")
            
            elif rule_type == 'image_count':
                actual = len(sub_images)
                if actual == expected:
                    score += 100 * weight / total_rules
                    results.append(f"✓ 图片数量正确（{actual}张）")
                elif abs(actual - expected) <= 1:
                    score += 80 * weight / total_rules
                    results.append(f"⚠️ 图片数量略有差异（期望{expected}张，实际{actual}张）")
                else:
                    results.append(f"✗ 图片数量不符（期望{expected}张，实际{actual}张）")
            
            elif rule_type == 'image_match_reference':
                ref_count = len(ref_images)
                sub_count = len(sub_images)
                code_compare_result = None
                
                if sub_count >= ref_count - 1 and sub_count <= ref_count + 1:
                    content_similarity = 1.0
                    if ref_images_data and sub_images_data and len(ref_images_data) > 0 and len(sub_images_data) > 0:
                        content_compare = img_processor.compare_image_content(ref_images_data, sub_images_data)
                        content_similarity = content_compare['similarity']
                        code_compare_result = content_compare
                        
                        if content_compare['missing_code']:
                            results.append(f"⚠️ 图片中缺少代码片段: {', '.join(content_compare['missing_code'])[:50]}...")
                        if content_compare['common_code']:
                            results.append(f"✓ 图片中匹配的代码片段: {', '.join(content_compare['common_code'])[:50]}...")
                    
                    score += 100 * weight / total_rules * content_similarity
                    results.append(f"✓ 图片数量与参考基本一致（参考{ref_count}张，提交{sub_count}张），内容相似度: {round(content_similarity*100)}%")
                else:
                    results.append(f"✗ 图片数量差异较大（参考{ref_count}张，提交{sub_count}张）")
            
            elif rule_type == 'code_comparison':
                code_compare_result = None
                if ref_images_data and sub_images_data:
                    content_compare = img_processor.compare_image_content(ref_images_data, sub_images_data)
                    content_similarity = content_compare['similarity']
                    code_compare_result = content_compare
                    
                    score += 100 * weight / total_rules * content_similarity
                    
                    if content_compare['missing_code']:
                        results.append(f"⚠️ 图片中缺少代码: {', '.join(content_compare['missing_code'])[:80]}...")
                    if content_compare['common_code']:
                        results.append(f"✓ 图片中匹配的代码: {', '.join(content_compare['common_code'])[:80]}...")
                    results.append(f"图片代码相似度: {round(content_similarity*100)}%")
                else:
                    results.append(f"⚠️ 无法进行图片内容比对（缺少图片数据）")
                    score += 50 * weight / total_rules
        
        return_result = {
            'score': int(score), 
            'ref_count': len(ref_images), 
            'sub_count': len(sub_images),
            'details': results
        }
        
        # 添加代码比对详细信息
        if code_compare_result:
            return_result['code_compare'] = code_compare_result
        
        return return_result
    
    def calculate_final_score(self, section_scores, image_score, rules=None):
        """计算最终总分"""
        weights = rules.get('weights', Config.DEFAULT_SCORING_RULES) if rules else Config.DEFAULT_SCORING_RULES
        
        structure_score = section_scores['average_similarity'] * 100 * weights['structure_weight']
        content_score = section_scores['average_similarity'] * 100 * weights['content_weight']
        image_portion = image_score * weights['images_weight']
        analysis_score = section_scores['average_similarity'] * 100 * weights['analysis_weight']
        
        total = structure_score + content_score + image_portion + analysis_score
        return min(100, round(total))
    
    def generate_comments(self, ref_doc, sub_doc, section_results, image_results, final_score):
        """生成个性化评语"""
        comments = []
        
        comments.append(f"## 综合评分: {final_score}分\n")
        
        comments.append("### 一、优点")
        matched_sections = [k for k, v in section_results['section_results'].items() if v['present'] and v['similarity'] >= 0.7]
        if matched_sections:
            comments.append(f"- 以下章节内容与参考答案高度一致：{', '.join(matched_sections)}")
        if image_results['is_acceptable']:
            comments.append(f"- 图片数量符合要求（参考答案{image_results['ref_count']}张，提交{image_results['sub_count']}张）")
        
        comments.append("\n### 二、需要改进的地方")
        missing_sections = [k for k, v in section_results['section_results'].items() if not v['present']]
        if missing_sections:
            comments.append(f"- 缺少以下必要章节：{', '.join(missing_sections)}")
        
        weak_sections = [(k, v) for k, v in section_results['section_results'].items() if v['present'] and v['similarity'] < 0.7 and v['similarity'] > 0]
        if weak_sections:
            comments.append("- 以下章节内容需要进一步完善：")
            for section, result in weak_sections:
                comments.append(f"  - {section}：相似度{round(result['similarity']*100)}%，建议参考参考答案补充关键内容")
        
        if image_results['difference'] != 0:
            comments.append(f"- 图片数量与参考答案不一致，建议核对并补充必要的截图")
        
        comments.append("\n### 三、改进建议")
        comments.append("1. 仔细阅读参考答案，对比检查每个章节的完整性")
        comments.append("2. 确保所有必要的实验截图都已包含")
        comments.append("3. 对于相似度较低的章节，建议重新撰写以更好地体现对知识点的理解")
        comments.append("4. 注意图片质量，确保尺寸合理、内容清晰")
        
        return '\n'.join(comments)
