import streamlit as st
import os
import tempfile
from document_parser import DocumentParser
from scoring_engine import ScoringEngine
from report_generator import ReportGenerator
from config import Config

Config.init_dirs()

def main():
    st.set_page_config(
        page_title="实训报告智能批改系统",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("📝 实训报告智能批改系统")
    st.markdown("基于Trae AI编程工具开发，支持docx和pdf格式的实训报告自动批改")
    
    # 上传文件
    col1, col2 = st.columns(2)
    
    with col1:
        reference_file = st.file_uploader("📁 上传参考答案", type=['docx', 'pdf'])
    
    with col2:
        submission_file = st.file_uploader("📁 上传待批改报告", type=['docx', 'pdf'])
    
    # 评分规则选择
    st.markdown("---")
    st.subheader("⚙️ 评分规则设置")
    
    rule_type = st.selectbox(
        "选择评分规则",
        ["与参考答案匹配", "指定图片数量", "行人检测", "图片代码比对"],
        index=0
    )
    
    custom_rules = []
    expected_count = 0
    
    if rule_type == "指定图片数量":
        expected_count = st.number_input("期望图片数量", min_value=1, max_value=100, value=5)
        custom_rules.append({'type': 'image_count', 'expected': expected_count})
    
    elif rule_type == "与参考答案匹配":
        custom_rules.append({'type': 'image_match_reference'})
    
    elif rule_type == "行人检测":
        expected_count = st.number_input("期望图片数量（可选）", min_value=0, max_value=100, value=0)
        custom_rules.append({'type': 'rectangle_detection'})
        if expected_count > 0:
            custom_rules.append({'type': 'image_count', 'expected': expected_count})
    
    elif rule_type == "图片代码比对":
        custom_rules.append({'type': 'code_comparison'})
        st.info("⚠️ 此规则会从参考答案图片中提取代码，与学生报告图片中的代码进行比对")
        
        # 显示 OCR 状态
        try:
            import pytesseract
            st.success("✅ pytesseract 已安装，图片 OCR 功能可用")
        except ImportError:
            st.warning("⚠️ pytesseract 未安装，图片 OCR 功能不可用")
    
    # 显示当前规则详情
    if custom_rules:
        st.markdown("**当前评分规则：**")
        for rule in custom_rules:
            if rule['type'] == 'image_match_reference':
                st.markdown("- 📊 与参考答案匹配（自动比对图片数量和内容）")
            elif rule['type'] == 'image_count':
                st.markdown(f"- 🖼️ 指定图片数量：{rule['expected']}张")
            elif rule['type'] == 'rectangle_detection':
                st.markdown("- ⬜ 行人检测（验证矩形框）")
            elif rule['type'] == 'code_comparison':
                st.markdown("- 💻 图片代码比对（OCR提取代码）")
    
    # 开始批改按钮
    if st.button("🚀 开始批改", disabled=not (reference_file and submission_file)):
        with st.spinner("正在批改中..."):
            try:
                # 保存临时文件
                ref_ext = os.path.splitext(reference_file.name)[1]
                sub_ext = os.path.splitext(submission_file.name)[1]
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ref_ext) as ref_temp:
                    ref_temp.write(reference_file.getbuffer())
                    ref_path = ref_temp.name
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=sub_ext) as sub_temp:
                    sub_temp.write(submission_file.getbuffer())
                    sub_path = sub_temp.name
                
                # 解析文档
                parser = DocumentParser()
                engine = ScoringEngine()
                generator = ReportGenerator()
                
                ref_doc = parser.analyze_document(ref_path)
                sub_doc = parser.analyze_document(sub_path)
                
                # 检测是否交错作业
                is_wrong, similarity = engine.detect_wrong_project(ref_doc['text'], sub_doc['text'])
                
                if is_wrong:
                    st.error(f"⚠️ 检测到可能提交了错误的项目！")
                    st.info(f"与参考答案相似度: {round(similarity*100)}%")
                    st.warning("建议检查提交的文件是否正确")
                    
                    result = {
                        'original_filename': submission_file.name,
                        'reference_filename': reference_file.name,
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
                        'original_filename': submission_file.name,
                        'reference_filename': reference_file.name,
                        'total_score': final_score,
                        'is_wrong_project': False,
                        'section_results': section_results,
                        'image_results': image_results,
                        'comments': comments,
                        'diff_summary': engine.generate_diff_summary(ref_doc, sub_doc, section_results)
                    }
                
                # 显示结果
                st.markdown("---")
                st.subheader("📊 批改结果")
                
                score_color = "green" if result['total_score'] >= 80 else "orange" if result['total_score'] >= 60 else "red"
                st.markdown(f"<h2 style='color:{score_color}'>总分: {result['total_score']}分</h2>", unsafe_allow_html=True)
                
                # 图片分析
                if 'image_results' in result and result['image_results']:
                    st.markdown("### 🖼️ 图片分析")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.markdown(f"- 参考答案图片数: {result['image_results'].get('ref_count', 0)}张")
                        st.markdown(f"- 提交图片数: {result['image_results'].get('sub_count', 0)}张")
                        st.markdown(f"- 图片得分: {result['image_results'].get('score', 0)}分")
                    with col_b:
                        if 'details' in result['image_results']:
                            st.markdown("**评分详情:**")
                            for detail in result['image_results']['details']:
                                st.markdown(f"  - {detail}")
                    
                    # 显示图片代码比对详细信息
                    if 'code_compare' in result['image_results']:
                        st.markdown("#### 💻 图片代码比对结果")
                        code_info = result['image_results']['code_compare']
                        col_c, col_d = st.columns(2)
                        with col_c:
                            st.markdown(f"- 参考答案图片提取文本: {code_info.get('ref_text_count', 0)}张")
                            st.markdown(f"- 提交图片提取文本: {code_info.get('sub_text_count', 0)}张")
                            st.markdown(f"- 代码相似度: {round(code_info.get('similarity', 0)*100)}%")
                        with col_d:
                            if code_info.get('common_code'):
                                st.markdown(f"**✅ 匹配的代码 ({len(code_info['common_code'])}个):**")
                                for code in code_info['common_code'][:5]:
                                    st.code(code[:100] + "..." if len(code) > 100 else code)
                            if code_info.get('missing_code'):
                                st.markdown(f"**⚠️ 缺失的代码 ({len(code_info['missing_code'])}个):**")
                                for code in code_info['missing_code'][:3]:
                                    st.code(code[:100] + "..." if len(code) > 100 else code)
                
                # 评语
                st.markdown("### 💬 评语")
                st.write(result['comments'])
                
                # 下载报告
                st.markdown("### 📥 下载报告")
                html_report = generator.generate_html_report(result)
                json_report = generator.generate_json_report(result)
                
                st.download_button(
                    label="下载 HTML 报告",
                    data=html_report,
                    file_name=f"{os.path.splitext(submission_file.name)[0]}_批改报告.html",
                    mime="text/html"
                )
                
                st.download_button(
                    label="下载 JSON 报告",
                    data=json_report,
                    file_name=f"{os.path.splitext(submission_file.name)[0]}_批改报告.json",
                    mime="application/json"
                )
                
                # 清理临时文件
                os.unlink(ref_path)
                os.unlink(sub_path)
                
            except Exception as e:
                st.error(f"处理过程中发生错误: {e}")
                import traceback
                st.exception(traceback.format_exc())

if __name__ == "__main__":
    main()
