#!/usr/bin/env python3
"""实训报告智能批改系统 - 命令行版本"""

import os
import sys
from document_parser import DocumentParser
from scoring_engine import ScoringEngine
from report_generator import ReportGenerator
from config import Config

def main():
    Config.init_dirs()
    
    print("=" * 60)
    print("    实训报告智能批改系统 - 命令行版本")
    print("=" * 60)
    
    # 获取文件路径
    ref_path = input("请输入参考答案文件路径 (.docx 或 .pdf): ").strip()
    sub_path = input("请输入待批改报告文件路径 (.docx 或 .pdf): ").strip()
    
    # 验证文件存在
    if not os.path.exists(ref_path):
        print(f"错误: 参考答案文件不存在 - {ref_path}")
        sys.exit(1)
    
    if not os.path.exists(sub_path):
        print(f"错误: 待批改文件不存在 - {sub_path}")
        sys.exit(1)
    
    # 选择评分规则
    print("\n请选择评分规则:")
    print("1. 与参考答案匹配")
    print("2. 指定图片数量")
    print("3. 行人检测")
    print("4. 图片代码比对")
    
    rule_choice = input("请输入规则编号 (1-4): ").strip()
    
    custom_rules = []
    if rule_choice == "1":
        custom_rules.append({'type': 'image_match_reference'})
    elif rule_choice == "2":
        count = int(input("请输入期望图片数量: "))
        custom_rules.append({'type': 'image_count', 'expected': count})
    elif rule_choice == "3":
        custom_rules.append({'type': 'rectangle_detection'})
        count = input("请输入期望图片数量 (回车跳过): ").strip()
        if count:
            custom_rules.append({'type': 'image_count', 'expected': int(count)})
    elif rule_choice == "4":
        custom_rules.append({'type': 'code_comparison'})
    else:
        print("使用默认规则: 与参考答案匹配")
        custom_rules.append({'type': 'image_match_reference'})
    
    print("\n正在批改中...")
    
    try:
        # 解析文档
        parser = DocumentParser()
        engine = ScoringEngine()
        generator = ReportGenerator()
        
        ref_doc = parser.analyze_document(ref_path)
        sub_doc = parser.analyze_document(sub_path)
        
        # 检测是否交错作业
        is_wrong, similarity = engine.detect_wrong_project(ref_doc['text'], sub_doc['text'])
        
        if is_wrong:
            print(f"\n⚠️ 检测到可能提交了错误的项目！")
            print(f"与参考答案相似度: {round(similarity*100)}%")
            print("建议检查提交的文件是否正确")
            
            result = {
                'original_filename': os.path.basename(sub_path),
                'reference_filename': os.path.basename(ref_path),
                'total_score': 0,
                'is_wrong_project': True,
                'wrong_project_similarity': similarity,
                'comments': f"检测到提交了错误的项目，与参考答案相似度仅为{round(similarity*100)}%，建议重新检查提交的文件是否正确。",
                'section_results': {'section_results': {}},
                'image_results': {},
                'diff_summary': '检测到项目不匹配'
            }
        else:
            # 评分
            section_results = engine.compare_sections(ref_doc['sections'], sub_doc['sections'])
            image_results = engine.score_images(ref_doc['images'], sub_doc['images'], 
                                               custom_rules if custom_rules else None,
                                               ref_doc.get('images_with_data'), 
                                               sub_doc.get('images_with_data'))
            final_score = engine.calculate_final_score(section_results, image_results['score'], 
                                                      {'weights': Config.DEFAULT_SCORING_RULES})
            comments = engine.generate_comments(ref_doc, sub_doc, section_results, image_results, final_score)
            
            result = {
                'original_filename': os.path.basename(sub_path),
                'reference_filename': os.path.basename(ref_path),
                'total_score': final_score,
                'is_wrong_project': False,
                'section_results': section_results,
                'image_results': image_results,
                'comments': comments,
                'diff_summary': engine.generate_diff_summary(ref_doc, sub_doc, section_results)
            }
        
        # 显示结果
        print("\n" + "=" * 60)
        print("                    批改结果")
        print("=" * 60)
        print(f"参考答案: {result['reference_filename']}")
        print(f"待批改报告: {result['original_filename']}")
        print(f"总分: {result['total_score']}分")
        print("=" * 60)
        
        if result['is_wrong_project']:
            print(f"\n⚠️ {result['comments']}")
        else:
            # 图片分析
            print("\n📊 图片分析:")
            print(f"  - 参考答案图片数: {result['image_results'].get('ref_count', 0)}张")
            print(f"  - 提交图片数: {result['image_results'].get('sub_count', 0)}张")
            print(f"  - 图片得分: {result['image_results'].get('score', 0)}分")
            
            if 'details' in result['image_results']:
                print("  - 评分详情:")
                for detail in result['image_results']['details']:
                    print(f"    * {detail}")
            
            # 章节分析
            print("\n📋 章节分析:")
            sections = result['section_results'].get('section_results', {})
            for section, info in sections.items():
                status = info.get('status', '')
                if status == 'missing':
                    print(f"  ✗ 缺失章节: {section}")
                elif status == 'partial':
                    print(f"  ⚠️ 部分缺失: {section}")
                else:
                    print(f"  ✓ 完整章节: {section}")
            
            # 评语
            print("\n💬 评语:")
            print(result['comments'])
        
        # 保存报告
        print("\n📥 保存批改报告...")
        html_report = generator.generate_html_report(result)
        json_report = generator.generate_json_report(result)
        
        output_dir = Config.OUTPUT_DIR
        base_name = os.path.splitext(os.path.basename(sub_path))[0]
        
        html_path = os.path.join(output_dir, f"{base_name}_批改报告.html")
        json_path = os.path.join(output_dir, f"{base_name}_批改报告.json")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            f.write(json_report)
        
        print(f"HTML报告已保存: {html_path}")
        print(f"JSON报告已保存: {json_path}")
        print("\n✅ 批改完成！")
        
    except Exception as e:
        print(f"\n❌ 处理过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
