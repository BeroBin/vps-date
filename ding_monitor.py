import time
import logging
import json
import hmac
import hashlib
import base64
import urllib.parse
from datetime import datetime
import requests
import re

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='vps_monitor.log'
)

# 配置
VPS_PAGE_URL = "https://woniu336.github.io/vps-date/"  # 替换为你的实际URL
DINGTALK_WEBHOOK = ""
DINGTALK_SECRET = ""

def calculate_days_until_expire(service):
    """计算距离到期还有多少天"""
    today = datetime.now()
    
    if 'expireDate' in service:
        # 处理具体到期日期
        expire_date = datetime.strptime(service['expireDate'], '%Y-%m-%d')
        days_left = (expire_date - today).days
    elif 'monthlyExpireDay' in service:
        # 处理每月重复日期
        expire_day = service['monthlyExpireDay']
        next_expire = datetime(today.year, today.month, expire_day)
        
        if today.day > expire_day:
            if today.month == 12:
                next_expire = datetime(today.year + 1, 1, expire_day)
            else:
                next_expire = datetime(today.year, today.month + 1, expire_day)
        
        days_left = (next_expire - today).days
    else:
        return None
    
    return days_left

def sign_dingtalk_webhook():
    """为钉钉消息签名"""
    timestamp = str(round(time.time() * 1000))
    secret_enc = DINGTALK_SECRET.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, DINGTALK_SECRET)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return f"{DINGTALK_WEBHOOK}&timestamp={timestamp}&sign={sign}"

def send_dingtalk_alert(expiring_services):
    """发送钉钉警报"""
    if not expiring_services:
        return
    
    message = "# VPS服务到期提醒\n\n"
    message += "> 以下服务即将在2天内到期，请注意续费！\n\n"
    
    for service in expiring_services:
        message += "---\n"  # 添加分隔线
        message += f"### {service['name']}\n"
        message += f"💰 费用：`{service['cost']} {service['currency']}`\n"
        message += f"⏰ 剩余：<font color='red'>{service['days_left']}天</font>\n\n"
    
    message += "\n> 💡 请及时处理，以免服务中断\n\n"
    message += f"---\n[查看详情]({VPS_PAGE_URL})"  # 添加链接
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": "VPS到期提醒",
            "text": message
        }
    }
    
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        'Accept': 'application/json'
    }
    webhook_url = sign_dingtalk_webhook()
    
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        response = requests.post(webhook_url, headers=headers, data=json_data.encode('utf-8'))
        if response.status_code == 200:
            logging.info("钉钉警报发送成功")
            print("钉钉警报发送成功")
        else:
            error_msg = f"钉钉警报发送失败: {response.text}"
            logging.error(error_msg)
            print(error_msg)
    except Exception as e:
        error_msg = f"发送钉钉警报时发生错误: {str(e)}"
        logging.error(error_msg)
        print(error_msg)

