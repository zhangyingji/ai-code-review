"""
功能集成测试
测试系统完整的评审流程，包括配置加载、GitLab 集成、LLM 评审、报告生成和数据存储
"""
import sys
import os
import unittest
import yaml
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.gitlab_client import GitLabClient
from src.llm_client import LLMClient
from src.review_engine import ReviewEngine
from src.report_generator import ReportGenerator
from src.storage.mysql_storage import MySQLStorage


class TestIntegration(unittest.TestCase):
    """功能集成测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化 - 加载配置"""
        config_file = 'config.yaml'
        if not os.path.exists(config_file):
            raise FileNotFoundError("配置文件不存在，请先创建 config.yaml")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            cls.config = yaml.safe_load(f)
        
        # 尝试加载本地配置
        local_config_file = 'config.local.yaml'
        if os.path.exists(local_config_file):
            with open(local_config_file, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
                if local_config:
                    cls.config.update(local_config)
        
        # 检查必需配置
        if 'gitlab' not in cls.config:
            raise unittest.SkipTest("GitLab 配置不存在，跳过集成测试")
        
        if 'llm' not in cls.config:
            raise unittest.SkipTest("LLM 配置不存在，跳过集成测试")
        
        cls.gitlab_client = None
        cls.llm_client = None
        cls.review_engine = None
    
    def setUp(self):
        """每个测试方法前执行"""
        print(f"\n{'='*60}")
        print(f"执行测试: {self._testMethodName}")
        print(f"{'='*60}")
    
    def tearDown(self):
        """每个测试方法后执行"""
        if self.gitlab_client:
            try:
                self.gitlab_client.cleanup()
            except:
                pass
    
    def test_01_load_config(self):
        """测试 1: 配置加载"""
        print("测试配置加载...")
        
        try:
            # 验证 GitLab 配置
            self.assertIn('url', self.config['gitlab'])
            self.assertIn('private_token', self.config['gitlab'])
            print(f"✓ GitLab 配置加载成功")
            print(f"  URL: {self.config['gitlab']['url']}")
            
            # 验证 LLM 配置
            self.assertIn('api_url', self.config['llm'])
            self.assertIn('api_key', self.config['llm'])
            self.assertIn('model', self.config['llm'])
            print(f"✓ LLM 配置加载成功")
            print(f"  模型: {self.config['llm']['model']}")
            
            # 验证评审规则
            self.assertIn('review_rules', self.config)
            print(f"✓ 评审规则加载成功")
            print(f"  规则类别数: {len(self.config['review_rules'])}")
            
        except Exception as e:
            self.fail(f"配置加载失败: {e}")
    
    def test_02_gitlab_connection(self):
        """测试 2: GitLab 连接"""
        print("测试 GitLab 连接...")
        
        try:
            # 初始化 GitLab 客户端
            project_id = self.config['gitlab'].get('project_id')
            if not project_id:
                self.skipTest("未配置 project_id")
            
            self.gitlab_client = GitLabClient(
                url=self.config['gitlab']['url'],
                private_token=self.config['gitlab']['private_token'],
                project_id=project_id
            )
            
            self.assertIsNotNone(self.gitlab_client, "GitLab 客户端应该被创建")
            print(f"✓ GitLab 客户端初始化成功")
            print(f"  项目 ID: {project_id}")
            
        except Exception as e:
            self.fail(f"GitLab 连接失败: {e}")
    
    def test_03_llm_connection(self):
        """测试 3: LLM 连接"""
        print("测试 LLM 连接...")
        
        try:
            # 初始化 LLM 客户端
            self.llm_client = LLMClient(
                api_url=self.config['llm']['api_url'],
                api_key=self.config['llm']['api_key'],
                model=self.config['llm']['model'],
                temperature=self.config['llm'].get('temperature', 0.3),
                max_tokens=self.config['llm'].get('max_tokens', 2000)
            )
            
            self.assertIsNotNone(self.llm_client, "LLM 客户端应该被创建")
            print(f"✓ LLM 客户端初始化成功")
            print(f"  API URL: {self.config['llm']['api_url']}")
            print(f"  模型: {self.config['llm']['model']}")
            
        except Exception as e:
            self.fail(f"LLM 初始化失败: {e}")
    
    def test_04_review_engine_initialization(self):
        """测试 4: 评审引擎初始化"""
        print("测试评审引擎初始化...")
        
        try:
            # 获取项目配置
            project_id = self.config['gitlab'].get('project_id')
            if not project_id:
                self.skipTest("未配置 project_id")
            
            # 初始化 GitLab 客户端
            self.gitlab_client = GitLabClient(
                url=self.config['gitlab']['url'],
                private_token=self.config['gitlab']['private_token'],
                project_id=project_id
            )
            
            # 初始化 LLM 客户端
            self.llm_client = LLMClient(
                api_url=self.config['llm']['api_url'],
                api_key=self.config['llm']['api_key'],
                model=self.config['llm']['model']
            )
            
            # 初始化评审引擎
            self.review_engine = ReviewEngine(
                gitlab_client=self.gitlab_client,
                llm_client=self.llm_client,
                review_rules=self.config['review_rules'],
                enable_concurrent=self.config.get('performance', {}).get('enable_concurrent', True),
                max_workers=self.config.get('performance', {}).get('max_workers', 3)
            )
            
            self.assertIsNotNone(self.review_engine, "评审引擎应该被创建")
            print(f"✓ 评审引擎初始化成功")
            print(f"✓ 并发模式: {self.config.get('performance', {}).get('enable_concurrent', True)}")
            
        except Exception as e:
            self.fail(f"评审引擎初始化失败: {e}")
    
    def test_05_report_generator(self):
        """测试 5: 报告生成器"""
        print("测试报告生成器...")
        
        try:
            # 创建报告生成器
            output_dir = self.config.get('report', {}).get('output_dir', './reports')
            report_generator = ReportGenerator(output_dir=output_dir)
            
            self.assertIsNotNone(report_generator, "报告生成器应该被创建")
            print(f"✓ 报告生成器创建成功")
            print(f"  输出目录: {output_dir}")
            
            # 准备测试数据
            test_review_data = {
                'metadata': {
                    'project_id': 999,
                    'project_name': 'test-project',
                    'review_branch': 'test-branch',
                    'base_branch': 'main',
                    'review_time': datetime.now().isoformat(),
                    'total_commits': 1,
                    'total_files_reviewed': 1
                },
                'statistics': {
                    'total_issues': 1,
                    'by_severity': {
                        'critical': 0,
                        'major': 1,
                        'minor': 0,
                        'suggestion': 0
                    },
                    'by_type': {
                        '测试': 1
                    }
                },
                'file_reviews': [
                    {
                        'file_path': 'test.py',
                        'issues': [
                            {
                                'line': '1',
                                'type': '测试',
                                'severity': 'major',
                                'description': '测试问题',
                                'suggestion': '测试建议'
                            }
                        ]
                    }
                ]
            }
            
            # 生成 HTML 报告
            html_path = report_generator.generate_report(
                review_data=test_review_data,
                format='html',
                group_by_author=False
            )
            
            self.assertTrue(os.path.exists(html_path), "HTML 报告文件应该存在")
            print(f"✓ HTML 报告生成成功")
            print(f"  文件路径: {html_path}")
            
            # 生成 Excel 报告
            excel_path = report_generator.generate_report(
                review_data=test_review_data,
                format='excel',
                group_by_author=False
            )
            
            self.assertTrue(os.path.exists(excel_path), "Excel 报告文件应该存在")
            print(f"✓ Excel 报告生成成功")
            print(f"  文件路径: {excel_path}")
            
        except Exception as e:
            self.fail(f"报告生成器测试失败: {e}")
    
    def test_06_storage_integration(self):
        """测试 6: 数据库存储集成"""
        print("测试数据库存储集成...")
        
        # 检查存储是否启用
        storage_config = self.config.get('storage', {})
        if not storage_config.get('enabled'):
            self.skipTest("存储功能未启用")
        
        try:
            # 创建存储实例
            storage = MySQLStorage(storage_config)
            print(f"✓ 存储实例创建成功")
            
            # 准备测试数据
            review_data = {
                'metadata': {
                    'project_id': 999,
                    'project_name': 'integration-test',
                    'review_branch': 'test-branch',
                    'base_branch': 'main',
                    'review_time': datetime.now().isoformat(),
                    'duration_seconds': 10.5,
                    'total_commits': 1,
                    'total_files_reviewed': 1
                },
                'statistics': {
                    'total_issues': 1,
                    'by_severity': {
                        'critical': 0,
                        'major': 1,
                        'minor': 0,
                        'suggestion': 0
                    }
                },
                'file_reviews': [
                    {
                        'file_path': 'test.py',
                        'issues': [
                            {
                                'line': '10',
                                'type': '集成测试',
                                'severity': 'major',
                                'description': '集成测试问题',
                                'suggestion': '集成测试建议',
                                'author': 'tester',
                                'author_email': 'tester@test.com'
                            }
                        ]
                    }
                ]
            }
            
            # 保存数据
            review_id = storage.save_review_with_issues(review_data)
            self.assertIsNotNone(review_id, "应该返回 review_id")
            print(f"✓ 数据保存成功: {review_id}")
            
            # 查询验证
            saved_review = storage.get_review(review_id)
            self.assertIsNotNone(saved_review, "应该能查询到保存的数据")
            self.assertEqual(saved_review['project_name'], 'integration-test')
            print(f"✓ 数据查询验证成功")
            
            # 清理测试数据
            storage.delete_review(review_id)
            print(f"✓ 测试数据清理成功")
            
        except Exception as e:
            self.fail(f"存储集成测试失败: {e}")
    
    def test_07_end_to_end_workflow(self):
        """测试 7: 端到端工作流（需要真实的 GitLab 项目和分支）"""
        print("测试端到端工作流...")
        
        # 获取分支配置
        source_branch = self.config.get('branch', {}).get('review_branch')
        target_branch = self.config.get('branch', {}).get('base_branch')
        
        if not source_branch or not target_branch:
            self.skipTest("未配置评审分支，跳过端到端测试")
        
        try:
            print(f"  源分支: {source_branch}")
            print(f"  目标分支: {target_branch}")
            
            # 获取项目配置
            project_id = self.config['gitlab'].get('project_id')
            if not project_id:
                self.skipTest("未配置 project_id")
            
            # 初始化 GitLab 客户端
            self.gitlab_client = GitLabClient(
                url=self.config['gitlab']['url'],
                private_token=self.config['gitlab']['private_token'],
                project_id=project_id
            )
            print(f"✓ GitLab 客户端初始化完成")
            
            # 初始化 LLM 客户端
            self.llm_client = LLMClient(
                api_url=self.config['llm']['api_url'],
                api_key=self.config['llm']['api_key'],
                model=self.config['llm']['model'],
                temperature=self.config['llm'].get('temperature', 0.3),
                max_tokens=self.config['llm'].get('max_tokens', 2000)
            )
            print(f"✓ LLM 客户端初始化完成")
            
            # 初始化评审引擎
            self.review_engine = ReviewEngine(
                gitlab_client=self.gitlab_client,
                llm_client=self.llm_client,
                review_rules=self.config['review_rules'],
                enable_concurrent=False,  # 测试时使用串行模式
                max_workers=1
            )
            print(f"✓ 评审引擎初始化完成")
            
            # 执行评审（限制文件数量以加快测试）
            print(f"  开始执行评审...")
            start_time = time.time()
            
            review_data = self.review_engine.review_branches(
                source_branch=source_branch,
                target_branch=target_branch,
                time_range=None
            )
            
            duration = time.time() - start_time
            print(f"✓ 评审完成，耗时: {duration:.2f} 秒")
            
            # 验证评审结果
            self.assertIn('metadata', review_data)
            self.assertIn('statistics', review_data)
            self.assertIn('file_reviews', review_data)
            
            print(f"  总文件数: {review_data['metadata']['total_files_reviewed']}")
            print(f"  总问题数: {review_data['statistics']['total_issues']}")
            print(f"    严重: {review_data['statistics']['by_severity'].get('critical', 0)}")
            print(f"    主要: {review_data['statistics']['by_severity'].get('major', 0)}")
            print(f"    次要: {review_data['statistics']['by_severity'].get('minor', 0)}")
            print(f"    建议: {review_data['statistics']['by_severity'].get('suggestion', 0)}")
            
            # 生成报告
            report_generator = ReportGenerator(
                output_dir=self.config.get('report', {}).get('output_dir', './reports')
            )
            
            report_path = report_generator.generate_report(
                review_data=review_data,
                format='html',
                group_by_author=True
            )
            
            self.assertTrue(os.path.exists(report_path), "报告文件应该存在")
            print(f"✓ 报告生成成功: {report_path}")
            
        except Exception as e:
            self.fail(f"端到端工作流测试失败: {e}")


def run_tests():
    """运行测试"""
    print("\n" + "="*70)
    print("功能集成测试")
    print("="*70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestIntegration)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 打印测试总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"总测试数: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"跳过: {len(result.skipped)}")
    
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
