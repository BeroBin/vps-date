// 汇率数据 - 相对于人民币(CNY) - 更新时间: 2025-06-19 19:18:40
const exchangeRates = {
    "CNY": 1.0,
    "USD": 0.139,
    "EUR": 0.121,
    "CAD": 0.19,
    "HKD": 1.09,
    "JPY": 20.16,
    "GBP": 0.103,
    "AUD": 0.214,
    "SGD": 0.179,
    "KRW": 191.21,
    "TWD": 4.11,
    "RUB": 10.92,
    "CHF": 0.114,
    "SEK": 1.34,
    "NOK": 1.39,
    "DKK": 0.903,
    "THB": 4.54,
    "MYR": 0.591,
    "INR": 12.02,
    "BRL": 0.764
};

// 币种中文名称映射
const currencyNames = {
    "USD": "美元",
    "EUR": "欧元",
    "CNY": "人民币",
    "CAD": "加元",
    "HKD": "港币",
    "JPY": "日元",
    "GBP": "英镑",
    "AUD": "澳元",
    "SGD": "新加坡元",
    "KRW": "韩元",
    "TWD": "新台币",
    "RUB": "俄罗斯卢布",
    "CHF": "瑞士法郎",
    "SEK": "瑞典克朗",
    "NOK": "挪威克朗",
    "DKK": "丹麦克朗",
    "THB": "泰铢",
    "MYR": "马来西亚林吉特",
    "INR": "印度卢比",
    "BRL": "巴西雷亚尔"
};

// 格式化货币显示
function formatCurrency(amount, currency) {
    const name = currencyNames[currency] || currency;
    return `${amount} ${currency} (${name})`;
}
