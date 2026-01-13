import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

# 设置页面配置
st.set_page_config(page_title="足彩14场数据分析插件", layout="wide")

def get_headers():
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://cp.zgzcw.com/lottery/zucai/14csfc/index.jsp",
        "Connection": "keep-alive"
    }

@st.cache_data(ttl=3600)  # 缓存1小时，减少请求频率
def get_issue_list():
    url = "https://cp.zgzcw.com/lottery/zucai/14csfc/index.jsp"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'html.parser')
        select_tag = soup.select_one('#lotteryIssue')
        if select_tag:
            options = select_tag.find_all('option')
            issues = [opt.get('value') for opt in options if opt.get('value')]
            return issues
        return []
    except Exception as e:
        return []

def fetch_zucai_data(issue):
    url = f"https://cp.zgzcw.com/lottery/zucai/14csfc/index.jsp?lotteryIssue={issue}"
    try:
        response = requests.get(url, headers=get_headers(), timeout=10)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.tr_vs')
        
        data = []
        for row in rows:
            tds = row.find_all('td')
            if len(tds) < 10: continue
            
            # 提取数据
            match = {
                "序号": tds[0].get_text(strip=True),
                "赛事": tds[1].get_text(strip=True),
                "开赛时间": tds[2].get_text(strip=True),
                "主队": tds[3].get_text(strip=True),
                "比分/状态": tds[4].get_text(strip=True) if tds[4].get_text(strip=True) else "VS",
                "客队": tds[5].get_text(strip=True),
                "胜": tds[8].select('span')[0].text if len(tds[8].select('span')) > 0 else "-",
                "平": tds[8].select('span')[1].text if len(tds[8].select('span')) > 1 else "-",
                "负": tds[8].select('span')[2].text if len(tds[8].select('span')) > 2 else "-",
            }
            data.append(match)
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"无法连接到服务器: {e}")
        return None

# --- UI 界面 ---
st.title("⚽ 14场胜负彩数据查询 (云端优化版)")

st.sidebar.header("查询设置")
with st.sidebar:
    issues = get_issue_list()
    
    if issues:
        selected_issue = st.selectbox("请选择期次：", issues)
    else:
        st.warning("⚠️ 自动获取期次列表失败，请手动输入期次：")
        # 如果自动获取失败，提供手动输入框作为兜底
        selected_issue = st.text_input("手动输入期次（如 24050）：", value="")

if selected_issue:
    st.info(f"正在查询：第 {selected_issue} 期")
    df = fetch_zucai_data(selected_issue)
    
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True)
        # 导出逻辑保持不变...
        md_string = df.to_markdown(index=False)
        st.download_button("📥 导出 Markdown", md_string, f"zucai_{selected_issue}.md")
    else:
        st.error("❌ 无法获取该期次数据。可能是由于网站禁止了云服务器访问。")
        st.markdown("""
        **排查建议：**
        1. 本地运行（Localhost）通常比云端更容易成功。
        2. 稍后再试，可能由于请求过于频繁触发了临时锁定。
        """)
