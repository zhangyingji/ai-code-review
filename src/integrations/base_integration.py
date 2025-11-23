"""集成接口 - 对接外部系统（Gerrit、GitLab等）"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BaseIntegration(ABC):
    """集成基类
    
    用于对接外部代码审查或版本控制系统
    如Gerrit、GitLab、GitHub等
    """
    
    def __init__(self, server_url: str, auth_token: str = None):
        """初始化集成
        
        Args:
            server_url: 服务器地址
            auth_token: 认证令牌
        """
        self.server_url = server_url
        self.auth_token = auth_token
        self.logger = logger
    
    @abstractmethod
    def get_merge_request(self, project_id: str, mr_id: str) -> Optional[Dict[str, Any]]:
        """获取合并请求信息
        
        Args:
            project_id: 项目ID
            mr_id: 合并请求ID
            
        Returns:
            合并请求详细信息
        """
        pass
    
    @abstractmethod
    def get_changes(self, project_id: str, mr_id: str) -> List[Dict[str, Any]]:
        """获取变更文件列表
        
        Args:
            project_id: 项目ID
            mr_id: 合并请求ID
            
        Returns:
            变更文件列表
        """
        pass
    
    @abstractmethod
    def post_comment(self, project_id: str, mr_id: str, comment: str,
                    file_path: str = None, line: int = None) -> bool:
        """发布评论
        
        Args:
            project_id: 项目ID
            mr_id: 合并请求ID
            comment: 评论内容
            file_path: 文件路径（可选，用于行内评论）
            line: 行号（可选，用于行内评论）
            
        Returns:
            是否发布成功
        """
        pass
    
    @abstractmethod
    def set_review_status(self, project_id: str, mr_id: str,
                         status: str, message: str = None) -> bool:
        """设置评审状态
        
        Args:
            project_id: 项目ID
            mr_id: 合并请求ID
            status: 状态（如 approved, rejected, needs_work）
            message: 状态消息
            
        Returns:
            是否设置成功
        """
        pass


class GerritIntegration(BaseIntegration):
    """Gerrit集成（示例）
    
    用于对接Gerrit代码审查系统
    """
    
    def __init__(self, server_url: str, username: str, password: str):
        """初始化Gerrit集成
        
        Args:
            server_url: Gerrit服务器地址
            username: 用户名
            password: 密码或HTTP密码
        """
        super().__init__(server_url)
        self.username = username
        self.password = password
        # TODO: 初始化Gerrit客户端
    
    def get_merge_request(self, project_id: str, change_id: str) -> Optional[Dict[str, Any]]:
        """获取Gerrit Change信息
        
        Args:
            project_id: 项目名称
            change_id: Change ID
        """
        # TODO: 实现Gerrit API调用
        self.logger.info(f"获取Gerrit Change: {project_id}/{change_id}")
        raise NotImplementedError("需要实现Gerrit API调用")
    
    def get_changes(self, project_id: str, change_id: str) -> List[Dict[str, Any]]:
        """获取Gerrit Change的文件变更"""
        # TODO: 实现Gerrit文件变更获取
        raise NotImplementedError("需要实现Gerrit文件变更获取")
    
    def post_comment(self, project_id: str, change_id: str, comment: str,
                    file_path: str = None, line: int = None) -> bool:
        """在Gerrit上发布评论
        
        支持全局评论和行内评论
        """
        # TODO: 实现Gerrit评论发布
        self.logger.info(f"发布Gerrit评论: {project_id}/{change_id}")
        raise NotImplementedError("需要实现Gerrit评论发布")
    
    def set_review_status(self, project_id: str, change_id: str,
                         status: str, message: str = None) -> bool:
        """设置Gerrit评审状态
        
        Args:
            status: +1, +2, -1, -2 等
        """
        # TODO: 实现Gerrit评审状态设置
        self.logger.info(f"设置Gerrit评审状态: {project_id}/{change_id} -> {status}")
        raise NotImplementedError("需要实现Gerrit评审状态设置")


class GitLabIntegration(BaseIntegration):
    """GitLab集成（示例）
    
    用于增强现有的GitLab对接功能
    """
    
    def __init__(self, server_url: str, private_token: str):
        """初始化GitLab集成
        
        Args:
            server_url: GitLab服务器地址
            private_token: 私有令牌
        """
        super().__init__(server_url, private_token)
        # 可以复用现有的 gitlab_client.py
    
    def get_merge_request(self, project_id: str, mr_id: str) -> Optional[Dict[str, Any]]:
        """获取GitLab MR信息"""
        # TODO: 实现或调用现有GitLab客户端
        raise NotImplementedError("可复用现有 gitlab_client.py 实现")
    
    def get_changes(self, project_id: str, mr_id: str) -> List[Dict[str, Any]]:
        """获取GitLab MR变更"""
        raise NotImplementedError("可复用现有 gitlab_client.py 实现")
    
    def post_comment(self, project_id: str, mr_id: str, comment: str,
                    file_path: str = None, line: int = None) -> bool:
        """在GitLab MR上发布评论"""
        raise NotImplementedError("可复用现有 gitlab_client.py 实现")
    
    def set_review_status(self, project_id: str, mr_id: str,
                         status: str, message: str = None) -> bool:
        """设置GitLab MR状态"""
        raise NotImplementedError("可复用现有 gitlab_client.py 实现")


# 使用示例:
# gerrit = GerritIntegration("https://gerrit.example.com", "user", "pass")
# change_info = gerrit.get_merge_request("my-project", "12345")
# gerrit.post_comment("my-project", "12345", "发现严重问题", "src/main.py", 42)
# gerrit.set_review_status("my-project", "12345", "-1", "需要修复安全问题")
