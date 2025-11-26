"""
数据库连接测试
测试 MySQL 数据库的连接、表结构创建、数据增删改查操作
"""
import sys
import os
import unittest
import yaml
import uuid
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.storage.mysql_storage import MySQLStorage
from src.storage.models import create_tables, drop_tables
from sqlalchemy import create_engine, inspect


class TestDatabaseConnection(unittest.TestCase):
    """数据库连接测试类"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化 - 加载配置"""
        config_file = 'config.yaml'
        if not os.path.exists(config_file):
            raise FileNotFoundError("配置文件不存在，请先创建 config.yaml")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # 尝试加载本地配置
        local_config_file = 'config.local.yaml'
        if os.path.exists(local_config_file):
            with open(local_config_file, 'r', encoding='utf-8') as f:
                local_config = yaml.safe_load(f)
                if local_config:
                    config.update(local_config)
        
        # 检查是否启用存储
        if not config.get('storage', {}).get('enabled'):
            raise unittest.SkipTest("存储功能未启用，跳过数据库测试")
        
        cls.storage_config = config['storage']
        cls.storage = None
    
    def setUp(self):
        """每个测试方法前执行"""
        print(f"\n{'='*60}")
        print(f"执行测试: {self._testMethodName}")
        print(f"{'='*60}")
    
    def tearDown(self):
        """每个测试方法后执行"""
        if self.storage:
            # 清理测试数据
            pass
    
    def test_01_database_connection(self):
        """测试 1: 数据库连接"""
        print("测试数据库连接...")
        
        try:
            # 创建存储实例
            storage = MySQLStorage(self.storage_config)
            self.assertIsNotNone(storage.engine, "数据库引擎应该被创建")
            self.assertIsNotNone(storage.Session, "Session 工厂应该被创建")
            
            # 测试连接
            session = storage.Session()
            session.execute("SELECT 1")
            session.close()
            
            print("✓ 数据库连接成功")
            print(f"✓ 连接字符串格式正确")
            print(f"✓ 字符集: {self.storage_config['connection'].get('charset', 'utf8mb4')}")
            
        except Exception as e:
            self.fail(f"数据库连接失败: {e}")
    
    def test_02_create_tables(self):
        """测试 2: 创建表结构"""
        print("测试创建表结构...")
        
        try:
            # 创建数据库引擎
            conn_config = self.storage_config['connection']
            connection_string = (
                f"mysql+pymysql://{conn_config['username']}:{conn_config['password']}"
                f"@{conn_config['host']}:{conn_config.get('port', 3306)}"
                f"/{conn_config['database']}"
                f"?charset={conn_config.get('charset', 'utf8mb4')}"
            )
            engine = create_engine(connection_string)
            
            # 删除旧表（如果存在）
            print("删除旧表（如果存在）...")
            drop_tables(engine)
            
            # 创建新表
            print("创建新表...")
            create_tables(engine)
            
            # 验证表结构
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            
            self.assertIn('review_records', tables, "review_records 表应该存在")
            self.assertIn('review_issues', tables, "review_issues 表应该存在")
            
            # 验证 review_records 表结构
            columns = {col['name']: col for col in inspector.get_columns('review_records')}
            required_columns = ['review_id', 'project_id', 'review_branch', 'base_branch', 
                              'review_time', 'total_issues', 'critical_count', 'major_count', 
                              'minor_count', 'suggestion_count']
            for col_name in required_columns:
                self.assertIn(col_name, columns, f"review_records 应该有 {col_name} 列")
            
            # 验证 review_issues 表结构
            columns = {col['name']: col for col in inspector.get_columns('review_issues')}
            required_columns = ['issue_id', 'review_id', 'file_path', 'severity', 
                              'description', 'status']
            for col_name in required_columns:
                self.assertIn(col_name, columns, f"review_issues 应该有 {col_name} 列")
            
            # 验证索引
            indexes = inspector.get_indexes('review_records')
            print(f"✓ review_records 表创建成功，包含 {len(indexes)} 个索引")
            
            indexes = inspector.get_indexes('review_issues')
            print(f"✓ review_issues 表创建成功，包含 {len(indexes)} 个索引")
            
        except Exception as e:
            self.fail(f"创建表结构失败: {e}")
    
    def test_03_save_review_data(self):
        """测试 3: 保存评审数据"""
        print("测试保存评审数据...")
        
        try:
            # 创建存储实例
            storage = MySQLStorage(self.storage_config)
            
            # 准备测试数据
            review_data = {
                'metadata': {
                    'project_id': 999,
                    'project_name': 'test-project',
                    'review_branch': 'feature/test',
                    'base_branch': 'main',
                    'review_time': datetime.now().isoformat(),
                    'duration_seconds': 120.5,
                    'total_commits': 5,
                    'total_files_reviewed': 10,
                    'time_filter_enabled': False
                },
                'statistics': {
                    'total_issues': 3,
                    'by_severity': {
                        'critical': 1,
                        'major': 1,
                        'minor': 1,
                        'suggestion': 0
                    }
                },
                'file_reviews': [
                    {
                        'file_path': 'src/test.py',
                        'issues': [
                            {
                                'line': '10',
                                'type': '安全性',
                                'severity': 'critical',
                                'description': '测试问题1',
                                'suggestion': '测试建议1',
                                'author': 'tester',
                                'author_email': 'tester@example.com',
                                'code_snippet': {
                                    'language': 'python',
                                    'code': 'print("test")'
                                }
                            },
                            {
                                'line': '20',
                                'type': '性能',
                                'severity': 'major',
                                'description': '测试问题2',
                                'suggestion': '测试建议2',
                                'author': 'tester',
                                'author_email': 'tester@example.com'
                            }
                        ]
                    },
                    {
                        'file_path': 'src/test2.py',
                        'issues': [
                            {
                                'line': '5',
                                'type': '代码风格',
                                'severity': 'minor',
                                'description': '测试问题3',
                                'suggestion': '测试建议3',
                                'author': 'tester2',
                                'author_email': 'tester2@example.com'
                            }
                        ]
                    }
                ]
            }
            
            # 保存数据
            review_id = storage.save_review_with_issues(review_data)
            self.assertIsNotNone(review_id, "应该返回 review_id")
            print(f"✓ 评审记录保存成功: {review_id}")
            
            # 保存 review_id 用于后续测试
            self.__class__.test_review_id = review_id
            
        except Exception as e:
            self.fail(f"保存评审数据失败: {e}")
    
    def test_04_query_review_data(self):
        """测试 4: 查询评审数据"""
        print("测试查询评审数据...")
        
        if not hasattr(self.__class__, 'test_review_id'):
            self.skipTest("需要先执行 test_03_save_review_data")
        
        try:
            storage = MySQLStorage(self.storage_config)
            review_id = self.__class__.test_review_id
            
            # 查询评审记录
            review = storage.get_review(review_id)
            self.assertIsNotNone(review, "应该能查询到评审记录")
            self.assertEqual(review['project_name'], 'test-project')
            self.assertEqual(review['total_issues'], 3)
            print(f"✓ 查询评审记录成功")
            print(f"  项目: {review['project_name']}")
            print(f"  总问题数: {review['total_issues']}")
            
            # 查询问题列表
            issues = storage.list_issues_by_review(review_id)
            self.assertEqual(len(issues), 3, "应该有 3 个问题")
            print(f"✓ 查询问题列表成功，共 {len(issues)} 个问题")
            
            # 验证问题详情
            for i, issue in enumerate(issues, 1):
                print(f"  问题 {i}: {issue['severity']} - {issue['description']}")
                self.assertIn('file_path', issue)
                self.assertIn('severity', issue)
                self.assertIn('description', issue)
            
        except Exception as e:
            self.fail(f"查询评审数据失败: {e}")
    
    def test_05_list_reviews(self):
        """测试 5: 列表查询"""
        print("测试列表查询...")
        
        try:
            storage = MySQLStorage(self.storage_config)
            
            # 查询所有评审记录
            reviews = storage.list_reviews(limit=10)
            self.assertIsInstance(reviews, list, "应该返回列表")
            print(f"✓ 查询到 {len(reviews)} 条评审记录")
            
            # 按项目查询
            reviews = storage.list_reviews(project='test-project', limit=10)
            print(f"✓ 测试项目的评审记录: {len(reviews)} 条")
            
        except Exception as e:
            self.fail(f"列表查询失败: {e}")
    
    def test_06_update_issue_status(self):
        """测试 6: 更新问题状态"""
        print("测试更新问题状态...")
        
        if not hasattr(self.__class__, 'test_review_id'):
            self.skipTest("需要先执行 test_03_save_review_data")
        
        try:
            storage = MySQLStorage(self.storage_config)
            review_id = self.__class__.test_review_id
            
            # 获取一个问题
            issues = storage.list_issues_by_review(review_id)
            if not issues:
                self.skipTest("没有问题可以更新")
            
            issue_id = issues[0]['issue_id']
            
            # 更新状态
            result = storage.update_issue_status(
                issue_id=issue_id,
                status='confirmed',
                verified_by='test_user',
                note='测试更新'
            )
            self.assertTrue(result, "更新应该成功")
            print(f"✓ 问题状态更新成功: {issue_id}")
            
            # 验证更新
            updated_issue = storage.get_issue_by_id(issue_id)
            self.assertEqual(updated_issue['status'], 'confirmed')
            self.assertEqual(updated_issue['verified_by'], 'test_user')
            print(f"✓ 状态验证成功: {updated_issue['status']}")
            
        except Exception as e:
            self.fail(f"更新问题状态失败: {e}")
    
    def test_07_statistics(self):
        """测试 7: 统计查询"""
        print("测试统计查询...")
        
        try:
            storage = MySQLStorage(self.storage_config)
            
            # 获取统计信息
            stats = storage.get_statistics(time_range=30)
            self.assertIsInstance(stats, dict, "应该返回字典")
            self.assertIn('total_reviews', stats)
            self.assertIn('total_issues', stats)
            print(f"✓ 统计查询成功")
            print(f"  总评审次数: {stats['total_reviews']}")
            print(f"  总问题数: {stats['total_issues']}")
            
            # 获取问题统计
            issue_stats = storage.get_issue_statistics(time_range=30)
            self.assertIn('total_issues', issue_stats)
            print(f"✓ 问题统计成功")
            print(f"  待处理: {issue_stats.get('pending', 0)}")
            print(f"  已确认: {issue_stats.get('confirmed', 0)}")
            
        except Exception as e:
            self.fail(f"统计查询失败: {e}")
    
    def test_08_delete_review(self):
        """测试 8: 删除评审记录"""
        print("测试删除评审记录...")
        
        if not hasattr(self.__class__, 'test_review_id'):
            self.skipTest("需要先执行 test_03_save_review_data")
        
        try:
            storage = MySQLStorage(self.storage_config)
            review_id = self.__class__.test_review_id
            
            # 删除前检查问题数量
            issues_before = storage.list_issues_by_review(review_id)
            print(f"  删除前问题数量: {len(issues_before)}")
            
            # 删除评审记录
            result = storage.delete_review(review_id)
            self.assertTrue(result, "删除应该成功")
            print(f"✓ 评审记录删除成功: {review_id}")
            
            # 验证删除
            review = storage.get_review(review_id)
            self.assertIsNone(review, "评审记录应该被删除")
            print(f"✓ 评审记录已删除")
            
            # 验证级联删除
            issues_after = storage.list_issues_by_review(review_id)
            self.assertEqual(len(issues_after), 0, "关联问题应该被级联删除")
            print(f"✓ 关联问题已级联删除")
            
        except Exception as e:
            self.fail(f"删除评审记录失败: {e}")
    
    def test_09_connection_error_handling(self):
        """测试 9: 连接错误处理"""
        print("测试连接错误处理...")
        
        # 使用错误的配置
        bad_config = {
            'connection': {
                'host': 'invalid-host',
                'port': 3306,
                'username': 'invalid',
                'password': 'invalid',
                'database': 'invalid',
                'charset': 'utf8mb4'
            }
        }
        
        # 应该抛出异常
        with self.assertRaises(Exception) as context:
            storage = MySQLStorage(bad_config)
        
        print(f"✓ 正确捕获连接错误")
        print(f"  错误类型: {type(context.exception).__name__}")


def run_tests():
    """运行测试"""
    print("\n" + "="*70)
    print("数据库连接测试")
    print("="*70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestDatabaseConnection)
    
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
