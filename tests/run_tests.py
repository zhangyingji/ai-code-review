"""
测试运行器
统一运行所有测试套件
"""
import sys
import os
import argparse
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_all_tests():
    """运行所有测试"""
    print("="*70)
    print("代码评审系统 - 测试套件")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    results = {}
    
    # 1. 数据库连接测试
    print("\n" + ">"*70)
    print(">>> 第一部分: 数据库连接测试")
    print(">"*70)
    try:
        from tests.test_database_connection import run_tests as run_db_tests
        results['database'] = run_db_tests()
    except Exception as e:
        print(f"数据库测试运行失败: {e}")
        results['database'] = False
    
    # 2. 定时任务调度测试
    print("\n" + ">"*70)
    print(">>> 第二部分: 定时任务调度测试")
    print(">"*70)
    try:
        from tests.test_scheduler import run_tests as run_scheduler_tests
        results['scheduler'] = run_scheduler_tests()
    except Exception as e:
        print(f"调度器测试运行失败: {e}")
        results['scheduler'] = False
    
    # 3. 功能集成测试
    print("\n" + ">"*70)
    print(">>> 第三部分: 功能集成测试")
    print(">"*70)
    try:
        from tests.test_integration import run_tests as run_integration_tests
        results['integration'] = run_integration_tests()
    except Exception as e:
        print(f"集成测试运行失败: {e}")
        results['integration'] = False
    
    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)
    print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-"*70)
    
    for test_name, success in results.items():
        status = "✓ 通过" if success else "✗ 失败"
        print(f"{test_name.ljust(20)}: {status}")
    
    print("="*70)
    
    # 返回是否所有测试都通过
    return all(results.values())


def run_specific_test(test_name):
    """运行特定测试"""
    print("="*70)
    print(f"运行测试: {test_name}")
    print("="*70)
    
    if test_name == 'database':
        from tests.test_database_connection import run_tests
        return run_tests()
    elif test_name == 'scheduler':
        from tests.test_scheduler import run_tests
        return run_tests()
    elif test_name == 'integration':
        from tests.test_integration import run_tests
        return run_tests()
    else:
        print(f"未知的测试名称: {test_name}")
        print("可用测试: database, scheduler, integration")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='代码评审系统测试运行器')
    parser.add_argument('test', nargs='?', choices=['all', 'database', 'scheduler', 'integration'],
                       default='all', help='要运行的测试 (默认: all)')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    try:
        if args.test == 'all':
            success = run_all_tests()
        else:
            success = run_specific_test(args.test)
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n测试运行出错: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
