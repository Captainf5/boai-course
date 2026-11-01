"""
课纲排版 - Markdown 转 Word（带图片版）
自动在指定位置插入 images/ 文件夹中的图片

图片插入位置：
1. "主讲人介绍" 章节末尾 → 讲师照片
2. "课件展示" 或 "五、" 章节 → 课件截图（如有）
3. "课程现场" 或 "六、" 章节 → 现场照片（如有）
4. "现场准备" 或 "课前准备" 章节末尾 → 电脑配置

使用方法：
    python 课纲排版toWord带图版.py --input "课纲.md"
    # 生成：课纲_带图.docx
"""

import argparse
import os
import re
import unicodedata
from pathlib import Path
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# 路径配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, '..', 'images')

# 图片文件名配置
IMAGE_FILES = {
    'lecturer': ['讲师照片1.jpg', '讲师照片1.png', '讲师照片1.jpeg'],
    'slides': ['课件展示1.jpg', '课件展示1.png', '课件展示1.jpeg'],
    'scene1': ['现场照片1.jpg', '现场照片1.png', '现场照片1.jpeg'],
    'scene2': ['现场照片2.jpg', '现场照片2.png', '现场照片2.jpeg'],
    'scene3': ['现场照片3.jpg', '现场照片3.png', '现场照片3.jpeg'],
    'scene4': ['现场照片4.jpg', '现场照片4.png', '现场照片4.jpeg'],
    'computer': ['讲师电脑.jpg', '讲师电脑.png', '讲师电脑.jpeg'],
}

# 图片说明文字配置
IMAGE_CAPTIONS = {
    'lecturer': '（讲师近照）',
    'slides': '（课件展示截图）',
    'scenes': '（培训现场照片）',
    'computer': '（老师使用自己的华为电脑演示课程，电脑接口如上图所示）',
}

# 颜色配置
ORANGE = RGBColor(0xFF, 0x6B, 0x35)
LIGHT_ORANGE_HEX = "FFF5EE"
BLACK = RGBColor(0x1A, 0x1A, 0x1A)
GRAY = RGBColor(0x66, 0x66, 0x66)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TITLE_COMPACT_WIDTH = 45

def find_image(key):
    """查找图片文件"""
    for filename in IMAGE_FILES.get(key, []):
        path = os.path.join(IMAGES_DIR, filename)
        if os.path.exists(path):
            return path
    return None

