import os

class Config:
    # 项目根目录
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 数据目录
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    REFERENCE_DIR = os.path.join(DATA_DIR, 'references')
    SUBMISSIONS_DIR = os.path.join(DATA_DIR, 'submissions')
    OUTPUT_DIR = os.path.join(DATA_DIR, 'output')
    
    # 图片处理配置
    MIN_IMAGE_WIDTH = 100
    MIN_IMAGE_HEIGHT = 100
    MAX_IMAGE_WIDTH = 5000
    MAX_IMAGE_HEIGHT = 5000
    
    # 评分配置
    DEFAULT_SCORE_THRESHOLD = 0.8
    IMAGE_COUNT_TOLERANCE = 1
    
    # 章节关键词
    SECTION_KEYWORDS = {
        '实训目的': ['实训目的', '实验目的', '学习目标', '实验目标'],
        '实训内容': ['实训内容', '实验内容', '项目内容', '任务描述'],
        '实训步骤': ['实训步骤', '实验步骤', '操作步骤', '实现过程'],
        '实验结果': ['实验结果', '实训结果', '结果分析', '实验数据'],
        '问题反思': ['问题反思', '遇到的问题', '问题分析', '故障排除'],
        '心得体会': ['心得体会', '总结', '收获', '感悟'],
        '参考文献': ['参考文献', '参考资料', '引用']
    }
    
    # 评分规则模板
    DEFAULT_SCORING_RULES = {
        'structure_weight': 0.2,
        'content_weight': 0.4,
        'images_weight': 0.2,
        'analysis_weight': 0.2
    }
    
    @staticmethod
    def init_dirs():
        os.makedirs(Config.REFERENCE_DIR, exist_ok=True)
        os.makedirs(Config.SUBMISSIONS_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