def get_html_content():
    """获取HTML内容"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Charset': 'UTF-8'
        }
        response = requests.get(VPS_PAGE_URL, headers=headers)
        response.encoding = 'utf-8'
        content = response.text
        print("✓ 成功获取页面内容")
        return content
    except requests.exceptions.RequestException as e:
        error_msg = f"获取页面内容失败: {str(e)}"
        logging.error(error_msg)
        print(f"✗ {error_msg}")
        return None

def extract_vps_services(html_content):
    """从HTML文件中提取VPS服务配置"""
    try:
        pattern = r'const\s+vpsServices\s*=\s*(\[\s*{[\s\S]*?\}\s*\]);'
        match = re.search(pattern, html_content)
        
        if not match:
            logging.error("HTML内容中未找到VPS服务配置")
            print("✗ HTML内容中未找到VPS服务配置")
            print("HTML内容预览:", html_content[:200])
            return []
        
        js_array = match.group(1)
        
        # 1. 移除注释行
        py_array = re.sub(r'//.*?\n', '\n', js_array)
        
        # 2. 处理单引号为双引号
        py_array = py_array.replace("'", '"')
        
        # 3. 处理没有引号的属性名
        py_array = re.sub(r'([{,]\s*)(\w+):', r'\1"\2":', py_array)
        
        # 4. 分割并处理每个对象
        # 使用更精确的正则表达式来分割对象
        objects = re.findall(r'{[^{]*?}(?=\s*[,\]])', py_array)
        processed_objects = []
        
        for obj in objects:
            # 创建一个新的字典来存储清理后的数据
            try:
                # 移除URL字段和其他不需要的字段
                obj_dict = {}
                # 提取必要的字段
                name_match = re.search(r'"name"\s*:\s*"([^"]+)"', obj)
                cost_match = re.search(r'"cost"\s*:\s*([0-9.]+)', obj)
                currency_match = re.search(r'"currency"\s*:\s*"([^"]+)"', obj)
                color_match = re.search(r'"color"\s*:\s*"([^"]+)"', obj)
                
                # 检查过期日期
                expire_date_match = re.search(r'"expireDate"\s*:\s*"([^"]+)"', obj)
                monthly_expire_match = re.search(r'"monthlyExpireDay"\s*:\s*([0-9]+)', obj)
                
                if name_match and cost_match and currency_match:
                    obj_dict["name"] = name_match.group(1)
                    obj_dict["cost"] = float(cost_match.group(1))
                    obj_dict["currency"] = currency_match.group(1)
                    if color_match:
                        obj_dict["color"] = color_match.group(1)
                    if expire_date_match:
                        obj_dict["expireDate"] = expire_date_match.group(1)
                    if monthly_expire_match:
                        obj_dict["monthlyExpireDay"] = int(monthly_expire_match.group(1))
                    
                    processed_objects.append(obj_dict)
            except Exception as e:
                print(f"处理对象时出错: {str(e)}, 跳过此对象")
                continue
        
        # 5. 转换为JSON字符串
        py_array = json.dumps(processed_objects, ensure_ascii=False)
        
        try:
            services = json.loads(py_array)
            print(f"✓ 成功读取 {len(services)} 个VPS配置")
            return services
        except json.JSONDecodeError as je:
            logging.error(f"JSON解析错误: {str(je)}")
            print(f"✗ JSON解析错误: {str(je)}")
            print(f"错误位置: 行 {je.lineno}, 列 {je.colno}")
            print(f"具体字符: {je.doc[max(0, je.pos-20):je.pos+20]}")
            return []
            
    except Exception as e:
        error_msg = f"配置读取失败: {str(e)}"
        logging.error(error_msg)
        print(f"✗ {error_msg}")
        return []

def check_vps_expiration():
    """检查VPS到期情况"""
    try:
        html_content = get_html_content()
        if not html_content:
            return
        
        services = extract_vps_services(html_content)
        expiring_services = []
        
        for service in services:
            days_left = calculate_days_until_expire(service)
            if days_left is not None and days_left <= 2:
                service['days_left'] = days_left
                expiring_services.append(service)
                print(f"⚠️ {service['name']} 将在 {days_left} 天后到期")
        
        if expiring_services:
            send_dingtalk_alert(expiring_services)
        else:
            print("✓ 所有服务运行正常")
            
    except Exception as e:
        error_msg = f"检查失败: {str(e)}"
        logging.error(error_msg)
        print(f"✗ {error_msg}")

def main():
    """主函数"""
    print("VPS监控服务已启动")
    logging.info("VPS监控服务启动")
    
    while True:
        try:
            check_vps_expiration()
            print("\n>>> 等待6小时后进行下一次检查...\n")
            time.sleep(6 * 60 * 60)
        except Exception as e:
            error_msg = f"运行时错误: {str(e)}"
            logging.error(error_msg)
            print(f"✗ {error_msg}")
            print(">>> 5分钟后重试...")
            time.sleep(300)

if __name__ == "__main__":
    main() 