def set_font(run, name='微软雅黑', size=11, bold=False, color=BLACK):
    """设置字体样式"""
    run.font.name = name
    run._element.rPr.rFonts.set(qn('w:eastAsia'), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = color

def display_width(text):
    """Estimate mixed Chinese/Latin title width in terminal-style columns."""
    return sum(2 if unicodedata.east_asian_width(char) in {'W', 'F', 'A'} else 1 for char in text)

def title_font_size(text):
    """Keep the standard 18pt title, reducing only titles that exceed one line."""
    return 16 if display_width(text) > TITLE_COMPACT_WIDTH else 18

def set_outline_level(para, level):
    """Add Word navigation/TOC semantics without changing visual styling."""
    outline = para._p.get_or_add_pPr().get_or_add_outlineLvl()
    outline.set(qn('w:val'), str(level))

def drop_unused_image_relationships(doc):
    """Remove template image parts that are no longer referenced by the body."""
    image_reference_attrs = {qn('r:embed'), qn('r:link'), qn('r:id')}
    used_rids = {
        value
        for element in doc._element.iter()
        for attr, value in element.attrib.items()
        if attr in image_reference_attrs
    }
    for rid, rel in list(doc.part.rels.items()):
        if rel.reltype == RT.IMAGE and rid not in used_rids:
            doc.part.drop_rel(rid)

def add_caption(doc, text):
    """添加居中小字图片说明"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    para.paragraph_format.space_before = Pt(2)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.keep_with_next = False
    run = para.add_run(text)
    set_font(run, size=9, color=GRAY)

def add_centered_image(doc, image_path, width_cm, caption=None):
    """添加居中图片，可选说明文字"""
    if not image_path or not os.path.exists(image_path):
        return False
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    run.add_picture(image_path, width=Cm(width_cm))
    if caption:
        add_caption(doc, caption)
    else:
        doc.add_paragraph()  # 间距
    return True

def add_image_row(doc, image_paths, width_cm_each, caption=None):
    """添加一行并排图片，可选说明文字"""
    valid_paths = [p for p in image_paths if p and os.path.exists(p)]
    if not valid_paths:
        return False
    
    table = doc.add_table(rows=1, cols=len(valid_paths))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    
    for cell, img_path in zip(table.row_cells(0), valid_paths):
        para = cell.paragraphs[0]
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = para.add_run()
        run.add_picture(img_path, width=Cm(width_cm_each))
    
    if caption:
        add_caption(doc, caption)
    else:
        doc.add_paragraph()
    return True

def parse_markdown(md_content):
    """解析 Markdown 内容"""
    lines = md_content.split('\n')
    elements = []
    current_table = []
    in_table = False
    
    for line in lines:
        line = line.rstrip('\r')
        
        # 表格处理
        if line.startswith('|'):
            in_table = True
            current_table.append(line)
            continue
        elif in_table:
            elements.append(('table', current_table))
            current_table = []
            in_table = False
        
        # 空行
        if not line.strip():
            continue
        
        # 分隔线
        if line.strip() == '---':
            continue
        
        # 标题
        if line.startswith('# '):
            elements.append(('h1', line[2:].strip()))
        elif line.startswith('## ——'):
            elements.append(('subtitle', line[3:].strip()))
        elif line.startswith('## '):
            elements.append(('h2', line[3:].strip()))
        elif line.startswith('### '):
            elements.append(('h3', line[4:].strip()))
        elif line.startswith('##### '):
            elements.append(('h5', line[6:].strip()))
        elif line.startswith('#### '):
            elements.append(('h4', line[5:].strip()))
        # 引用块
        elif line.startswith('> '):
            elements.append(('quote', line[2:].strip()))
        # 列表
        elif line.startswith('- '):
            elements.append(('bullet', line[2:].strip()))
        elif re.match(r'^\d+\. ', line):
            elements.append(('numbered', re.sub(r'^\d+\. ', '', line).strip()))
        # 普通段落
        else:
            elements.append(('paragraph', line.strip()))
    
    # 处理最后的表格
    if current_table:
        elements.append(('table', current_table))
    
    return elements

def add_h1(doc, text):
    """橙色横幅标题"""
    para = doc.add_paragraph()
    set_outline_level(para, 0)
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FF6B35"/>')
    para._p.get_or_add_pPr().append(shading)
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(12)
    para.paragraph_format.keep_with_next = True
    run = para.add_run(text)
    set_font(run, size=title_font_size(text), bold=True, color=WHITE)

def add_subtitle(doc, text):
    """灰色右对齐副标题"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = para.add_run(text)
    set_font(run, size=11, color=GRAY)

def add_h2(doc, text):
    """橙色加粗二级标题"""
    para = doc.add_paragraph()
    set_outline_level(para, 1)
    para.paragraph_format.space_before = Pt(18)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.keep_with_next = True
    run = para.add_run(text)
    set_font(run, size=16, bold=True, color=ORANGE)

def add_h3(doc, text):
    """左侧橙色竖线三级标题"""
    para = doc.add_paragraph()
    set_outline_level(para, 2)
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.keep_with_next = True
    if text.startswith(('第一天', 'Day 1', '第二天', 'Day 2', '第三天', 'Day 3')):
        para.paragraph_format.space_before = Pt(18)
        para._p.get_or_add_pPr().append(parse_xml(f'<w:shd {nsdecls("w")} w:fill="FFF1EB"/>'))
    pPr = para._p.get_or_add_pPr()
    pBdr = parse_xml(
        f'<w:pBdr {nsdecls("w")}>'
        f'<w:left w:val="single" w:sz="24" w:space="4" w:color="FF6B35"/>'
        f'</w:pBdr>'
    )
    pPr.append(pBdr)
    run = para.add_run(text)
    set_font(run, size=14, bold=True, color=BLACK)

def add_h4(doc, text):
    """黑色加粗四级标题"""
    para = doc.add_paragraph()
    set_outline_level(para, 3)
    para.paragraph_format.space_before = Pt(18)
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.keep_with_next = True
    run = para.add_run(text)
    set_font(run, size=12, bold=True, color=BLACK)

def add_h5(doc, text):
    """黑色加粗五级标题（模块标题）"""
    para = doc.add_paragraph()
    set_outline_level(para, 4)
    para.paragraph_format.space_before = Pt(18)
    para.paragraph_format.space_after = Pt(3)
    para.paragraph_format.keep_with_next = True
    run = para.add_run(text)
    set_font(run, size=11, bold=True, color=BLACK)

def add_quote(doc, text):
    """灰色背景引用块"""
    para = doc.add_paragraph()
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F7F7F7"/>')
    para._p.get_or_add_pPr().append(shading)
    para.paragraph_format.space_before = Pt(6)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.left_indent = Cm(0.5)
    run = para.add_run(text)
    set_font(run, size=10, color=GRAY)
    run.italic = True

def add_bullet(doc, text):
    """无序列表"""
    para = doc.add_paragraph(style='List Bullet')
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    # 处理加粗文本
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = para.add_run(part[2:-2])
            set_font(run, size=11, bold=True, color=BLACK)
        else:
            run = para.add_run(part)
            set_font(run, size=11, color=BLACK)

def add_numbered(doc, text):
    """有序列表"""
    para = doc.add_paragraph(style='List Number')
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    # 处理加粗文本
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = para.add_run(part[2:-2])
            set_font(run, size=11, bold=True, color=BLACK)
        else:
            run = para.add_run(part)
            set_font(run, size=11, color=BLACK)

def add_paragraph(doc, text):
    """普通段落"""
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(3)
    para.paragraph_format.space_after = Pt(3)
    # 处理加粗文本
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = para.add_run(part[2:-2])
            set_font(run, size=11, bold=True, color=BLACK)
        else:
            run = para.add_run(part)
            set_font(run, size=11, color=BLACK)

def add_table(doc, table_lines):
    """添加表格（飞书风格）"""
    # 解析表格
    rows = []
    for line in table_lines:
        if '---' in line:
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if cells:
            rows.append(cells)
    
    if not rows:
        return
    
    # 创建表格
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    widths = [3.2, 6.8, 5.6] if len(rows[0]) == 3 else [15.6 / len(rows[0])] * len(rows[0])
    for col, width in zip(table.columns, widths):
        col.width = Cm(width)
    for row in table.rows:
        row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
        for cell,width in zip(row.cells,widths):
            cell.width = Cm(width)
    table.rows[0]._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    
    for i, row_data in enumerate(rows):
        for j, cell_text in enumerate(row_data):
            if j >= len(rows[0]):
                raise ValueError('表格列数不一致')
            cell = table.cell(i, j)
            para = cell.paragraphs[0]
            para.paragraph_format.space_before = Pt(3)
            para.paragraph_format.space_after = Pt(3)
            para.paragraph_format.line_spacing = 1.1
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER if i == 0 else WD_ALIGN_PARAGRAPH.LEFT
            
            # 设置单元格样式
            tc = cell._tc
            tcPr = tc.get_or_add_tcPr()
            
            if i == 0:  # 表头：橙色背景
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FF6B35"/>')
                tcPr.append(shading)
                run = para.add_run(cell_text)
                set_font(run, size=10, bold=True, color=WHITE)
            elif j == 0:  # 首列：浅橙色背景
                shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{LIGHT_ORANGE_HEX}"/>')
                tcPr.append(shading)
                run = para.add_run(cell_text)
                set_font(run, size=10, bold=True, color=BLACK)
            else:  # 其他单元格
                run = para.add_run(cell_text)
                set_font(run, size=10, color=BLACK)
    
    doc.add_paragraph()  # 表格后间距

def convert_md_to_docx(input_path, output_path):
    """One reference-derived template for local and cloud generation."""
    md_content = Path(input_path).read_text(encoding='utf-8-sig')
    if len(md_content) > 100000:
        raise ValueError('课纲过长，请控制在100000字符以内')
    elements = parse_markdown(md_content)
    course_titles = [text for kind, text in elements if kind == 'h1']
    if len(course_titles) != 1:
        raise ValueError('课纲必须且只能有一个 H1 课程标题')
    course_title = course_titles[0]
    template = Path(SCRIPT_DIR).parent / '课纲模板.docx'
    doc = Document(str(template))
    doc.core_properties.title = course_title
    # The retained package supplies styles, numbering, media, and page geometry.
    for child in list(doc._element.body):
        if child.tag != qn('w:sectPr'):
            doc._element.body.remove(child)
    current_section = ''
    def finish_section():
        if '主讲人介绍' in current_section:
            add_centered_image(doc, find_image('lecturer'), 10, IMAGE_CAPTIONS['lecturer'])
        elif '课件展示' in current_section:
            add_centered_image(doc, find_image('slides'), 14, '（历史课件示例）')
        elif '课程现场' in current_section:
            add_image_row(doc, [find_image('scene1'), find_image('scene2')], 7)
            add_image_row(doc, [find_image('scene3'), find_image('scene4')], 7, IMAGE_CAPTIONS['scenes'])
    handlers = {'h1':add_h1, 'subtitle':add_subtitle, 'h2':add_h2, 'h3':add_h3,
                'h4':add_h4, 'h5':add_h5, 'quote':add_quote, 'bullet':add_bullet,
                'numbered':add_numbered, 'paragraph':add_paragraph, 'table':add_table}
    for kind, text in elements:
        if kind == 'h2':
            finish_section()
            current_section = text
        handlers[kind](doc, text)
        if kind == 'paragraph' and re.match(r'^\*\*(模块\d+|加餐：)', text):
            doc.paragraphs[-1].paragraph_format.keep_with_next = True
            doc.paragraphs[-1].paragraph_format.space_before = Pt(12)
    finish_section()
    drop_unused_image_relationships(doc)
    for para in doc.paragraphs:
        para.paragraph_format.widow_control = True
        para.paragraph_format.line_spacing = 1.1
        if para.text.strip().startswith('关键词'):
            para.paragraph_format.keep_with_next = True
        if any(r._r.xpath('.//w:drawing') for r in para.runs):
            para.paragraph_format.keep_with_next = True
    for table in doc.tables:
        for row in table.rows:
            if not row._tr.xpath('./w:trPr/w:cantSplit'):
                row._tr.get_or_add_trPr().append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))
    for section in doc.sections:
        section.page_width = Pt(612)
        section.page_height = Pt(792)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc.save(output_path)
    print(f'Word已生成：{output_path}')

def main():
    parser = argparse.ArgumentParser(description='课纲排版 - Markdown 转 Word（带图片版）')
    parser.add_argument('--input', '-i', required=True, help='输入的 Markdown 文件路径')
    parser.add_argument('--output', '-o', help='输出的 Word 文件路径（默认为同名_带图.docx）')
    
    args = parser.parse_args()
    
    input_path = args.input
    if not os.path.exists(input_path):
        print(f"❌ 文件不存在：{input_path}")
        return
    
    if args.output:
        output_path = args.output
    else:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_带图.docx"
    
    convert_md_to_docx(input_path, output_path)

if __name__ == "__main__":
    main()
