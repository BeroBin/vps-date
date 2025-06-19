import json
import os
import logging
from datetime import datetime
import requests
from vps_manager import VPSManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='vps_monitor.log'
)

def check_vps_expiry():
    """检查VPS到期情况并发送通知"""
    try:
        manager = VPSManager()
        expiring_vps = []
        monthly_vps = []

        # 检查所有VPS
        for vps in manager.vps_data:
            if 'expireDate' in vps:
                expire_date = datetime.strptime(vps['expireDate'], '%Y-%m-%d')
                days_left = (expire_date - datetime.now()).days
                if 0 < days_left <= 3:
                    expiring_vps.append(f"• {vps['name']}: {days_left}天后到期 ({vps['expireDate']})")
            elif 'monthlyExpireDay' in vps:
                today = datetime.now()
                expire_day = vps['monthlyExpireDay']
                days_until_expire = expire_day - today.day
                
                next_month = today.replace(day=1)
                if today.day >= expire_day:
                    next_month = next_month.replace(month=today.month + 1)
                next_pay_date = next_month.replace(day=expire_day)
                
                if days_until_expire <= 3 and days_until_expire > 0:
                    monthly_vps.append(f"• {vps['name']}: {days_until_expire}天后续费 ({next_pay_date.strftime('%Y-%m-%d')})")
                elif days_until_expire <= 0:
                    days_until_expire = expire_day
                    monthly_vps.append(f"• {vps['name']}: {days_until_expire}天后续费 ({next_pay_date.strftime('%Y-%m-%d')})")

        # 如果有即将到期的VPS，发送通知
        if expiring_vps or monthly_vps:
            message = "⚠️ VPS到期提醒\n"
            
            if expiring_vps:
                message += "\n" + "\n".join(expiring_vps)
            
            if monthly_vps:
                if expiring_vps:
                    message += "\n"
                message += "\n" + "\n".join(monthly_vps)
            
            # 发送Telegram通知
            if manager.notification.config['telegram']['enabled']:
                manager.notification.send_telegram(message)
                print("已发送到期提醒通知")
                logging.info("已发送到期提醒通知")
        else:
            print("没有即将到期的VPS")
            logging.info("没有即将到期的VPS")

    except Exception as e:
        error_msg = f"检查过程出错: {str(e)}"
        print(error_msg)
        logging.error(error_msg)

if __name__ == "__main__":
    check_vps_expiry() 