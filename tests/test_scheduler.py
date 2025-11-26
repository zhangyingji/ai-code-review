"""
定时任务调度测试
测试 APScheduler 调度器的任务调度、执行和管理功能
"""
import sys
import os
import unittest
import time
import threading
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.schedulers.aps_scheduler import APSScheduler


class TestScheduler(unittest.TestCase):
    """调度器测试类"""
    
    def setUp(self):
        """每个测试方法前执行"""
        print(f"\n{'='*60}")
        print(f"执行测试: {self._testMethodName}")
        print(f"{'='*60}")
        self.scheduler = None
        self.task_executed = []
    
    def tearDown(self):
        """每个测试方法后执行"""
        if self.scheduler and self.scheduler.running:
            self.scheduler.stop()
    
    def task_function(self, task_id, **kwargs):
        """测试任务函数"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] 任务执行: {task_id}")
        self.task_executed.append({
            'task_id': task_id,
            'timestamp': timestamp,
            'kwargs': kwargs
        })
    
    def test_01_scheduler_initialization(self):
        """测试 1: 调度器初始化"""
        print("测试调度器初始化...")
        
        try:
            # 创建调度器
            scheduler = APSScheduler(timezone='Asia/Shanghai', max_instances=3)
            self.assertIsNotNone(scheduler, "调度器应该被创建")
            self.assertFalse(scheduler.running, "调度器初始状态应该是未运行")
            print(f"✓ 调度器创建成功")
            print(f"✓ 时区: Asia/Shanghai")
            print(f"✓ 最大实例数: 3")
            
        except Exception as e:
            self.fail(f"调度器初始化失败: {e}")
    
    def test_02_scheduler_start_stop(self):
        """测试 2: 调度器启动和停止"""
        print("测试调度器启动和停止...")
        
        try:
            scheduler = APSScheduler()
            
            # 启动调度器
            scheduler.start()
            self.assertTrue(scheduler.running, "调度器应该处于运行状态")
            print(f"✓ 调度器启动成功")
            
            # 等待一小段时间
            time.sleep(1)
            
            # 停止调度器
            scheduler.stop()
            self.assertFalse(scheduler.running, "调度器应该处于停止状态")
            print(f"✓ 调度器停止成功")
            
        except Exception as e:
            self.fail(f"调度器启动停止失败: {e}")
    
    def test_03_schedule_interval_job(self):
        """测试 3: 间隔调度"""
        print("测试间隔调度...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册一个每2秒执行的任务
            result = self.scheduler.schedule_job(
                job_id='interval_test',
                schedule_expr='interval:seconds=2',
                task_func=self.task_function,
                task_id='interval_test'
            )
            self.assertTrue(result, "任务调度应该成功")
            print(f"✓ 间隔任务注册成功")
            
            # 启动调度器
            self.scheduler.start()
            print(f"✓ 调度器已启动，等待任务执行...")
            
            # 等待任务执行
            time.sleep(5)
            
            # 验证任务执行
            self.assertGreater(len(self.task_executed), 0, "任务应该至少执行一次")
            print(f"✓ 任务执行 {len(self.task_executed)} 次")
            
        except Exception as e:
            self.fail(f"间隔调度失败: {e}")
    
    def test_04_schedule_cron_job(self):
        """测试 4: Cron 表达式调度"""
        print("测试 Cron 表达式调度...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 获取当前时间的下一分钟
            now = datetime.now()
            next_minute = (now + timedelta(minutes=1)).strftime('%M')
            
            # 注册一个每分钟执行的任务
            result = self.scheduler.schedule_job(
                job_id='cron_test',
                schedule_expr=f'{next_minute} * * * *',
                task_func=self.task_function,
                task_id='cron_test'
            )
            self.assertTrue(result, "Cron 任务调度应该成功")
            print(f"✓ Cron 任务注册成功")
            
            # 获取任务状态
            status = self.scheduler.get_job_status('cron_test')
            self.assertIsNotNone(status, "应该能获取任务状态")
            print(f"✓ 下次执行时间: {status.get('next_run_time')}")
            
        except Exception as e:
            self.fail(f"Cron 调度失败: {e}")
    
    def test_05_schedule_daily_job(self):
        """测试 5: 每日调度"""
        print("测试每日调度...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册一个每天特定时间执行的任务
            result = self.scheduler.schedule_job(
                job_id='daily_test',
                schedule_expr='daily:10:00',
                task_func=self.task_function,
                task_id='daily_test'
            )
            self.assertTrue(result, "每日任务调度应该成功")
            print(f"✓ 每日任务注册成功")
            
            # 获取任务状态
            status = self.scheduler.get_job_status('daily_test')
            self.assertIsNotNone(status, "应该能获取任务状态")
            print(f"✓ 下次执行时间: {status.get('next_run_time')}")
            
        except Exception as e:
            self.fail(f"每日调度失败: {e}")
    
    def test_06_schedule_weekly_job(self):
        """测试 6: 每周调度"""
        print("测试每周调度...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册一个每周一执行的任务
            result = self.scheduler.schedule_job(
                job_id='weekly_test',
                schedule_expr='weekly:MON:09:00',
                task_func=self.task_function,
                task_id='weekly_test'
            )
            self.assertTrue(result, "每周任务调度应该成功")
            print(f"✓ 每周任务注册成功")
            
            # 获取任务状态
            status = self.scheduler.get_job_status('weekly_test')
            self.assertIsNotNone(status, "应该能获取任务状态")
            print(f"✓ 下次执行时间: {status.get('next_run_time')}")
            
        except Exception as e:
            self.fail(f"每周调度失败: {e}")
    
    def test_07_list_jobs(self):
        """测试 7: 任务列表查询"""
        print("测试任务列表查询...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册多个任务
            self.scheduler.schedule_job(
                job_id='job1',
                schedule_expr='interval:minutes=5',
                task_func=self.task_function,
                task_id='job1'
            )
            self.scheduler.schedule_job(
                job_id='job2',
                schedule_expr='daily:10:00',
                task_func=self.task_function,
                task_id='job2'
            )
            
            # 查询任务列表
            jobs = self.scheduler.list_jobs()
            self.assertEqual(len(jobs), 2, "应该有 2 个任务")
            print(f"✓ 查询到 {len(jobs)} 个任务")
            
            for job_id, job_info in jobs.items():
                print(f"  - {job_id}: 下次执行 {job_info.get('next_run_time')}")
            
        except Exception as e:
            self.fail(f"任务列表查询失败: {e}")
    
    def test_08_cancel_job(self):
        """测试 8: 取消任务"""
        print("测试取消任务...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册任务
            self.scheduler.schedule_job(
                job_id='cancel_test',
                schedule_expr='interval:seconds=10',
                task_func=self.task_function,
                task_id='cancel_test'
            )
            print(f"✓ 任务注册成功")
            
            # 取消任务
            result = self.scheduler.cancel_job('cancel_test')
            self.assertTrue(result, "任务取消应该成功")
            print(f"✓ 任务取消成功")
            
            # 验证任务已取消
            status = self.scheduler.get_job_status('cancel_test')
            self.assertIsNone(status, "已取消的任务应该查询不到")
            print(f"✓ 任务已从调度器移除")
            
        except Exception as e:
            self.fail(f"取消任务失败: {e}")
    
    def test_09_multiple_jobs(self):
        """测试 9: 多任务调度"""
        print("测试多任务调度...")
        
        try:
            self.scheduler = APSScheduler(max_instances=3)
            
            # 注册多个任务
            for i in range(5):
                self.scheduler.schedule_job(
                    job_id=f'multi_job_{i}',
                    schedule_expr='interval:seconds=3',
                    task_func=self.task_function,
                    task_id=f'multi_job_{i}'
                )
            
            print(f"✓ 注册 5 个任务")
            
            # 启动调度器
            self.scheduler.start()
            
            # 等待任务执行
            time.sleep(8)
            
            # 验证任务执行
            executed_jobs = set([t['task_id'] for t in self.task_executed])
            print(f"✓ 执行了 {len(executed_jobs)} 个不同的任务")
            print(f"✓ 总共执行 {len(self.task_executed)} 次")
            
        except Exception as e:
            self.fail(f"多任务调度失败: {e}")
    
    def test_10_task_with_params(self):
        """测试 10: 带参数的任务"""
        print("测试带参数的任务...")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册带参数的任务
            self.scheduler.schedule_job(
                job_id='param_test',
                schedule_expr='interval:seconds=2',
                task_func=self.task_function,
                task_id='param_test',
                param1='value1',
                param2=123
            )
            
            # 启动调度器
            self.scheduler.start()
            
            # 等待任务执行
            time.sleep(3)
            
            # 验证参数传递
            self.assertGreater(len(self.task_executed), 0, "任务应该执行")
            task_info = self.task_executed[0]
            self.assertIn('kwargs', task_info)
            self.assertEqual(task_info['kwargs'].get('param1'), 'value1')
            self.assertEqual(task_info['kwargs'].get('param2'), 123)
            print(f"✓ 任务参数传递正确")
            print(f"  param1: {task_info['kwargs'].get('param1')}")
            print(f"  param2: {task_info['kwargs'].get('param2')}")
            
        except Exception as e:
            self.fail(f"带参数任务失败: {e}")
    
    def test_11_task_exception_handling(self):
        """测试 11: 任务异常处理"""
        print("测试任务异常处理...")
        
        def failing_task():
            """会抛出异常的任务"""
            raise ValueError("测试异常")
        
        try:
            self.scheduler = APSScheduler()
            
            # 注册会失败的任务
            self.scheduler.schedule_job(
                job_id='failing_task',
                schedule_expr='interval:seconds=2',
                task_func=failing_task
            )
            
            # 注册正常任务
            self.scheduler.schedule_job(
                job_id='normal_task',
                schedule_expr='interval:seconds=2',
                task_func=self.task_function,
                task_id='normal_task'
            )
            
            # 启动调度器
            self.scheduler.start()
            print(f"✓ 调度器启动，包含一个会失败的任务")
            
            # 等待任务执行
            time.sleep(5)
            
            # 验证调度器仍在运行
            self.assertTrue(self.scheduler.running, "调度器应该仍在运行")
            print(f"✓ 调度器在任务失败后仍然运行")
            
            # 验证正常任务仍在执行
            self.assertGreater(len(self.task_executed), 0, "正常任务应该执行")
            print(f"✓ 正常任务不受失败任务影响")
            
        except Exception as e:
            self.fail(f"异常处理测试失败: {e}")


def run_tests():
    """运行测试"""
    print("\n" + "="*70)
    print("定时任务调度测试")
    print("="*70)
    
    # 创建测试套件
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestScheduler)
    
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
