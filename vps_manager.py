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
            
            base_url = self.config.get('web_dashboard_url', 'https://berobin.github.io/vps-date')
            message += f"\n\n👉 查看详情：{base_url}"
            
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

class VPSManager:
    def __init__(self):
        self.vps_file = 'index.html'
        self.vps_data = self.load_vps_data()
        self.currencies = [
            'USD', 'EUR', 'CNY', 'CAD', 'HKD', 'JPY', 'GBP', 'AUD',
            'SGD', 'KRW', 'TWD', 'RUB', 'CHF', 'SEK', 'NOK', 'DKK',
            'THB', 'MYR', 'INR', 'BRL'
        ]
        self.currency_names = {
            'USD': '美元', 'EUR': '欧元', 'CNY': '人民币', 'CAD': '加元',
            'HKD': '港币', 'JPY': '日元', 'GBP': '英镑', 'AUD': '澳元',
            'SGD': '新加坡元', 'KRW': '韩元', 'TWD': '新台币', 'RUB': '俄罗斯卢布',
            'CHF': '瑞士法郎', 'SEK': '瑞典克朗', 'NOK': '挪威克朗', 'DKK': '丹麦克朗',
            'THB': '泰铢', 'MYR': '马来西亚林吉特', 'INR': '印度卢比', 'BRL': '巴西雷亚尔'
        }
        # Optimized billing cycles
        self.billing_cycles = {
            'Monthly': '月付',
            'Quarterly': '季度付',
            'Semi-Annually': '半年付',
            'Annually': '年付',
            'Biennially': '2年付',
            'Triennially': '3年付'
        }
        self.exchange_rates = {}
        self.notification = NotificationManager()

    def load_vps_data(self):
        try:
            with open(self.vps_file, 'r', encoding='utf-8') as f:
                content = f.read()
                start = content.find('const vpsServices = [')
                if start == -1: return []
                end = content.find('];', start) + 1
                vps_str = content[start:end].replace('const vpsServices = ', '')
                return json.loads(vps_str)
        except Exception as e:
            print(f"Load data failed: {e}")
            return []

    def save_vps_data(self):
        try:
            with open(self.vps_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            start = content.find('const vpsServices = [')
            end = content.find('];', start) + 1
            
            # Ensure new fields exist gracefully
            vps_data_to_save = []
            for vps in self.vps_data:
                # Remove old keys if new ones exist
                if 'billingCycle' in vps and 'nextDueDate' in vps:
                    vps.pop('expireDate', None)
                    vps.pop('monthlyExpireDay', None)
                vps_data_to_save.append(vps)

            new_content = (
                content[:start] + 
                'const vpsServices = ' + 
                json.dumps(vps_data_to_save, ensure_ascii=False, indent=4) +
                content[end:]
            )
            
            with open(self.vps_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print("\n保存成功！")
            
            message = "VPS信息已更新\n"
            message += f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"当前监控: {len(self.vps_data)}台服务器"
            self.send_notification(message)
            
        except Exception as e:
            print(f"\n保存失败: {e}")

    def display_currencies(self):
        print("\n可选币种:")
        print("-" * 60)
        for i, curr in enumerate(self.currencies, 1):
            name = self.currency_names.get(curr, curr)
            print(f"{i:2d}.{curr} ({name})", end="  ")
            if i % 4 == 0: print()
        if len(self.currencies) % 4 != 0: print()
        print("-" * 60)

    def select_currency(self, current_currency=None):
        self.display_currencies()
        prompt = f"\n请选择币种"
        if current_currency:
            prompt += f" (当前: {current_currency} - {self.currency_names.get(current_currency, current_currency)})"
        prompt += " (回车跳过): "
        
        try:
            curr_input = input(prompt)
            if not curr_input and current_currency: return current_currency
            if not curr_input: return None
            curr_idx = int(curr_input) - 1
            if 0 <= curr_idx < len(self.currencies):
                return self.currencies[curr_idx]
            else:
                print("无效的币种选择！")
                return None
        except ValueError:
            print("输入格式无效！")
            return None
    
    def select_billing_cycle(self, current_cycle=None):
        """Displays and handles billing cycle selection."""
        print("\n请选择计费时段:")
        cycles = list(self.billing_cycles.keys())
        for i, cycle_key in enumerate(cycles, 1):
            print(f"{i}. {self.billing_cycles[cycle_key]} ({cycle_key})")
        
        prompt = "\n请选择"
        if current_cycle:
            prompt += f" (当前: {self.billing_cycles.get(current_cycle, current_cycle)})"
        prompt += " (回车跳过): "

        try:
            choice_input = input(prompt)
            if not choice_input and current_cycle:
                return current_cycle
            if not choice_input:
                return None
            
            choice_idx = int(choice_input) - 1
            if 0 <= choice_idx < len(cycles):
                return cycles[choice_idx]
            else:
                print("无效的选择！")
                return None
        except ValueError:
            print("输入格式无效！")
            return None

    def list_vps(self):
        print("\nVPS列表:")
        print("-" * 100)
        print(f"{'#':<3}{'Name':<20}{'Cost':<15}{'Billing':<20}{'Next Due Date':<15}{'URL':<25}")
        print("-" * 100)
        for i, vps in enumerate(self.vps_data, 1):
            currency_name = self.currency_names.get(vps['currency'], vps['currency'])
            cost_info = f"{vps['cost']} {vps['currency']} ({currency_name})"
            
            # Handle both new and old data formats for display
            if 'billingCycle' in vps and 'nextDueDate' in vps:
                cycle_display = self.billing_cycles.get(vps['billingCycle'], vps['billingCycle'])
                billing_info = f"{cycle_display}"
                due_date_info = vps['nextDueDate']
            else: # Fallback for old format
                billing_info = "旧格式(请修改)"
                due_date_info = vps.get('expireDate', f"每月{vps.get('monthlyExpireDay')}日")

            print(f"{i:<3}{vps['name']:<20}{cost_info:<15}{billing_info:<20}{due_date_info:<15}{vps.get('url', ''):<25}")
        print("-" * 100)

    def edit_vps(self):
        self.list_vps()
        try:
            idx_str = input("\n请输入要修改的序号: ")
            if not idx_str.isdigit():
                print("无效的输入!")
                return
            idx = int(idx_str) - 1
            if not (0 <= idx < len(self.vps_data)):
                print("无效的序号！")
                return

            vps = self.vps_data[idx]
            print(f"\n正在修改: {vps['name']}")
            print("直接回车保持原值")
            
            changes = {}
            
            name = input(f"Name ({vps['name']}): ")
            if name: changes['name'] = name.strip()
            
            cost_str = input(f"费用 ({vps['cost']}): ")
            if cost_str:
                try:
                    changes['cost'] = float(cost_str)
                except ValueError:
                    print("费用格式无效，保持原值")
            
            new_currency = self.select_currency(vps['currency'])
            if new_currency and new_currency != vps['currency']:
                changes['currency'] = new_currency
            
            # --- New Billing Logic ---
            # Check if using old format and force update
            is_old_format = 'billingCycle' not in vps or 'nextDueDate' not in vps
            if is_old_format:
                print("\n检测到旧的日期格式，请更新为新的计费方式。")
                current_cycle = None
                current_due_date = vps.get('expireDate', 'N/A')
            else:
                current_cycle = vps.get('billingCycle')
                current_due_date = vps.get('nextDueDate')

            new_cycle = self.select_billing_cycle(current_cycle)
            if new_cycle:
                changes['billingCycle'] = new_cycle

            new_due_date_str = input(f"到期时间 (YYYY-MM-DD) ({current_due_date}): ")
            if new_due_date_str:
                try:
                    datetime.strptime(new_due_date_str, '%Y-%m-%d')
                    changes['nextDueDate'] = new_due_date_str
                except ValueError:
                    print("日期格式无效 (应为 YYYY-MM-DD)，保持原值")
            
            url = input(f"URL ({vps.get('url', '')}): ")
            if url: changes['url'] = url

            if changes:
                vps.update(changes)
                self.vps_data[idx] = vps
                self.save_vps_data()
                print("\n修改成功！")
            else:
                print("\n未做任何修改")
            
        except Exception as e:
            print(f"\n修改失败: {str(e)}")

    def add_vps(self):
        try:
            print("\n添加新VPS")
            name = input("Name: ")
            if not name:
                print("名称不能为空！"); return
            
            try:
                cost = float(input("费用: "))
            except ValueError:
                print("费用格式无效！"); return
            
            currency = self.select_currency()
            if not currency:
                print("必须选择一个币种!"); return
            
            # --- New Billing Logic ---
            billing_cycle = self.select_billing_cycle()
            if not billing_cycle:
                print("必须选择一个计费时段!"); return

            next_due_date = ""
            while not next_due_date:
                date_str = input("到期时间 (YYYY-MM-DD): ")
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    next_due_date = date_str
                except ValueError:
                    print("无效的日期格式，请重新输入！")
            
            url = input("Management URL: ")
            
            new_vps = {
                'name': name,
                'cost': cost,
                'currency': currency,
                'billingCycle': billing_cycle,
                'nextDueDate': next_due_date,
                'url': url
            }
            
            self.vps_data.append(new_vps)
            self.save_vps_data()
            print("\n添加成功！")
            
        except Exception as e:
            print(f"\n添加失败: {str(e)}")

    def delete_vps(self):
        self.list_vps()
        try:
            idx_str = input("\n请输入要删除的序号: ")
            if not idx_str.isdigit():
                print("无效的输入!")
                return
            idx = int(idx_str) - 1
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
            commit_message = f'Update VPS data: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            os.system(f'git commit -m "{commit_message}"')
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
            if choice == '1': self.notification.setup_telegram()
            elif choice == '2': self.send_test_notification()
            elif choice == '0': break
            else: print("无效的选择！")

    def send_test_notification(self):
        message = "VPS监控系统通知\n"
        message += f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        message += f"监控服务器数量: {len(self.vps_data)} 台"
        
        results = []
        if self.notification.config['telegram']['enabled']:
            self.notification.send_telegram(message)
            results.append("Telegram: 已发送")
        
        if not results: print("未启用任何通知方式！")
        else: print("\n".join(results))

    def check_expiring_vps(self):
        expiring_vps = []
        today = datetime.now()
        for vps in self.vps_data:
            # Use new 'nextDueDate' field, with fallback to 'expireDate' for old data
            due_date_str = vps.get('nextDueDate') or vps.get('expireDate')
            if not due_date_str:
                continue

            try:
                expire_date = datetime.strptime(due_date_str, '%Y-%m-%d')
                days_left = (expire_date - today).days
                if 0 < days_left <= 3:
                    expiring_vps.append(f"<b>{vps['name']}</b>: 还有 {days_left} 天到期 ({vps['nextDueDate']})")
            except ValueError:
                continue # Skip malformed dates
        
        if expiring_vps:
            message = "VPS到期提醒\n"
            message += f"当前时间: {today.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            message += "\n".join(expiring_vps)
            self.send_notification(message)

    def send_notification(self, message):
        if self.notification.config['telegram']['enabled']:
            self.notification.send_telegram(message)

    def update_exchange_rates(self):
        try:
            print("\n正在更新汇率...")
            base_currency = 'CNY'
            api_url = f"https://api.exchangerate-api.com/v4/latest/{base_currency}"
            rates_data = None
            try:
                response = requests.get(api_url, timeout=10)
                response.raise_for_status()
                rates_data = response.json()
            except Exception as e:
                print(f"API {api_url} 失败: {str(e)}")
            
            if not rates_data or 'rates' not in rates_data:
                print("API获取失败，无法更新汇率。")
                return False

            self.exchange_rates = rates_data['rates']
            
            js_content = f"// 汇率数据 - 相对于人民币(CNY) - 更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            js_content += f"const exchangeRates = {json.dumps(self.exchange_rates, indent=4, ensure_ascii=False)};\n\n"
            js_content += f"// 币种中文名称映射\n"
            js_content += f"const currencyNames = {json.dumps(self.currency_names, indent=4, ensure_ascii=False)};\n"
            
            with open('exchange_rates.js', 'w', encoding='utf-8') as f:
                f.write(js_content)
            
            print("\n当前汇率（相对于CNY）：")
            print("-" * 50)
            for i, (currency, rate) in enumerate(self.exchange_rates.items(), 1):
                if currency in self.currency_names:
                    name = self.currency_names.get(currency, currency)
                    print(f"{currency} ({name}): {rate:.4f}", end="  ")
                    if i % 2 == 0: print()
            if len(self.exchange_rates) % 2 != 0: print()
            print("-" * 50)
            
            message = "💱 汇率更新通知\n\n"
            message += f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            message += f"基准货币: CNY\n"
            message += "主要汇率：\n"
            for currency in ['USD', 'EUR', 'HKD', 'JPY', 'GBP']:
                if currency in self.exchange_rates:
                    message += f"{currency}: {self.exchange_rates[currency]:.4f}\n"
            self.send_notification(message)
            print("\n汇率更新成功！")
            return True
            
        except Exception as e:
            print(f"更新汇率失败: {str(e)}")
            return False

    def show_currency_stats(self):
        if not self.exchange_rates:
            print("\n请先运行 '7. 更新汇率' 来获取汇率数据。")
            return
        if not self.vps_data:
            print("暂无VPS数据！")
            return
        
        currency_stats = {}
        total_cost_cny = 0
        
        for vps in self.vps_data:
            currency = vps['currency']
            cost = vps['cost']
            
            if currency not in currency_stats:
                currency_stats[currency] = {'count': 0, 'total_cost': 0}
            
            currency_stats[currency]['count'] += 1
            currency_stats[currency]['total_cost'] += cost
            
            rate_to_cny = self.exchange_rates.get(currency)
            if rate_to_cny:
                total_cost_cny += cost / rate_to_cny
        
        print("\n=== 货币使用统计 ===")
        print("-" * 60)
        print(f"{'币种':<8} {'中文名':<12} {'数量':<6} {'总费用':<15} {'人民币约':<12}")
        print("-" * 60)
        
        for currency, stats in sorted(currency_stats.items()):
            name = self.currency_names.get(currency, currency)
            count = stats['count']
            total = stats['total_cost']
            
            rate_to_cny = self.exchange_rates.get(currency)
            cny_equivalent = (total / rate_to_cny) if rate_to_cny else 0
            
            print(f"{currency:<8} {name:<12} {count:<6} {total:<15.2f} {cny_equivalent:<12.2f}")
        
        print("-" * 60)
        print(f"总计: {len(self.vps_data)} 台服务器，约 {total_cost_cny:.2f} CNY")
        print("-" * 60)

    def show_menu(self):
        # Automatically check for expiring VPS on start
        self.check_expiring_vps()
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\n=== VPS到期监控 (已优化计费方式) ===")
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
            print("=" * 38)
            
            choice = input("\n请选择操作: ").strip()
            
            if choice == '1': self.list_vps()
            elif choice == '2': self.add_vps()
            elif choice == '3': self.delete_vps()
            elif choice == '4': self.edit_vps()
            elif choice == '5': self.push_to_github()
            elif choice == '6': self.notification_menu()
            elif choice == '7': self.update_exchange_rates()
            elif choice == '8': self.show_currency_stats()
            elif choice == '0': break
            else: print("无效的选择！")
            
            if choice != '0':
                input("\n按回车键继续...")

if __name__ == "__main__":
    try:
        manager = VPSManager()
        manager.show_menu()
    except Exception as e:
        print(f"\n程序出错: {e}")
        input("\n按回车键退出...")