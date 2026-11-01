"""Local questionnaire preparation and evidence checks. No network calls or email sends."""
import argparse
import json
import os
import re
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import uuid4

SKILL = Path(__file__).resolve().parents[1]
PROFILE_DIR = Path(os.environ.get('BOAI_QUESTIONNAIRE_HOME', Path.home()/'.config'/'boai-questionnaire'))
PROFILE = PROFILE_DIR/'profile.json'
SHANGHAI = timezone(timedelta(hours=8))

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name+'.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.replace(path)

def profile():
    return read(PROFILE) if PROFILE.exists() else {}

def valid_email(value):
    return bool(re.fullmatch(r'[^\s@<>;,]+@[^\s@<>;,]+\.[^\s@<>;,]+', value))

def clean_name(value):
    value = value.strip()
    if not value or len(value) > 60 or any(ord(c)<32 for c in value):
        raise ValueError('甲方名称不能为空、含控制字符或超过60字。请使用明确的客户简称。')
    return value

def settings(args):
    config = profile()
    changed = False
    if args.email is not None:
        if not valid_email(args.email):
            raise ValueError('请输入一个明确的报告收件邮箱，不接受多个地址或换行。')
        config['report_email'] = args.email
        changed = True
    if args.style:
        config['ppt_style'] = args.style
        changed = True
    if changed:
        config['updated_at'] = datetime.now(SHANGHAI).isoformat(timespec='seconds')
        write(PROFILE, config)
    return {'profile_path': str(PROFILE), 'settings': config, 'missing_email': not bool(config.get('report_email'))}

def api_question(question):
    result = {key: value for key, value in question.items() if key not in {'key','max_choices','exclusive_options','incompatible_options'}}
    if question['type'] == 'select':
        result['options'] = [{'name': name, 'hue': 'Blue'} for name in question['options']]
        result['option_display_mode'] = 1
    return result

def prepare(args):
    client = clean_name(args.client)
    out = Path(args.out).resolve()
    project_file = out/'project.json'
    if project_file.exists():
        existing = read(project_file)
        if existing.get('client') != client or (args.batch and args.batch != existing.get('batch')):
            raise ValueError('项目目录已属于另一客户或班次；请提供新的项目目录，不覆盖旧问卷。')
        return {'status':'existing_project_reused','project':str(project_file),'cloud':existing.get('cloud',{}),'missing_email':not bool(existing.get('report_email') or profile().get('report_email'))}
    if out.exists() and any(out.iterdir()):
        raise ValueError('新项目目录非空；请选择空目录，避免覆盖其他文件。')
    if getattr(args,'name_required',None) not in {'yes','no'}:
        raise ValueError('每次新建问卷都必须先询问姓名是否必填，并显式传入 --name-required yes 或 no。')
    now = datetime.now(SHANGHAI)
    batch = args.batch or now.strftime('%Y%m%d')+'-'+uuid4().hex[:6]
    if not re.fullmatch(r'[\w-]{1,50}', batch):
        raise ValueError('班次编码仅使用字母、数字、中文、下划线或连字符，最多50字符。')
    config = profile()
    schema = read(SKILL/'templates'/'learner-questionnaire.json')
    annual_base = config.get('annual_bases',{}).get(str(now.year))
    legacy_index = config.get('legacy_index')
    if annual_base and legacy_index and annual_base.get('base_token') == legacy_index.get('base_token') and annual_base.get('index_table_id') == legacy_index.get('table_id'):
        legacy_index = None  # One physical index receives one project row.
    schema['questions'][0]['required'] = args.name_required == 'yes'
    schema['questions'][0]['description'] = '必填。' if args.name_required == 'yes' else '选填。'
    title = f'{client}｜课前调研｜{batch}'
    project = {
        'schema_version':schema['schema_version'], 'client':client, 'batch':batch,
        'title':title, 'audience':schema['audience'], 'questionnaire_phase':'pre-course', 'created_at':now.isoformat(timespec='seconds'),
        'year':now.year, 'report_email':config.get('report_email'), 'ppt_style':config.get('ppt_style'),
        'annual_base':annual_base,
        'legacy_index':legacy_index, 'status':'prepared_locally',
        'description':schema['description'], 'name_required':args.name_required == 'yes',
        'questions':schema['questions'], 'cloud':{}
    }
    write(project_file, project)
    first = schema['questions'][0]
    write(out/'table-fields.json', [{'name':first['title'],'type':'text'}, {'name':'提交时间','type':'created_at','style':{'format':'yyyy-MM-dd HH:mm'}}])
    write(out/'questions.json', [api_question(q) for q in schema['questions']])
    md=['# '+title,'','状态：本地准备，尚未创建飞书问卷。','',project['description'],'']
    for q in schema['questions']:
        md += ['## '+q['title'], '', ('条件显示时必填' if q.get('visible_rule') and q['required'] else '必填' if q['required'] else '选填')+' · '+q['description'], '']
        md += ['- '+name for name in q.get('options',[])]
        md.append('')
    (out/'questionnaire.md').write_text('\n'.join(md),encoding='utf-8')
    (out/'AI-README.md').write_text(f'# {title}\n\n状态：本地准备，尚未创建飞书资源。更新时间：{now.date()}。\n\n用途：{client}的独立学员调研。入口：project.json、questionnaire.md、questions.json；部署后将真实云端坐标写入project.json。内部数据、邮箱和客户资料不得进入公开Skill包。\n',encoding='utf-8')
    return {'status':'prepared_locally','project':str(project_file),'year':now.year,'needs_annual_base':project['annual_base'] is None,'missing_email':not bool(project['report_email']),'question_count':len(schema['questions'])}

