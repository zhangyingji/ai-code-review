"""CSS样式定义"""


def get_css_styles() -> str:
    """获取CSS样式
    
    Returns:
        CSS样式字符串
    """
    return """<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; line-height: 1.6; color: #24292e; background-color: #f6f8fa; padding: 20px; }
    .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    h1 { color: #0366d6; margin-bottom: 20px; padding-bottom: 10px; border-bottom: 3px solid #0366d6; }
    h2 { color: #24292e; margin-top: 30px; margin-bottom: 15px; padding-bottom: 8px; border-bottom: 1px solid #e1e4e8; }
    
    /* 元数据 */
    .metadata { background: #f6f8fa; padding: 15px; border-radius: 6px; margin-bottom: 20px; }
    .metadata-item { display: inline-block; margin-right: 30px; margin-bottom: 10px; }
    .metadata-label { font-weight: 600; color: #586069; }
    
    /* 仪表盘 */
    .dashboard { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; }
    .dashboard h2 { color: white; border-bottom: 2px solid rgba(255,255,255,0.3); margin-top: 0; }
    .dashboard-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px; margin-top: 20px; }
    .dashboard-item { text-align: center; padding: 15px; background: rgba(255,255,255,0.1); border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }
    .dashboard-item:hover { background: rgba(255,255,255,0.15); transform: translateY(-2px); }
    .dashboard-item.active { box-shadow: 0 4px 12px rgba(3, 102, 214, 0.3); border-color: rgba(255, 255, 255, 0.5); }
    .dashboard-item-label { font-size: 0.9em; opacity: 0.9; margin-bottom: 8px; }
    .dashboard-item-value { font-size: 2em; font-weight: bold; }
    
    /* 问题卡片 */
    .issues-list { margin-top: 20px; }
    .problem-card { background: #fff; border: 1px solid #e1e4e8; border-radius: 6px; padding: 15px; margin-bottom: 15px; display: none; }
    .problem-card.show { display: block; }
    
    .problem-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-bottom: 12px; border-bottom: 1px solid #e1e4e8; }
    .problem-author { color: #586069; font-size: 0.9em; flex-shrink: 0; margin-left: 15px; }
    
    .problem-location { background: #f6f8fa; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-size: 0.9em; }
    .problem-location div { margin-bottom: 5px; line-height: 1.5; }
    .problem-location div:last-child { margin-bottom: 0; }
    
    .problem-description { margin-bottom: 10px; line-height: 1.6; }
    .problem-suggestion { background: #f0f7ff; border-left: 4px solid #0366d6; padding: 10px; border-radius: 4px; margin-bottom: 10px; font-size: 0.9em; }
    
    /* 严重程度标签 */
    .severity-badge { display: inline-block; padding: 3px 8px; border-radius: 12px; font-size: 0.85em; font-weight: 600; color: white; margin-right: 8px; }
    .badge-critical { background-color: #d73a4a; }
    .badge-major { background-color: #e36209; }
    .badge-minor { background-color: #fbca04; color: #333; }
    .badge-suggestion { background-color: #0366d6; }
    
    /* 代码段落 */
    .code-snippet { background: #f6f8fa; border: 1px solid #d1d5da; border-radius: 6px; margin: 10px 0; font-family: 'Courier New', monospace; font-size: 0.85em; overflow-x: auto; }
    .code-snippet-header { background: #f3f3f3; padding: 8px 12px; border-bottom: 1px solid #d1d5da; font-weight: 600; color: #24292e; cursor: pointer; user-select: none; display: flex; justify-content: space-between; align-items: center; }
    .code-snippet-header:hover { background: #e8e8e8; }
    .code-snippet-toggle { display: inline-block; width: 20px; height: 20px; text-align: center; transition: transform 0.3s ease; }
    .code-snippet-toggle.collapsed { transform: rotate(-90deg); }
    .code-snippet-content { max-height: 400px; overflow-y: auto; transition: max-height 0.3s ease; }
    .code-snippet-content.collapsed { max-height: 0; overflow: hidden; }
    .code-line { display: flex; padding: 2px 0; line-height: 1.5; }
    .code-line-num { width: 50px; text-align: right; padding-right: 12px; color: #586069; background: #f6f8fa; user-select: none; border-right: 1px solid #d1d5da; flex-shrink: 0; }
    .code-line-content { flex: 1; padding: 0 12px; white-space: pre-wrap; word-wrap: break-word; color: #24292e; }
    .code-line.added { background: #f0f9ff; }
    .code-line.added .code-line-num { background: #cce5ff; }
    .code-line.added .code-line-content { color: #0366d6; }
    .code-line.deleted { background: #fef2f2; }
    .code-line.deleted .code-line-num { background: #ffd7d7; }
    .code-line.deleted .code-line-content { color: #cb2431; }
    .code-line.in-range { background-color: #fff3cd !important; }
    .code-line.in-range .code-line-num { background-color: #ffe5a1 !important; }
    
    footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e1e4e8; text-align: center; color: #586069; font-size: 0.9em; }
    
    /* 维度视图 */
    .dimension-view { display: none; }
    .dimension-view.active { display: block; }
    
    /* 维度选项卡 */
    .dimension-tab { cursor: pointer; }
    .dimension-tab.active { box-shadow: 0 4px 12px rgba(3, 102, 214, 0.3); border-color: rgba(255, 255, 255, 0.5); }
    
    /* 严重程度筛选仪表盘 */
    .severity-filter-dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 15px; margin-bottom: 20px; }
    .filter-item { text-align: center; padding: 12px; background: #f6f8fa; border-radius: 6px; cursor: pointer; border: 2px solid transparent; transition: all 0.3s; }
    .filter-item:hover { background: #e1e4e8; }
    .filter-label { font-size: 0.9em; color: #586069; margin-bottom: 6px; }
    .filter-value { font-size: 1.8em; font-weight: bold; }
    
    /* 文件分组 */
    .file-group { margin-bottom: 30px; }
    .file-group-title { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 15px; border-radius: 6px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
    .file-stats { font-size: 0.85em; opacity: 0.9; }
    
    /* 作者分组 */
    .author-group { margin-bottom: 30px; }
    .author-group-title { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 15px; border-radius: 6px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }
    .author-stats { font-size: 0.85em; opacity: 0.9; }
    
    /* 严重程度分组 */
    .severity-group { margin-bottom: 30px; }
    .severity-group-title { background: #f6f8fa; padding: 12px 15px; border-radius: 6px; margin-bottom: 15px; display: flex; align-items: center; gap: 12px; border-left: 4px solid #e1e4e8; }
    
    /* 问题容器 */
    .issues-container { margin-top: 20px; }
</style>"""
