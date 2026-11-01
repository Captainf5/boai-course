import argparse
import importlib.util
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('workflow',SOURCE/'scripts'/'workflow.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

class WorkflowTests(unittest.TestCase):
    def test_simulation_isolated_from_real_metrics(self):
        args=self.fixture([{'record_id':'sim'},{'record_id':'real'}])
        project=w.read(self.project/'project.json')
        project.update(test_project=True,synthetic_record_ids=['sim'])
        w.write(self.project/'project.json',project)
        w.analyze(args)
        original=(self.project/'metrics.json').read_bytes()
        args.simulation_only=True
        w.analyze(args)
        result=w.read(self.project/'simulation-analysis'/'metrics.json')
        self.assertEqual(result['response_records'],1)
        self.assertEqual(result['real_response_records'],0)
        self.assertEqual(result['excluded_records'],['real'])
        self.assertEqual((self.project/'metrics.json').read_bytes(),original)
        self.assertEqual(w.read(self.project/'project.json')['synthetic_record_ids'],['sim'])

    def test_simulation_rejects_real_project(self):
        args=self.fixture([{'record_id':'sim'}]);args.simulation_only=True
        with self.assertRaises(ValueError):w.analyze(args)

    def test_simulation_rejects_unidentified_rows(self):
        args=self.fixture([{'record_id':'sim'},{}]);args.simulation_only=True
        project=w.read(self.project/'project.json')
        project.update(test_project=True,synthetic_record_ids=['sim'])
        w.write(self.project/'project.json',project)
        with self.assertRaises(ValueError):w.analyze(args)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.profile_patch=patch.object(w,'PROFILE',self.root/'private'/'profile.json')
        self.profile_patch.start()
        self.project=self.root/'project'

    def tearDown(self):
        self.profile_patch.stop();self.temp.cleanup()

    def prepare(self,client='示例甲方',batch='cohort-01',name_required='no'):
        return w.prepare(argparse.Namespace(client=client,batch=batch,out=str(self.project),name_required=name_required))

    def fixture(self,rows,**manifest_changes):
        self.prepare()
        project=w.read(self.project/'project.json')
        project['cloud']={'base_token':'base-test','table_id':'table-test'}
        w.write(self.project/'project.json',project)
        path=self.root/'records.ndjson'
        path.write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows),encoding='utf-8')
        manifest={'records_count':len(rows),'has_more':False,'table_id':'table-test','base_token':'base-test'}
        manifest.update(manifest_changes)
        w.write(self.root/'manifest.json',manifest)
        return argparse.Namespace(project=str(self.project),answers=str(path),manifest=str(self.root/'manifest.json'),exclude_record=[],stage='pre-course')

    def test_new_user_has_no_author_email(self):
        result=self.prepare()
        self.assertTrue(result['missing_email'])
        self.assertIsNone(w.read(self.project/'project.json')['report_email'])
        self.assertIn('示例甲方',w.read(self.project/'project.json')['title'])
        self.assertEqual(result['question_count'],12)
        self.assertEqual(w.read(self.project/'project.json')['audience'],'learner')

    def test_first_email_saved_and_reused(self):
        w.settings(argparse.Namespace(email='owner@example.org',style='swiss-ikb'))
        self.assertFalse(self.prepare()['missing_email'])
        self.assertEqual(w.read(self.project/'project.json')['report_email'],'owner@example.org')

    def test_conditional_department_denominator(self):
        args=self.fixture([{'record_id':'1','department':['销售／市场']},{'record_id':'2','department':['其他'],'department_other':'质量部'},{'record_id':'3','department':['其他']}])
        w.analyze(args)
        stats=w.read(self.project/'metrics.json')['questions']['department_other']
        self.assertEqual(stats['applicable_records'],2)
        self.assertEqual(stats['not_applicable'],1)
        self.assertEqual(stats['missing'],1)

    def test_conditional_rule_reaches_form_payload(self):
        self.prepare()
        questions=w.read(self.project/'questions.json')
        self.assertEqual(questions[2]['visible_rule']['conditions'][0],['您所在的部门','intersects',['其他']])
        self.assertTrue(questions[2]['required'])
        self.assertIn('Skill',questions[3]['options'][3]['name'])

    def test_address_injection_rejected(self):
        for address in ['a@example.org\nBcc:b@example.org','a@example.org,b@example.org','bad']:
            with self.assertRaises(ValueError): w.settings(argparse.Namespace(email=address,style=None))

    def test_resume_does_not_overwrite(self):
        self.prepare()
        p=w.read(self.project/'project.json');p['cloud']={'table_id':'kept'};w.write(self.project/'project.json',p)
        self.assertEqual(self.prepare()['cloud']['table_id'],'kept')
        with self.assertRaises(ValueError):self.prepare('另一客户')
        with self.assertRaises(ValueError):self.prepare(batch='cohort-02')

    def test_blank_client_rejected(self):
        with self.assertRaises(ValueError):self.prepare('  ')

    def test_year_routing_preserves_old_base(self):
        w.write(w.PROFILE,{'annual_bases':{'2026':{'base_token':'old'}}})
        class Date2027(datetime):
            @classmethod
            def now(cls,tz=None): return cls(2027,1,1,tzinfo=w.SHANGHAI)
        with patch.object(w,'datetime',Date2027):result=self.prepare()
        self.assertEqual(result['year'],2027)
        self.assertTrue(result['needs_annual_base'])
        self.assertEqual(w.profile()['annual_bases']['2026']['base_token'],'old')

    def test_year_end_uses_designated_base_and_one_index(self):
        w.write(w.PROFILE,{'annual_bases':{'2026':{'base_token':'designated','index_table_id':'index'}},'legacy_index':{'base_token':'designated','table_id':'index'}})
        class YearEnd(datetime):
            @classmethod
            def now(cls,tz=None): return cls(2026,12,31,23,59,tzinfo=w.SHANGHAI)
        with patch.object(w,'datetime',YearEnd):result=self.prepare()
        p=w.read(self.project/'project.json')
        self.assertFalse(result['needs_annual_base'])
        self.assertEqual(p['annual_base']['base_token'],'designated')
        self.assertIsNone(p['legacy_index'])

    def test_existing_project_keeps_coordinates_after_route_change(self):
        self.prepare()
        p=w.read(self.project/'project.json');p['cloud']={'base_token':'original','table_id':'kept'};w.write(self.project/'project.json',p)
        w.write(w.PROFILE,{'annual_bases':{'2026':{'base_token':'replacement'}}})
        self.assertEqual(self.prepare()['cloud'],{'base_token':'original','table_id':'kept'})

    def test_valid_denominator_and_unknown_answers(self):
        args=self.fixture([{'record_id':'1','priority_task':['数据整理与分析']},{'record_id':'2','priority_task':['不存在的选项']},{'record_id':'3','priority_task':['数据整理与分析','汇报与写材料']},{'record_id':'4','priority_task':None}])
        out=w.analyze(args);m=w.read(self.project/'metrics.json')
        self.assertEqual(out['flags'],2)
        self.assertEqual(m['questions']['priority_task']['valid_denominator'],1)
        self.assertEqual(m['questions']['priority_task']['missing'],1)

    def test_partial_export_rejected(self):
        with self.assertRaises(ValueError):w.analyze(self.fixture([],has_more=True))

    def test_wrong_client_table_rejected(self):
        with self.assertRaises(ValueError):w.analyze(self.fixture([],table_id='another-client'))

    def test_empty_has_no_report_instruction(self):
        out=w.analyze(self.fixture([]));self.assertEqual(out['status'],'no_responses')

    def test_duplicate_records_rejected(self):
        with self.assertRaises(ValueError):w.analyze(self.fixture([{'record_id':'1'},{'record_id':'1'}]))

    def test_equal_answers_are_not_person_duplicates(self):
        args=self.fixture([{'record_id':'1','priority_task':['数据整理与分析']},{'record_id':'2','priority_task':['数据整理与分析']}])
        self.assertEqual(w.analyze(args)['records'],2)

    def test_explicit_test_exclusion(self):
        args=self.fixture([{'record_id':'real'},{'record_id':'test'}]);args.exclude_record=['test']
        self.assertEqual(w.analyze(args)['records'],1)

    def test_known_simulation_automatically_excluded(self):
        args=self.fixture([{'record_id':'real'},{'record_id':'simulation'}])
        p=w.read(self.project/'project.json');p['synthetic_record_ids']=['simulation'];w.write(self.project/'project.json',p)
        self.assertEqual(w.analyze(args)['records'],1)

    def test_conflicting_install_conditions_flagged(self):
        args=self.fixture([{'record_id':'1','practice_conditions':['可下载安装客户端','公司不允许下载安装客户端']}])
        w.analyze(args)
        flags=w.read(self.project/'metrics.json')['flags']
        self.assertTrue(any(f['issue']=='incompatible_options' for f in flags))

    def test_pre_data_cannot_become_post_effect(self):
        args=self.fixture([{'record_id':'real'}]);args.stage='post-course'
        with self.assertRaises(ValueError):w.analyze(args)

    def test_name_choice_required_each_new_project(self):
        with self.assertRaises(ValueError):self.prepare(name_required=None)
        self.assertFalse((self.project/'project.json').exists())

    def test_explicit_name_required_is_applied(self):
        self.prepare(name_required='yes')
        project=w.read(self.project/'project.json')
        self.assertTrue(project['questions'][0]['required'])
        self.assertEqual(project['questions'][0]['title'],'姓名')

    def test_missing_optional_name_keeps_response(self):
        args=self.fixture([{'record_id':'1','learner_name':None,'priority_task':['数据整理与分析']}])
        self.assertEqual(w.analyze(args)['records'],1)

    def test_manifest_resolves_field_id_to_old_column_name(self):
        args=self.fixture([{'record_id':'1','旧的底层字段名':['数据整理与分析']}])
        project=w.read(self.project/'project.json')
        next(q for q in project['questions'] if q['key']=='priority_task')['field_id']='fld-real'
        w.write(self.project/'project.json',project)
        manifest=w.read(args.manifest);manifest['columns']={'旧的底层字段名':{'field_id':'fld-real'}};w.write(args.manifest,manifest)
        w.analyze(args)
        self.assertEqual(w.read(self.project/'metrics.json')['questions']['priority_task']['counts']['数据整理与分析'],1)

if __name__=='__main__':unittest.main(verbosity=2)