def nonempty(value):
    return value is not None and value != [] and value != {} and (not isinstance(value,str) or bool(value.strip()))

def answer_value(row, question, field_names_by_id):
    candidates = [question.get('field_id'),field_names_by_id.get(question.get('field_id')),question.get('field_name'),question['title'],question['key']]
    return next((row[name] for name in candidates if name and name in row), None)

def question_applies(row, question, questions, field_names_by_id):
    rule = question.get('visible_rule') or {}
    matches = []
    for reference, operator, expected in rule.get('conditions', []):
        source = next((q for q in questions if reference in [q['key'],q['title'],q.get('field_id')]), None)
        if source is None or operator != 'intersects':
            raise ValueError('无法可靠计算条件题分母；请核对显隐规则。')
        actual = answer_value(row, source, field_names_by_id)
        selected = actual if isinstance(actual,list) else [actual]
        matches.append(any(value in expected for value in selected))
    if not matches: return True
    return any(matches) if rule.get('logic') == 'or' else all(matches)

def analyze(args):
    root = Path(args.project).resolve()
    project = read(root/'project.json')
    if args.stage == 'post-course' and project.get('questionnaire_phase') != 'post-course':
        raise ValueError('当前项目是课前需求问卷，不能标为课后成效数据；请关联真实课后问卷或作品验收证据。')
    answers = Path(args.answers).resolve()
    rows = [json.loads(line) for line in answers.read_text(encoding='utf-8-sig').splitlines() if line.strip()]
    if any(not isinstance(r,dict) for r in rows):
        raise ValueError('每行答卷必须是JSON对象。')
    completeness = 'unknown'
    field_names_by_id = {}
    if args.manifest:
        manifest = read(args.manifest)
        field_names_by_id = {details['field_id']:name for name,details in manifest.get('columns',{}).items() if details.get('field_id')}
        if manifest.get('has_more') is not False:
            raise ValueError('分页尚未完成：先取得后续页面，不能把局部导出当完整数据。')
        if manifest.get('records_count') != len(rows):
            raise ValueError('manifest数量与答卷行数不一致。')
        cloud = project.get('cloud',{})
        expected_base = cloud.get('base_token') or (project.get('annual_base') or {}).get('base_token')
        for expected, actual, kind in [(cloud.get('table_id'),manifest.get('table_id'),'子表'),(expected_base,manifest.get('base_token'),'Base')]:
            if expected and actual != expected:
                raise ValueError(kind+'来源与选定项目不匹配，拒绝混合客户数据。')
        completeness = 'complete_export_scope'
    # A repeated record ID is an overlapping export, not a repeated person.
    ids=[r.get('record_id') for r in rows if r.get('record_id')]
    repeated = [key for key,n in Counter(ids).items() if n>1]
    if repeated:
        raise ValueError('存在重复record_id，可能是分页重叠；请先核对导出，不能重复计数。')
    exclude = set(args.exclude_record or [])
    if not exclude.issubset(set(ids)):
        raise ValueError('排除名单中存在未在本次导出发现的记录。')
    synthetic = set(project.get('synthetic_record_ids',[])) & set(ids)
    simulation = getattr(args, 'simulation_only', False)
    if simulation:
        if not project.get('test_project') or not synthetic:
            raise ValueError('模拟分析仅限明确标记test_project且存在已登记模拟记录的项目。')
        exclude.update(set(ids) - synthetic)
        if any(not r.get('record_id') for r in rows):
            raise ValueError('模拟分析要求每条答卷有record_id，以免混入真实答卷。')
    else:
        exclude.update(synthetic)
    included = [r for r in rows if r.get('record_id') not in exclude]
    result={'client':project['client'],'batch':project['batch'],'stage':args.stage,'schema_version':project['schema_version'],'source':str(answers),'completeness':completeness,'raw_records':len(rows),'excluded_records':sorted(exclude),'response_records':len(included),'unit':'答卷份数，不等于去重人数或企业数','questions':{},'flags':[]}
    for q in project['questions']:
        key, title = q['key'], q['title']
        # Exact semantic mapping from this project's own schema; no substring matching.
        applicable = [(i,r) for i,r in enumerate(included) if question_applies(r,q,project['questions'],field_names_by_id)]
        values = [(r.get('record_id',f'row-{i+1}'),answer_value(r,q,field_names_by_id)) for i,r in applicable]
        present = [(rid,v) for rid,v in values if nonempty(v)]
        stats={'title':title,'type':q['type'],'response_records':len(included),'applicable_records':len(applicable),'not_applicable':len(included)-len(applicable),'nonempty':len(present),'missing':len(applicable)-len(present)}
        if q['type']=='select':
            counts=Counter(); valid=0
            for rid,value in present:
                selected=value if isinstance(value,list) else [value]
                issue=None
                if any(not isinstance(v,str) or v not in q['options'] for v in selected): issue='unknown_option_or_type'
                elif len(set(selected)) != len(selected): issue='duplicate_option'
                elif not q.get('multiple') and len(selected)!=1: issue='invalid_single_select'
                elif q.get('max_choices') and len(selected)>q['max_choices']: issue='over_selection_limit'
                elif len(selected)>1 and any(v in q.get('exclusive_options',[]) for v in selected): issue='exclusive_option_conflict'
                elif any(all(v in selected for v in pair) for pair in q.get('incompatible_options',[])): issue='incompatible_options'
                if issue:
                    result['flags'].append({'record_id':rid,'question':key,'issue':issue})
                    continue
                valid+=1; counts.update(selected)
            stats.update(valid_denominator=valid,counts=dict(counts),percent={k:round(100*v/valid,1) for k,v in counts.items()} if valid else {})
        result['questions'][key]=stats
    result['analysis_scope'] = 'simulation_only' if simulation else 'real_responses_only'
    result['synthetic_response_records'] = len(included) if simulation else 0
    result['real_response_records'] = 0 if simulation else len(included)
    output_root = root/'simulation-analysis' if simulation else root
    write(output_root/'metrics.json',result)
    lines=[f'# {project["client"]}｜分析输入核对','',f'状态：{len(included)}份答卷；完整性：{completeness}；阶段：{args.stage}。','', '本文件只有结构化计数。核心结论须阅读实际开放回答并关联课程目标；不能直接作为成效报告。','']
    for key, stats in result['questions'].items():
        lines += ['## '+stats['title'],'',f'非空 {stats["nonempty"]}/{stats["applicable_records"]}（适用答卷）；缺失 {stats["missing"]}。','']
        lines += [f'- {name}：{n}份（有效答题分母 {stats["valid_denominator"]}）' for name,n in stats.get('counts',{}).items()]
        lines.append('')
    if simulation:
        lines.insert(2, '【模拟测试】仅验证分析交付流程；真实答卷0份，不代表教学效果或客户总体。')
    (output_root/'analysis-input.md').write_text('\n'.join(lines),encoding='utf-8')
    return {'status':'no_responses' if not included else 'metrics_ready','records':len(included),'flags':len(result['flags']),'completeness':completeness,'next':'无答卷：返回填写链接，不制作空结论PPT或发信。' if not included else '阅读开放回答→形成结论与页纲→调用guizang-ppt-skill→核验→按用户授权发送。'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    subs=parser.add_subparsers(dest='command',required=True)
    p=subs.add_parser('settings');p.add_argument('--email');p.add_argument('--style',choices=['swiss-ikb','magazine']);p.set_defaults(handler=settings)
    p=subs.add_parser('prepare');p.add_argument('--client',required=True);p.add_argument('--out',required=True);p.add_argument('--batch');p.add_argument('--name-required',choices=['yes','no']);p.set_defaults(handler=prepare)
    p=subs.add_parser('analyze');p.add_argument('--project',required=True);p.add_argument('--answers',required=True);p.add_argument('--manifest');p.add_argument('--exclude-record',action='append',default=[]);p.add_argument('--stage',choices=['pre-course','post-course'],default='pre-course');p.set_defaults(handler=analyze)
    p.add_argument('--simulation-only',action='store_true',help='仅分析test_project中已登记的模拟记录，独立输出，不改变真实分析默认排除规则')
    args=parser.parse_args()
    try:
        print(json.dumps(args.handler(args),ensure_ascii=False,indent=2))
    except (ValueError,OSError,KeyError) as error:
        parser.exit(2,str(error)+'\n')

if __name__=='__main__':
    main()
