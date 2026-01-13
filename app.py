import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="足彩14场分析助手", layout="wide")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://datachart.500.com/"
    }

@st.cache_data(ttl=600)
def fetch_500_data(issue=""):
    """从 500.com 获取数据，支持期次查询"""
    # 500.com 的14场胜负彩地址，如果不传 issue 则显示当前期
    if issue:
        url = f"https://datachart.500.com/sfzc/history/history.php?expect={issue}"
    else:
        url = "https://datachart.500.com/sfzc/"
        
    try:
        res = requests.get(url, headers=get_headers(), timeout=10)
        res.encoding = 'utf-8' # 500.com 通常是 utf-8
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 定位表格 (500.com 的 ID 通常是 table_data)
        table = soup.select_one('#table_data')
        if not table:
            # 备用方案：抓取常规页面表格
            rows = soup.select('tr.tr1, tr.tr2')
        else:
            rows = table.select('tr')

        data = []
        for row in rows:
            tds = row.find_all('td')
            if len(tds) < 5: continue
            
            # 逻辑清洗
            cells = [td.get_text(strip=True) for td in tds]
            # 根据 500.com 结构匹配字段
            item = {
                "场次": cells[0],
                "赛事": cells[1],
                "开赛时间": cells[2],
                "对阵": f"{cells[3]} VS {cells[4]}",
                "数据": "查看详情"
            }
            data.append(item)
        return pd.DataFrame(data)
    except Exception as e:
        return None

# --- UI 界面 ---
st.title("⚽ 足彩14场数据查询 (备用引擎)")
st.caption("提示：由于原站IP封锁，已切换至 500.com 数据源")

with st.sidebar:
    st.header("设置")
    issue_input = st.text_input("请输入期次（例如：24010）", placeholder="留空显示最新一期")
    run_btn = st.button("获取数据")

# 默认加载最新一期
if run_btn or 'first_run' not in st.session_state:
    st.session_state['first_run'] = True
    with st.spinner('正在调取最新赔率数据...'):
        df = fetch_500_data(issue_input)
        
        if df is not None and not df.empty:
            st.success(f"成功获取第 {issue_input if issue_input else '最新'} 期数据")
            st.table(df) # 使用静态表格展示，更稳定
            
            # Markdown 导出
            md_code = df.to_markdown(index=False)
            st.download_button("📥 导出 Markdown", md_code, "zucai_data.md")
        else:
            st.error("无法获取数据。请检查期次输入是否有误，或尝试本地运行。")

st.info("💡 如果云端持续失败，建议下载代码到本地运行，本地网络通常不会被拦截。")
