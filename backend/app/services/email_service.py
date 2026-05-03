import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """邮件通知服务"""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.from_email = settings.FROM_EMAIL
        self.enabled = all([self.smtp_server, self.smtp_username, self.smtp_password])
    
    def send_inquiry_notification(self, inquiry_data: dict) -> bool:
        """发送询盘通知邮件给管理员"""
        if not self.enabled:
            logger.warning("邮件服务未配置，跳过通知")
            return False
        
        subject = f"【新询盘】{inquiry_data.get('name', '未知')} - {inquiry_data.get('product', '无产品')}"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; color: white;">
                <h1 style="margin: 0;">新询盘通知</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">优丁建材官网收到新的客户询盘</p>
            </div>
            
            <div style="padding: 30px; background: #f9f9f9;">
                <h2 style="color: #333; margin-top: 0;">客户信息</h2>
                <table style="width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden;">
                    <tr style="background: #f5f5f5;">
                        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold; width: 120px;">姓名</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{inquiry_data.get('name', '未知')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold;">电话</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;"><a href="tel:{inquiry_data.get('phone', '')}" style="color: #667eea; text-decoration: none;">{inquiry_data.get('phone', '未知')}</a></td>
                    </tr>
                    <tr style="background: #f5f5f5;">
                        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold;">邮箱</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{inquiry_data.get('email', '未提供')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 12px; border-bottom: 1px solid #eee; font-weight: bold;">产品需求</td>
                        <td style="padding: 12px; border-bottom: 1px solid #eee;">{inquiry_data.get('product', '未指定')}</td>
                    </tr>
                </table>
                
                <h2 style="color: #333; margin-top: 30px;">留言内容</h2>
                <div style="background: white; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea;">
                    <p style="margin: 0; line-height: 1.6; color: #555;">{inquiry_data.get('message', '无')}</p>
                </div>
            </div>
            
            <div style="padding: 20px 30px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee;">
                <p>此邮件由优丁建材官网自动发送，请勿直接回复</p>
                <p>请登录 <a href="{settings.FRONTEND_URL}/admin/inquiries" style="color: #667eea;">管理后台</a> 查看和处理询盘</p>
            </div>
        </html>
        """
        
        return self._send_email(
            to_email=self.smtp_username,
            subject=subject,
            html_content=html_content
        )
    
    def send_inquiry_confirmation(self, inquiry_data: dict) -> bool:
        """发送询盘确认邮件给客户"""
        if not self.enabled or not inquiry_data.get('email'):
            return False
        
        subject = "感谢您的咨询 - 优丁建材"
        
        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; color: white;">
                <h1 style="margin: 0;">感谢您的咨询</h1>
                <p style="margin: 10px 0 0 0; opacity: 0.9;">优丁建材已收到您的询盘</p>
            </div>
            
            <div style="padding: 30px;">
                <p style="color: #555; line-height: 1.8;">尊敬的 {inquiry_data.get('name', '客户')}：</p>
                <p style="color: #555; line-height: 1.8;">
                    感谢您对优丁建材的关注！我们已收到您的询盘，专业客服团队将在工作时间24小时内与您联系。
                </p>
                
                <div style="background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #333; margin-top: 0;">您的询盘信息</h3>
                    <p style="margin: 5px 0;"><strong>产品需求：</strong>{inquiry_data.get('product', '未指定')}</p>
                    <p style="margin: 5px 0;"><strong>留言内容：</strong>{inquiry_data.get('message', '无')}</p>
                </div>
                
                <p style="color: #555; line-height: 1.8;">
                    如有紧急需求，您也可以直接拨打我们的咨询热线：<strong>400-888-8888</strong>
                </p>
            </div>
            
            <div style="padding: 20px 30px; text-align: center; color: #999; font-size: 12px; border-top: 1px solid #eee;">
                <p>优丁建材有限公司 | 专业保温材料供应商</p>
                <p>此邮件由系统自动发送，请勿直接回复</p>
            </div>
        </html>
        """
        
        return self._send_email(
            to_email=inquiry_data['email'],
            subject=subject,
            html_content=html_content
        )
    
    def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """发送邮件的底层实现"""
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.from_email or self.smtp_username
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"邮件发送成功: {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {to_email}, 错误: {str(e)}")
            return False


email_service = EmailService()
