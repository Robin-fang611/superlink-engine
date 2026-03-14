#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统状态检查和诊断模块
用于监控SuperLink Data Engine的各个组件是否正常运行
"""

import os
import sys
import socket
import time
import logging
import requests
from datetime import datetime

# 添加项目根目录到Python搜索路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=os.getenv('LOG_FILE', 'output/superlink.log')
)
logger = logging.getLogger('Diagnostics')


class SystemDiagnostics:
    """系统诊断类"""
    
    def __init__(self):
        """初始化诊断工具"""
        self.api_status = {}
        self.network_status = {}
        self.email_status = {}
        self.database_status = {}
        self.system_status = {}
    
    def check_api_keys(self):
        """检查API密钥状态"""
        logger.info("开始检查API密钥状态")
        
        api_keys = {
            'SERPER_API_KEY': 'Serper搜索API',
            'ZHIPUAI_API_KEY': '智谱AI API',
            'APOLLO_API_KEY': 'Apollo.io API',
            'SNOVIO_USER_ID': 'Snov.io User ID',
            'SNOVIO_API_SECRET': 'Snov.io API Secret'
        }
        
        for key, name in api_keys.items():
            value = os.getenv(key)
            if value:
                self.api_status[key] = {
                    'status': 'valid',
                    'message': f'{name} 已配置',
                    'length': len(value)
                }
                logger.info(f'{name} 已配置')
            else:
                self.api_status[key] = {
                    'status': 'missing',
                    'message': f'{name} 未配置',
                    'length': 0
                }
                logger.warning(f'{name} 未配置')
        
        return self.api_status
    
    def check_network(self):
        """检查网络连接状态"""
        logger.info("开始检查网络连接状态")
        
        # 测试DNS解析
        try:
            socket.gethostbyname('google.com')
            dns_status = 'ok'
            dns_message = 'DNS解析正常'
            logger.info('DNS解析正常')
        except Exception as e:
            dns_status = 'error'
            dns_message = f'DNS解析失败: {str(e)}'
            logger.warning(f'DNS解析失败: {str(e)}')
        
        # 测试HTTP连接
        try:
            response = requests.get('https://www.google.com', timeout=5)
            if response.status_code == 200:
                http_status = 'ok'
                http_message = 'HTTP连接正常'
                logger.info('HTTP连接正常')
            else:
                http_status = 'error'
                http_message = f'HTTP连接失败，状态码: {response.status_code}'
                logger.warning(f'HTTP连接失败，状态码: {response.status_code}')
        except Exception as e:
            http_status = 'error'
            http_message = f'HTTP连接失败: {str(e)}'
            logger.warning(f'HTTP连接失败: {str(e)}')
        
        # 测试代理设置
        use_proxy = os.getenv('USE_PROXY', 'False').lower() == 'true'
        proxy_status = 'disabled'
        proxy_message = '代理未启用'
        
        if use_proxy:
            http_proxy = os.getenv('HTTP_PROXY')
            https_proxy = os.getenv('HTTPS_PROXY')
            
            if http_proxy or https_proxy:
                proxy_status = 'configured'
                proxy_message = f'代理已配置: HTTP={http_proxy}, HTTPS={https_proxy}'
                logger.info(f'代理已配置: HTTP={http_proxy}, HTTPS={https_proxy}')
            else:
                proxy_status = 'error'
                proxy_message = '代理已启用但未配置'
                logger.warning('代理已启用但未配置')
        
        self.network_status = {
            'dns': {
                'status': dns_status,
                'message': dns_message
            },
            'http': {
                'status': http_status,
                'message': http_message
            },
            'proxy': {
                'status': proxy_status,
                'message': proxy_message
            }
        }
        
        return self.network_status
    
    def check_email_services(self):
        """检查邮件服务状态"""
        logger.info("开始检查邮件服务状态")
        
        # 检查SMTP配置
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT', '587')
        sender_email = os.getenv('SENDER_EMAIL')
        sender_password = os.getenv('SENDER_PASSWORD')
        
        smtp_configured = all([smtp_server, sender_email, sender_password])
        
        # 测试SMTP连接
        smtp_status = 'error'
        smtp_message = 'SMTP未配置'
        
        if smtp_configured:
            try:
                import smtplib
                server = smtplib.SMTP(smtp_server, int(smtp_port), timeout=10)
                server.ehlo()
                server.starttls()
                server.login(sender_email, sender_password)
                server.quit()
                smtp_status = 'ok'
                smtp_message = 'SMTP连接正常'
                logger.info('SMTP连接正常')
            except Exception as e:
                smtp_status = 'error'
                smtp_message = f'SMTP连接失败: {str(e)}'
                logger.warning(f'SMTP连接失败: {str(e)}')
        
        # 检查IMAP配置
        imap_server = os.getenv('IMAP_SERVER')
        imap_port = os.getenv('IMAP_PORT', '993')
        
        imap_configured = all([imap_server, sender_email, sender_password])
        
        # 测试IMAP连接
        imap_status = 'error'
        imap_message = 'IMAP未配置'
        
        if imap_configured:
            try:
                import imaplib
                mail = imaplib.IMAP4_SSL(imap_server, int(imap_port))
                mail.login(sender_email, sender_password)
                mail.logout()
                imap_status = 'ok'
                imap_message = 'IMAP连接正常'
                logger.info('IMAP连接正常')
            except Exception as e:
                imap_status = 'error'
                imap_message = f'IMAP连接失败: {str(e)}'
                logger.warning(f'IMAP连接失败: {str(e)}')
        
        self.email_status = {
            'smtp': {
                'status': smtp_status,
                'message': smtp_message,
                'configured': smtp_configured
            },
            'imap': {
                'status': imap_status,
                'message': imap_message,
                'configured': imap_configured
            }
        }
        
        return self.email_status
    
    def check_database(self):
        """检查数据库状态"""
        logger.info("开始检查数据库状态")
        
        try:
            from core.database import DatabaseHandler
            
            # 确保output目录存在
            os.makedirs('output', exist_ok=True)
            
            # 初始化数据库
            db = DatabaseHandler()
            
            # 测试连接
            with db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 测试表结构
                tables = ['verified_leads', 'email_send_records', 'feedback_records']
                table_status = {}
                
                for table in tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}';")
                    result = cursor.fetchone()
                    if result:
                        table_status[table] = 'exists'
                    else:
                        table_status[table] = 'missing'
                
                # 测试数据查询
                cursor.execute("SELECT COUNT(*) FROM verified_leads;")
                lead_count = cursor.fetchone()[0]
                
                self.database_status = {
                    'status': 'ok',
                    'message': '数据库连接正常',
                    'tables': table_status,
                    'lead_count': lead_count
                }
                
                logger.info('数据库连接正常')
                logger.info(f'数据库表状态: {table_status}')
                logger.info(f'线索数量: {lead_count}')
                
        except Exception as e:
            self.database_status = {
                'status': 'error',
                'message': f'数据库连接失败: {str(e)}',
                'tables': {},
                'lead_count': 0
            }
            logger.warning(f'数据库连接失败: {str(e)}')
        
        return self.database_status
    
    def check_system_resources(self):
        """检查系统资源使用情况"""
        logger.info("开始检查系统资源使用情况")
        
        # 检查磁盘空间
        try:
            import psutil
            disk_usage = psutil.disk_usage('.')
            disk_free_gb = disk_usage.free / (1024 ** 3)
            disk_total_gb = disk_usage.total / (1024 ** 3)
            disk_percent = disk_usage.percent
            
            if disk_percent > 90:
                disk_status = 'warning'
                disk_message = f'磁盘空间不足: {disk_free_gb:.2f}GB 可用'
                logger.warning(f'磁盘空间不足: {disk_free_gb:.2f}GB 可用')
            else:
                disk_status = 'ok'
                disk_message = f'磁盘空间正常: {disk_free_gb:.2f}GB / {disk_total_gb:.2f}GB'
                logger.info(f'磁盘空间正常: {disk_free_gb:.2f}GB / {disk_total_gb:.2f}GB')
        except ImportError:
            disk_status = 'unknown'
            disk_message = '无法检查磁盘空间 (psutil 未安装)'
            logger.warning('无法检查磁盘空间 (psutil 未安装)')
        except Exception as e:
            disk_status = 'error'
            disk_message = f'检查磁盘空间失败: {str(e)}'
            logger.warning(f'检查磁盘空间失败: {str(e)}')
        
        # 检查内存使用
        try:
            import psutil
            memory = psutil.virtual_memory()
            memory_free_gb = memory.available / (1024 ** 3)
            memory_total_gb = memory.total / (1024 ** 3)
            memory_percent = memory.percent
            
            if memory_percent > 80:
                memory_status = 'warning'
                memory_message = f'内存使用过高: {memory_free_gb:.2f}GB 可用'
                logger.warning(f'内存使用过高: {memory_free_gb:.2f}GB 可用')
            else:
                memory_status = 'ok'
                memory_message = f'内存使用正常: {memory_free_gb:.2f}GB / {memory_total_gb:.2f}GB'
                logger.info(f'内存使用正常: {memory_free_gb:.2f}GB / {memory_total_gb:.2f}GB')
        except ImportError:
            memory_status = 'unknown'
            memory_message = '无法检查内存使用 (psutil 未安装)'
            logger.warning('无法检查内存使用 (psutil 未安装)')
        except Exception as e:
            memory_status = 'error'
            memory_message = f'检查内存使用失败: {str(e)}'
            logger.warning(f'检查内存使用失败: {str(e)}')
        
        # 检查Python版本
        python_version = sys.version
        python_status = 'ok'
        python_message = f'Python版本: {python_version}'
        logger.info(f'Python版本: {python_version}')
        
        self.system_status = {
            'disk': {
                'status': disk_status,
                'message': disk_message
            },
            'memory': {
                'status': memory_status,
                'message': memory_message
            },
            'python': {
                'status': python_status,
                'message': python_message
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return self.system_status
    
    def run_full_diagnostics(self):
        """运行完整的系统诊断"""
        logger.info("开始运行完整的系统诊断")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'api_keys': self.check_api_keys(),
            'network': self.check_network(),
            'email_services': self.check_email_services(),
            'database': self.check_database(),
            'system_resources': self.check_system_resources()
        }
        
        logger.info("系统诊断完成")
        return results
    
    def generate_report(self):
        """生成诊断报告"""
        results = self.run_full_diagnostics()
        
        report = """
