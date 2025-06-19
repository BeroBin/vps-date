import json
import os
import requests
import hmac
import hashlib
import base64
import urllib.parse
import time
from datetime import datetime

class NotificationManager:
    def __init__(self):
        self.config_file = 'config.json'
        self.config = self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_file):
            default_config = {
                "telegram": {"enabled": False, "bot_token": "", "chat_id": ""}
            }
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=4)
            return default_config
        
        with open(self.config_file, 'r') as f:
            return json.load(f)

    def save_config(self):
        with open(self.config_file, 'w') as f:
            json.dump(self.config, f, indent=4)

    def setup_telegram(self):
        print("\n=== Telegram配置 ===")
        enabled = input("启用Telegram通知? (y/n): ").lower() == 'y'
        self.config['telegram']['enabled'] = enabled
        
        if enabled:
            self.config['telegram']['bot_token'] = input("Bot Token: ")
            self.config['telegram']['chat_id'] = input("Chat ID: ")
        self.save_config()
        print("Telegram配置已保存！")

    def send_telegram(self, message):
        """发送Telegram通知"""
        try:
            if not self.config['telegram']['enabled']:
                return
                
            bot_token = self.config['telegram']['bot_token']
            chat_id = self.config['telegram']['chat_id']
            
            # 添加详情链接到消息末尾
            base_url = self.config.get('web_dashboard_url', 'https://berobin.github.io/vps-date')
            message += f"\n\n👉 查看详情：{base_url}"
            
            # 发送消息到Telegram
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            
            response = requests.post(url, json=data)
            response.raise_for_status()
            
        except Exception as e:
            print(f"发送Telegram通知失败: {str(e)}")


from datetime import datetime, timedelta

# 在 VPSManager 中添加或替换以下方法

def get_billing_period_input():
    billing_periods = {
        '1': ('monthly', 30),
        '2': ('quarterly', 90),
        '3': ('semiannual', 182),
        '4': ('annual', 365),
        '5': ('biennial', 730),
        '6': ('triennial', 1095),
    }
    print("\n计费周期：")
    print("1. 月付\n2. 季付\n3. 半年付\n4. 年付\n5. 2年付\n6. 3年付")
    choice = input("请选择计费周期: ").strip()
    return billing_periods.get(choice, (None, None))

def add_vps(self):
    try:
        print("\n添加新VPS")
        name = input("Name: ")
        if not name:
            print("名称不能为空！")
            return

        try:
            cost = float(input("费用: "))
        except ValueError:
            print("费用格式无效！")
            return

        currency = self.select_currency()
        if not currency:
            return

        billing_type, days = get_billing_period_input()
        if not billing_type:
            print("计费周期无效！")
            return

        start_date_str = input("开始日期 (YYYY-MM-DD): ")
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            expire_date = start_date + timedelta(days=days)
        except ValueError:
            print("开始日期格式错误！")
            return

        url = input("Management URL: ")

        new_vps = {
            'name': name,
            'cost': cost,
            'currency': currency,
            'billingPeriod': billing_type,
            'startDate': start_date_str,
            'expireDate': expire_date.strftime('%Y-%m-%d'),
            'url': url
        }

        self.vps_data.append(new_vps)
        self.save_vps_data()
        print("\nAdded successfully!")

    except Exception as e:
        print(f"\nAdd failed: {str(e)}")

def list_vps(self):
    print("\nVPS列表:")
    print("-" * 80)
    for i, vps in enumerate(self.vps_data, 1):
        if 'billingPeriod' in vps:
            expire_info = f"{vps['billingPeriod']}付 - 到期: {vps['expireDate']}"
        else:
            expire_info = vps.get('expireDate', f"每月{vps.get('monthlyExpireDay')}号续费")
        currency_name = self.currency_names.get(vps['currency'], vps['currency'])
        print(f"{i:2d}. {vps['name']:<20} - {vps['cost']:>8} {vps['currency']} ({currency_name}) - {expire_info}")
    print("-" * 80)

