import re, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CAT=ROOT/'outputs/catalog'
EXPECTED_COUNT=13

class CatalogTests(unittest.TestCase):
    def read_course(self, name):
        return (CAT/name).read_text(encoding='utf-8')

    def assert_terms(self, text, terms):
        for term in terms:
            self.assertIn(term, text)

    def test_latest_lecturer_intro_is_consistent(self):
        required=[
            '**冯博 Gatsby　企业AI落地专家**',
            '2024年至今，已为超过200家头部公司完成AI课程交付',
            '更多的实操、更多的作品、更强的产出',
            '让2%的中国人用好AI'
        ]
        for path in CAT.glob('*.md'):
            text=path.read_text(encoding='utf-8')
            intro=text.split('## 一、主讲人介绍',1)[1].split('## 二、本课程说明',1)[0]
            self.assert_terms(intro,required)
            for outdated in ['100+','96%','TOP 5%']:
                self.assertNotIn(outdated,intro,path.name)

    def test_catalog_names_and_complete_modules(self):
        files=list(CAT.glob('*.md'))
        self.assertEqual(len(files),EXPECTED_COUNT)
        for path in files:
            text=path.read_text(encoding='utf-8')
            first_line=text.splitlines()[0]
            if path.name=='博AI增效-OPC实战工作坊.md':
                self.assertEqual(first_line,'# 博AI增效-OPC实战工作坊')
            else:
                filename_match=re.fullmatch(r'博AI增效-([1-9]\d*)D-(.+)',path.stem)
                self.assertIsNotNone(filename_match,path.name)
                duration,course_name=filename_match.groups()
                self.assertEqual(first_line,f'# 【博AI增效-{duration}D】{course_name}')
            self.assertTrue(
                path.name=='博AI增效-OPC实战工作坊.md'
                or re.fullmatch(r'博AI增效-[12]D-.+_6X(畅销|数据|高管|极速|进阶|飞书|垂直)版.md',path.name)
            )
            for section in ['一、主讲人介绍','二、本课程说明','三、课程大纲','四、课程产出','五、课件展示','六、课程现场','七、课后准备','八、培训准备']:
                self.assertIn('## '+section,text)
            for forbidden in ['Reconcile','iSlide','智谱GLM']:
                self.assertNotIn(forbidden,text,path.name)
            modules=re.split(r'\*\*(?:模块\d+|加餐)：',text)[1:]
            self.assertTrue(modules,path.name)
            for block in modules:
                keys=['关键词：','讲解要点：','演示：','学员练习：','产出物：']
                positions=[block.index(k) for k in keys]
                self.assertEqual(positions,sorted(positions),path.name)

    def test_schedules_have_breaks_and_match_modules(self):
        for path in CAT.glob('*.md'):
            text=path.read_text(encoding='utf-8')
            rows=re.findall(r'^\| (\d{2}:\d{2})—(\d{2}:\d{2}) \|',text,re.M)
            slots=re.findall(r'\*\*(?:模块\d+|加餐)：[^\n]*｜(\d{2}:\d{2})—(\d{2}:\d{2})\*\*',text)
            self.assertEqual(rows,slots,path.name)
            number=lambda t:int(t[:2])*60+int(t[3:])
            day_breaks=0
            last=None
            for a,b in rows:
                a,b=number(a),number(b)
                self.assertGreater(b,a)
                if last is not None:
                    if a<last:
                        self.assertEqual(last,1050)
                        self.assertEqual(a,540)
                        day_breaks+=1
                    else:
                        self.assertIn(a-last,[15,120])
                last=b
            self.assertEqual(last,1050)
            days_match=re.match(r'^博AI增效-([12])D-',path.name)
            expected_days=int(days_match.group(1)) if days_match else 1
            self.assertEqual(day_breaks+1,expected_days,path.name)

    def test_matrix_links_match_catalog(self):
        matrix=ROOT/'outputs/博AI增效-课程销售矩阵.md'
        text=matrix.read_text(encoding='utf-8')
        links=re.findall(r'\]\((catalog/[^)]+\.md)\)',text)
        self.assertEqual(len(links),EXPECTED_COUNT)
        self.assertEqual(len(links),len(set(links)))
        linked_files={Path(link).name for link in links}
        catalog_files={path.name for path in CAT.glob('*.md')}
        self.assertEqual(linked_files,catalog_files)
        self.assert_terms(text,['职场办公','管理者','行业专项','适合对象','主要解决的问题','主要软件'])
        for forbidden in ['iSlide','智谱GLM']:
            self.assertNotIn(forbidden,text)

    def test_customer_service_qa_has_safe_sales_boundaries(self):
        text=(ROOT/'outputs/博AI增效-课程销售客服Q&A.md').read_text(encoding='utf-8')
        self.assert_terms(text,[
            'AI客服基础Q&A','先讲客户问题和课堂成果','一次优先推荐一门课程',
            '具体价格、档期或合同范围','建议转人工的情况',
            '2024年至今，已为超过200家头部公司完成AI课程交付'
        ])
        for forbidden in ['99元/人','标准价：','保证提升10倍','保证ROI']:
            self.assertNotIn(forbidden,text)

    def test_high_manager_course_capabilities(self):
        text=self.read_course('博AI增效-1D-面向管理者的AI增长进阶课_6X高管版.md')
        self.assert_terms(text,[
            '四维模型选型表','同一项业务任务','专家团与自动化链路',
            '经营分析会管理质询单','可操作HTML原型',
            '独立工作目录与文件副本','30天试点'
        ])
        headings=['AI×技术前沿','AI×经营洞察','AI×业务原型','AI×组织行动']
        positions=[text.index(heading) for heading in headings]
        self.assertEqual(positions,sorted(positions))

    def test_marketing_course_capabilities(self):
        text=self.read_course('博AI增效-1D-10倍AI营销引擎_6X极速版.md')
        self.assert_terms(text,[
            '参考图反推','多模态参考','即梦','Seedream','Seedance',
            '智能改图','首尾帧','运镜','备用片段'
        ])

    def test_feishu_course_capabilities(self):
        text=self.read_course('博AI增效-1D-飞书AI实战课_6X飞书版.md')
        self.assert_terms(text,[
            '知识问答','智能纪要','文档AI','多维表格','AI字段',
            'Aily','妙搭','人工终稿对照','招聘或项目场景复测'
        ])
        self.assertNotIn('Aliy',text)
        self.assertNotIn('秒搭',text)

    def test_power_grid_course_capabilities(self):
        text=self.read_course('博AI增效-1D-电网AI办公增效实战_6X垂直版.md')
        self.assert_terms(text,[
            'WorkBuddy','公文','多表合并','AGENTS.md（岗位个性化规则）',
            '不连接生产控制系统'
        ])
        self.assertLess(text.index('AI×公文与汇报'),text.index('AI×数据整理'))

    def test_communications_course_capabilities(self):
        government=self.read_course('博AI增效-1D-通讯政企前端AI实战课_6X垂直版.md')
        self.assert_terms(government,[
            'WorkBuddy','客户画像','一页方案','岗位Skill',
            'CRM写入与定时自动化不作为本课必交项'
        ])

        grid=self.read_course('博AI增效-2D-通讯网格营销AI实战工作坊_6X垂直版.md')
        self.assert_terms(grid,[
            'WorkBuddy','网格营销素材包','即梦和剪映仅用于视觉与视频制作',
            '日报或周报','岗位AI工作台v1.0'
        ])

        token=self.read_course('博AI增效-2D-通讯Token运营AI实战工作坊_6X垂直版.md')
        self.assert_terms(token,[
            'WorkBuddy','Token运营','SKILL.md','受控自动化',
            '不承诺现场必然接通'
        ])