=======================================================================
                        SuperLink Data Engine 系统诊断报告
=======================================================================
时间: {timestamp}

-----------------------------------------------------------------------
1. API密钥状态
-----------------------------------------------------------------------
{api_report}

-----------------------------------------------------------------------
2. 网络连接状态
-----------------------------------------------------------------------
{network_report}

-----------------------------------------------------------------------
3. 邮件服务状态
-----------------------------------------------------------------------
{email_report}

-----------------------------------------------------------------------
4. 数据库状态
-----------------------------------------------------------------------
{database_report}

-----------------------------------------------------------------------
5. 系统资源状态
-----------------------------------------------------------------------
{system_report}

=======================================================================
                        诊断报告结束
=======================================================================
""".format(
            timestamp=results['timestamp'],
            api_report=self._format_api_report(results['api_keys']),
            network_report=self._format_network_report(results['network']),
            email_report=self._format_email_report(results['email_services']),
            database_report=self._format_database_report(results['database']),
            system_report=self._format_system_report(results['system_resources'])
        )
        
        # 保存报告到文件
        report_file = f"output/diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"诊断报告已保存到: {report_file}")
        return report, report_file
    
    def _format_api_report(self, api_status):
        """格式化API报告"""
        report = []
        for key, info in api_status.items():
            status_icon = '✓' if info['status'] == 'valid' else '✗'
            report.append(f"{status_icon} {key}: {info['message']} (长度: {info['length']})")
        return '\n'.join(report)
    
    def _format_network_report(self, network_status):
        """格式化网络报告"""
        report = []
        for service, info in network_status.items():
            status_icon = '✓' if info['status'] == 'ok' else '✗'
            report.append(f"{status_icon} {service.upper()}: {info['message']}")
        return '\n'.join(report)
    
    def _format_email_report(self, email_status):
        """格式化邮件报告"""
        report = []
        for service, info in email_status.items():
            status_icon = '✓' if info['status'] == 'ok' else '✗'
            report.append(f"{status_icon} {service.upper()}: {info['message']} (已配置: {info['configured']})")
        return '\n'.join(report)
    
    def _format_database_report(self, database_status):
        """格式化数据库报告"""
        report = []
        status_icon = '✓' if database_status['status'] == 'ok' else '✗'
        report.append(f"{status_icon} 连接状态: {database_status['message']}")
        report.append(f"线索数量: {database_status['lead_count']}")
        report.append("表结构状态:")
        for table, status in database_status['tables'].items():
            table_icon = '✓' if status == 'exists' else '✗'
            report.append(f"  {table_icon} {table}: {status}")
        return '\n'.join(report)
    
    def _format_system_report(self, system_status):
        """格式化系统报告"""
        report = []
        for resource, info in system_status.items():
            if resource == 'timestamp':
                continue
            status_icon = '✓' if info['status'] == 'ok' else '⚠' if info['status'] == 'warning' else '✗'
            report.append(f"{status_icon} {resource.upper()}: {info['message']}")
        return '\n'.join(report)


if __name__ == '__main__':
    """运行诊断工具"""
    print("开始运行SuperLink Data Engine系统诊断...\n")
    
    diagnostics = SystemDiagnostics()
    report, report_file = diagnostics.generate_report()
    
    print(report)
    print(f"诊断报告已保存到: {report_file}")
    print("\n诊断完成！")