def edit_vps(self):
    self.list_vps()
    try:
        idx = int(input("\n请输入要修改的序号: ")) - 1
        if not (0 <= idx < len(self.vps_data)):
            print("无效的序号！")
            return

        vps = self.vps_data[idx]
        print(f"\n正在修改: {vps['name']}")
        print("\n直接回车保持原值")

        changes = {}

        name = input(f"Name ({vps['name']}): ")
        if name:
            changes['name'] = name.strip()

        cost_str = input(f"费用 ({vps['cost']}): ")
        if cost_str:
            try:
                changes['cost'] = float(cost_str)
            except ValueError:
                print("费用格式无效，保持原值")

        new_currency = self.select_currency(vps['currency'])
        if new_currency and new_currency != vps['currency']:
            changes['currency'] = new_currency

        billing_type, days = get_billing_period_input()
        if billing_type:
            start_date_str = input(f"开始日期 ({vps.get('startDate', 'YYYY-MM-DD')}): ")
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                expire_date = start_date + timedelta(days=days)
                changes['billingPeriod'] = billing_type
                changes['startDate'] = start_date_str
                changes['expireDate'] = expire_date.strftime('%Y-%m-%d')
            except ValueError:
                print("日期格式错误，略过更新")

        url = input(f"URL ({vps['url']}): ")
        if url:
            changes['url'] = url

        if changes:
            vps.update(changes)
            self.vps_data[idx] = vps
            self.save_vps_data()
            print("\nUpdated successfully!")
        else:
            print("\nNo changes made")

    except Exception as e:
        print(f"\nEdit failed: {str(e)}")


