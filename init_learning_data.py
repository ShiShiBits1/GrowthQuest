# 初始化学习资源数据的脚本
import sys
sys.path.append('d:/Users/Administrator/GitHub/GrowthQuest')

from app import create_app, db
from app.models import LearningCategory, LearningResource

app = create_app()

with app.app_context():
    print("开始初始化学习资源数据...")
    
    # 检查是否已有数据
    if LearningCategory.query.count() > 0:
        print("学习分类数据已存在，跳过初始化")
    else:
        # 创建学习分类
        categories = [
            LearningCategory(
                name="科学探索",
                description="有趣的科学实验和自然现象解释，激发孩子的科学好奇心",
                icon="🔬"
            ),
            LearningCategory(
                name="语文阅读",
                description="经典童话故事和优美散文，培养孩子的阅读兴趣和语言能力",
                icon="📖"
            ),
            LearningCategory(
                name="数学思维",
                description="通过游戏和动画学习数学知识，让数学变得简单有趣",
                icon="🔢"
            ),
            LearningCategory(
                name="艺术创意",
                description="绘画、手工和音乐欣赏，培养孩子的创造力和审美能力",
                icon="🎨"
            )
        ]
        
        for category in categories:
            db.session.add(category)
        db.session.commit()
        print(f"成功创建{len(categories)}个学习分类")
    
    # 创建学习资源
    if LearningResource.query.count() > 0:
        print("学习资源数据已存在，跳过初始化")
    else:
        categories = LearningCategory.query.all()
        
        # 科学探索分类的资源
        science_resources = [
            LearningResource(
                title="为什么天空是蓝色的？",
                description="通过生动的动画讲解光的散射原理，让孩子了解天空颜色的科学原因。适合6-12岁儿童观看。",
                resource_type="视频",
                content_url="#",  # 这里应该是实际的视频URL
                thumbnail_url="#",  # 这里应该是实际的缩略图URL
                duration=300,  # 5分钟
                difficulty_level="初级",
                category_id=categories[0].id,
                is_active=True
            ),
            LearningResource(
                title="简单的家庭科学小实验",
                description="介绍5个简单安全的家庭科学实验，只需要日常材料就能完成，培养孩子的动手能力和科学思维。",
                resource_type="文章",
                content_url="#",
                thumbnail_url="#",
                difficulty_level="初级",
                category_id=categories[0].id,
                is_active=True
            )
        ]
        
        # 语文阅读分类的资源
        chinese_resources = [
            LearningResource(
                title="小蝌蚪找妈妈",
                description="经典童话故事，通过讲述小蝌蚪寻找妈妈的旅程，介绍了青蛙的生长过程。",
                resource_type="文章",
                content_url="#",
                thumbnail_url="#",
                difficulty_level="初级",
                category_id=categories[1].id,
                is_active=True
            ),
            LearningResource(
                title="唐诗三百首精选",
                description="精选30首适合儿童朗读的唐诗，配有拼音和简单解释，培养孩子的语言美感。",
                resource_type="文章",
                content_url="#",
                thumbnail_url="#",
                difficulty_level="中级",
                category_id=categories[1].id,
                is_active=True
            )
        ]
        
        # 数学思维分类的资源
        math_resources = [
            LearningResource(
                title="认识数字1-100",
                description="通过有趣的动画和游戏，帮助孩子认识和记忆1-100的数字顺序。",
                resource_type="视频",
                content_url="#",
                thumbnail_url="#",
                duration=480,  # 8分钟
                difficulty_level="初级",
                category_id=categories[2].id,
                is_active=True
            ),
            LearningResource(
                title="加减法的趣味学习",
                description="通过生活中的例子和游戏，让孩子轻松掌握10以内的加减法。",
                resource_type="视频",
                content_url="#",
                thumbnail_url="#",
                duration=420,  # 7分钟
                difficulty_level="初级",
                category_id=categories[2].id,
                is_active=True
            )
        ]
        
        # 艺术创意分类的资源
        art_resources = [
            LearningResource(
                title="手指画基础教程",
                description="简单易学的手指画技巧，只需要颜料和纸就能创作美丽的图画。",
                resource_type="视频",
                content_url="#",
                thumbnail_url="#",
                duration=540,  # 9分钟
                difficulty_level="初级",
                category_id=categories[3].id,
                is_active=True
            ),
            LearningResource(
                title="儿童手工制作大全",
                description="收集了20种适合儿童的手工制作方法，培养孩子的动手能力和创造力。",
                resource_type="文章",
                content_url="#",
                thumbnail_url="#",
                difficulty_level="初级",
                category_id=categories[3].id,
                is_active=True
            )
        ]
        
        all_resources = science_resources + chinese_resources + math_resources + art_resources
        
        for resource in all_resources:
            db.session.add(resource)
        db.session.commit()
        print(f"成功创建{len(all_resources)}个学习资源")
    
    print("学习资源数据初始化完成！")