class VPSManager:
    def __init__(self):
        self.vps_file = 'index.html'
        self.vps_data = self.load_vps_data()
        # 扩展币种列表，包含更多常用货币
        self.currencies = [
            'USD',  # 美元
            'EUR',  # 欧元
            'CNY',  # 人民币
            'CAD',  # 加元
            'HKD',  # 港币
            'JPY',  # 日元
            'GBP',  # 英镑
            'AUD',  # 澳元
            'SGD',  # 新加坡元
            'KRW',  # 韩元
            'TWD',  # 新台币
            'RUB',  # 俄罗斯卢布
            'CHF',  # 瑞士法郎
            'SEK',  # 瑞典克朗
            'NOK',  # 挪威克朗
            'DKK',  # 丹麦克朗
            'THB',  # 泰铢
            'MYR',  # 马来西亚林吉特
            'INR',  # 印度卢比
            'BRL',  # 巴西雷亚尔
        ]
        # 币种中文名称映射
        self.currency_names = {
            'USD': '美元', 'EUR': '欧元', 'CNY': '人民币', 'CAD': '加元',
            'HKD': '港币', 'JPY': '日元', 'GBP': '英镑', 'AUD': '澳元',
            'SGD': '新加坡元', 'KRW': '韩元', 'TWD': '新台币', 'RUB': '俄罗斯卢布',
            'CHF': '瑞士法郎', 'SEK': '瑞典克朗', 'NOK': '挪威克朗', 'DKK': '丹麦克朗',
            'THB': '泰铢', 'MYR': '马来西亚林吉特', 'INR': '印度卢比', 'BRL': '巴西雷亚尔'
        }
        self.exchange_rates = {}  # 添加汇率存储
        self.notification = NotificationManager()

    def load_vps_data(self):
        try:
            with open(self.vps_file, 'r') as f:
                content = f.read()
                start = content.find('const vpsServices = [')
                end = content.find('];', start) + 1
                vps_str = content[start:end].replace('const vpsServices = ', '')
                return json.loads(vps_str)
        except Exception as e:
            print(f"Load data failed: {e}")
            return []

    def save_vps_data(self):
        try:
            with open(self.vps_file, 'r') as f:
                content = f.read()
            
            start = content.find('const vpsServices = [')
            end = content.find('];', start) + 1
            new_content = (
                content[:start] + 
                'const vpsServices = ' + 
                json.dumps(self.vps_data, ensure_ascii=False, indent=4) +
                content[end:]
            )
            
            with open(self.vps_file, 'w') as f:
                f.write(new_content)
            print("\n保存成功！")
            
            # 添加变更通知
            message = "VPS信息已更新\n"
            message += f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"当前监控: {len(self.vps_data)}台服务器"
            self.send_notification(message)
            
        except Exception as e:
            print(f"\n保存失败: {e}")

    def display_currencies(self):
        """分页显示货币选择"""
        print("\n可选币种:")
        print("-" * 60)
        for i, curr in enumerate(self.currencies, 1):
            name = self.currency_names.get(curr, curr)
            print(f"{i:2d}.{curr} ({name})", end="  ")
            if i % 4 == 0:  # 每行显示4个
                print()
        if len(self.currencies) % 4 != 0:
            print()
        print("-" * 60)

    def select_currency(self, current_currency=None):
        """选择货币的通用函数"""
        self.display_currencies()
        
        prompt = f"\n请选择币种"
        if current_currency:
            prompt += f" (当前: {current_currency} - {self.currency_names.get(current_currency, current_currency)})"
        prompt += ": "
        
        try:
            curr_input = input(prompt)
            if not curr_input and current_currency:
                return current_currency  # 保持原值
            
            curr_idx = int(curr_input) - 1
            if 0 <= curr_idx < len(self.currencies):
                return self.currencies[curr_idx]
            else:
                print("无效的币种选择！")
                return None
        except ValueError:
            print("输入格式无效！")
            return None

    def list_vps(self):
        print("\nVPS列表:")
        print("-" * 80)
        for i, vps in enumerate(self.vps_data, 1):
            expire_info = vps.get('expireDate', f"每月{vps.get('monthlyExpireDay')}号续费")
            currency_name = self.currency_names.get(vps['currency'], vps['currency'])
            print(f"{i:2d}. {vps['name']:<20} - {vps['cost']:>8} {vps['currency']} ({currency_name}) - 到期: {expire_info}")
        print("-" * 80)

    def edit_vps(self):
        self.list_vps()
        try:
            idx = int(input("\n请输入要修改的序号: ")) - 1
            if not (0 <= idx < len(self.vps_data)):
                print("无效的序号！")
                return

            vps = self.vps_data[idx]
            print(f"\n正在修改: {vps['name']}")
            print("\n直接回车保持原值")
            
            # Record changes
            changes = {}
            
            # Basic info (use English for VPS name)
            name = input(f"Name ({vps['name']}): ")
            if name:
                changes['name'] = name.strip()
            
            cost_str = input(f"费用 ({vps['cost']}): ")
            if cost_str:
                try:
                    changes['cost'] = float(cost_str)
                except ValueError:
                    print("费用格式无效，保持原值")
            
            # Currency selection
            new_currency = self.select_currency(vps['currency'])
            if new_currency and new_currency != vps['currency']:
                changes['currency'] = new_currency
            
            # Expiry date
            if 'expireDate' in vps:
                date = input(f"Expiry date ({vps['expireDate']}): ")
                if date:
                    try:
                        datetime.strptime(date, '%Y-%m-%d')
                        changes['expireDate'] = date
                    except ValueError:
                        print("Invalid date format")
            else:
                day_str = input(f"Monthly renewal day ({vps['monthlyExpireDay']}): ")
                if day_str:
                    try:
                        day = int(day_str)
                        if 1 <= day <= 31:
                            changes['monthlyExpireDay'] = day
                        else:
                            print("Day must be between 1-31")
                    except ValueError:
                        print("Invalid day format")
            
            # URL
            url = input(f"URL ({vps['url']}): ")
            if url:
                changes['url'] = url

            # Apply changes if any
            if changes:
                new_vps = vps.copy()
                new_vps.update(changes)
                self.vps_data[idx] = new_vps
                self.save_vps_data()
                print("\nUpdated successfully!")
            else:
                print("\nNo changes made")
            
        except Exception as e:
            print(f"\nEdit failed: {str(e)}")

    def add_vps(self):
        try:
            print("\n添加新VPS")
            name = input("Name: ")  # 使用英文提示VPS名称
            if not name:
                print("名称不能为空！")
                return
            
            try:
                cost = float(input("费用: "))
            except ValueError:
                print("费用格式无效！")
                return
            
            # Currency selection
            currency = self.select_currency()
            if not currency:
                return
            
            # Expiry info
            expire_type = input("\nExpiry type (1:Fixed date 2:Monthly): ")
            if expire_type == '1':
                date = input("Expiry date (YYYY-MM-DD): ")
                try:
                    datetime.strptime(date, '%Y-%m-%d')
                    expire_info = {'expireDate': date}
                except ValueError:
                    print("Invalid date format!")
                    return
            elif expire_type == '2':
                try:
                    day = int(input("Monthly renewal day (1-31): "))
                    if not (1 <= day <= 31):
                        print("Day must be between 1-31!")
                        return
                    expire_info = {'monthlyExpireDay': day}
                except ValueError:
                    print("Invalid day format!")
                    return
            else:
                print("Invalid selection!")
                return
            
            url = input("Management URL: ")
            
            # Create new VPS data
            new_vps = {
                'name': name,
                'cost': cost,
                'currency': currency,
                'url': url,
                **expire_info
            }
            
            self.vps_data.append(new_vps)
            self.save_vps_data()
            print("\nAdded successfully!")
            
        except Exception as e:
            print(f"\nAdd failed: {str(e)}")

    def delete_vps(self):
        self.list_vps()
        try:
            idx = int(input("\n请输入要删除的序号: ")) - 1
            if 0 <= idx < len(self.vps_data):
                vps = self.vps_data.pop(idx)
                print(f"\n已删除: {vps['name']}")
                self.save_vps_data()
            else:
                print("无效的序号！")
        except Exception as e:
            print(f"\n删除失败: {str(e)}")

    def push_to_github(self):
        try:
            os.system('git add .')
            os.system(f'git commit -m "Update VPS data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"')
            os.system('git push')
            print("\n推送成功！")
        except Exception as e:
            print(f"\n推送失败: {str(e)}")

    def notification_menu(self):
        while True:
            print("\n=== 通知设置 ===")
            print("1. 配置Telegram通知")
            print("2. 发送测试通知")
            print("0. 返回主菜单")
            
            choice = input("\n请选择操作: ")
            
            if choice == '1':
                self.notification.setup_telegram()
            elif choice == '2':
                self.send_test_notification()
            elif choice == '0':
                break
            else:
                print("无效的选择！")

    def send_test_notification(self):
        message = "VPS监控系统通知\n"
        message += f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"监控服务器数量: {len(self.vps_data)} 台"
        
        results = []
        if self.notification.config['telegram']['enabled']:
            self.notification.send_telegram(message)
            results.append("Telegram: 已发送")
        
        if not results:
            print("未启用任何通知方式！")
        else:
            print("\n".join(results))

    def check_expiring_vps(self):
        """检查即将到期的VPS"""
        expiring_vps = []
        for vps in self.vps_data:
            if 'expireDate' in vps:
                expire_date = datetime.strptime(vps['expireDate'], '%Y-%m-%d')
                days_left = (expire_date - datetime.now()).days
                if 0 < days_left <= 3:
                    expiring_vps.append(f"{vps['name']}: 还有{days_left}天到期")
        
        if expiring_vps:
            message = "VPS到期提醒\n"
            message += f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += "\n".join(expiring_vps)
            self.send_notification(message)

    def send_notification(self, message):
        """统一的通知发送函数"""
        if self.notification.config['telegram']['enabled']:
            self.notification.send_telegram(message)

    def update_exchange_rates(self):
        """更新汇率信息 - 支持更多币种"""
        try:
            print("\n正在更新汇率...")
            
            # 使用免费的汇率API，支持更多币种
            base_currency = 'CNY'  # 使用人民币作为基准货币
            
            # 尝试多个API源
            api_urls = [
                f"https://api.exchangerate-api.com/v4/latest/{base_currency}",
                f"https://open.er-api.com/v6/latest/{base_currency}",
                f"https://api.fixer.io/latest?base={base_currency}"
            ]
            
            rates_data = None
            for api_url in api_urls:
                try:
                    response = requests.get(api_url, timeout=10)
                    response.raise_for_status()
                    rates_data = response.json()
                    if 'rates' in rates_data:
                        break
                except Exception as e:
                    print(f"API {api_url} 失败: {str(e)}")
                    continue
            
            if not rates_data or 'rates' not in rates_data:
                # 如果API都失败，使用默认汇率
                print("API获取失败，使用默认汇率...")
                self.exchange_rates = {
                    'CNY': 1.0,      # 基准货币
                    'USD': 0.14,     # 美元
                    'EUR': 0.13,     # 欧元
                    'CAD': 0.19,     # 加元
                    'HKD': 1.09,     # 港币
                    'JPY': 21.0,     # 日元
                    'GBP': 0.11,     # 英镑
                    'AUD': 0.21,     # 澳元
                    'SGD': 0.19,     # 新加坡元
                    'KRW': 182.0,    # 韩元
                    'TWD': 4.5,      # 新台币
                    'RUB': 13.0,     # 俄罗斯卢布
                    'CHF': 0.13,     # 瑞士法郎
                    'SEK': 1.48,     # 瑞典克朗
                    'NOK': 1.48,     # 挪威克朗
                    'DKK': 0.97,     # 丹麦克朗
                    'THB': 4.9,      # 泰铢
                    'MYR': 0.64,     # 马来西亚林吉特
                    'INR': 12.0,     # 印度卢比
                    'BRL': 0.77,     # 巴西雷亚尔
                }
            else:
                # 成功获取汇率数据
                self.exchange_rates = {'CNY': 1.0}  # 基准货币
                
                for currency in self.currencies:
                    if currency != 'CNY':
                        if currency in rates_data['rates']:
                            self.exchange_rates[currency] = rates_data['rates'][currency]
                        else:
                            # 如果某个币种不存在，设置默认值
                            default_rates = {
                                'USD': 0.14, 'EUR': 0.13, 'CAD': 0.19, 'HKD': 1.09,
                                'JPY': 21.0, 'GBP': 0.11, 'AUD': 0.21, 'SGD': 0.19,
                                'KRW': 182.0, 'TWD': 4.5, 'RUB': 13.0, 'CHF': 0.13,
                                'SEK': 1.48, 'NOK': 1.48, 'DKK': 0.97, 'THB': 4.9,
                                'MYR': 0.64, 'INR': 12.0, 'BRL': 0.77
                            }
                            self.exchange_rates[currency] = default_rates.get(currency, 1.0)
            
            # 保存汇率到JS文件
            js_content = f"""// 汇率数据 - 相对于人民币(CNY) - 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
const exchangeRates = {json.dumps(self.exchange_rates, indent=4, ensure_ascii=False)};

// 币种中文名称映射
const currencyNames = {json.dumps(self.currency_names, indent=4, ensure_ascii=False)};

// 格式化货币显示
function formatCurrency(amount, currency) {{
    const name = currencyNames[currency] || currency;
    return `${{amount}} ${{currency}} (${{name}})`;
}}
"""
            
            with open('exchange_rates.js', 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            # 显示更新后的汇率
            print("\n当前汇率（相对于CNY）：")
            print("-" * 50)
            for i, (currency, rate) in enumerate(self.exchange_rates.items(), 1):
                name = self.currency_names.get(currency, currency)
                print(f"{currency} ({name}): {rate:.4f}", end="  ")
                if i % 2 == 0:  # 每行显示2个
                    print()
            if len(self.exchange_rates) % 2 != 0:
                print()
            print("-" * 50)
            
            # 发送通知
            message = "💱 汇率更新通知\n\n"
            message += f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"支持币种: {len(self.exchange_rates)} 种\n"
            message += "主要汇率（相对于CNY）：\n"
            major_currencies = ['USD', 'EUR', 'HKD', 'JPY', 'GBP']
            for currency in major_currencies:
                if currency in self.exchange_rates:
                    rate = self.exchange_rates[currency]
                    name = self.currency_names.get(currency, currency)
                    message += f"{currency}({name}): {rate:.4f}\n"
            
            self.send_notification(message)
            
            print("\n汇率更新成功！")
            return True
            
        except Exception as e:
            error_msg = f"更新汇率失败: {str(e)}"
            print(error_msg)
            return False

    def show_currency_stats(self):
        """显示货币统计信息"""
        if not self.vps_data:
            print("暂无VPS数据！")
            return
        
        # 统计各币种的使用情况
        currency_stats = {}
        total_cost_cny = 0
        
        for vps in self.vps_data:
            currency = vps['currency']
            cost = vps['cost']
            
            if currency not in currency_stats:
                currency_stats[currency] = {'count': 0, 'total_cost': 0}
            
            currency_stats[currency]['count'] += 1
            currency_stats[currency]['total_cost'] += cost
            
            # 转换为人民币计算总成本
            if currency in self.exchange_rates:
                if currency == 'CNY':
                    total_cost_cny += cost
                else:
                    total_cost_cny += cost / self.exchange_rates[currency]
        
        print("\n=== 货币使用统计 ===")
        print("-" * 60)
        print(f"{'币种':<8} {'中文名':<12} {'数量':<6} {'总费用':<15} {'人民币约':<12}")
        print("-" * 60)
        
        for currency, stats in sorted(currency_stats.items()):
            name = self.currency_names.get(currency, currency)
            count = stats['count']
            total = stats['total_cost']
            
            # 计算人民币等值
            if currency == 'CNY':
                cny_equivalent = total
            elif currency in self.exchange_rates:
                cny_equivalent = total / self.exchange_rates[currency]
            else:
                cny_equivalent = 0
            
            print(f"{currency:<8} {name:<12} {count:<6} {total:<15.2f} {cny_equivalent:<12.2f}")
        
        print("-" * 60)
        print(f"总计: {len(self.vps_data)} 台服务器，约 {total_cost_cny:.2f} CNY")
        print("-" * 60)

    def show_menu(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n=== VPS到期监控 (支持20种货币) ===")
            print()
            print("1. 查看VPS列表")
            print("2. 添加VPS")
            print("3. 删除VPS")
            print("4. 修改VPS")
            print("5. 推送到GitHub")
            print("6. 通知设置")
            print("7. 更新汇率")
            print("8. 货币统计")
            print("0. 退出")
            print()
            print("=" * 35)
            
            choice = input("\n请选择操作: ").strip()
            
            if choice == '1':
                self.list_vps()
            elif choice == '2':
                self.add_vps()
            elif choice == '3':
                self.delete_vps()
            elif choice == '4':
                self.edit_vps()
            elif choice == '5':
                self.push_to_github()
            elif choice == '6':
                self.notification_menu()
            elif choice == '7':
                self.update_exchange_rates()
            elif choice == '8':
                self.show_currency_stats()
            elif choice == '0':
                break
            else:
                print("无效的选择！")
            
            if choice != '0':
                input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        manager = VPSManager()
        manager.show_menu()
    except Exception as e:
        print(f"\n程序出错: {e}")
        input("\n按回车键退出...")