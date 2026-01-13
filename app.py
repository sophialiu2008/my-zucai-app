import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from io import BytesIO

# 设置页面配置
st.set_page_config(page_title="足彩14场数据分析插件", layout="wide")

def get_issue_list():
    """获取所有可用的期次列表"""
    url = "https://cp.zgzcw.com/lottery/zucai/14csfc/index.jsp"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'html.parser')
        # 查找期次下拉选择框
        select_tag = soup.select_one('#lotteryIssue')
        if select_tag:
            options = select_tag.find_all('option')
            return [opt.get('value') for opt in options if opt.get('value')]
        return []
    except:
        return []

def fetch_zucai_data(issue):
    """根据期次抓取数据"""
    # 如果是最新一期，URL保持默认；如果是往期，添加参数
    url = f"https://cp.zgzcw.com/lottery/zucai/14csfc/index.jsp?lotteryIssue={issue}"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    
    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'gbk'
        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.select('tr.tr_vs')
        
        data = []
        for row in rows:
            tds = row.find_all('td')
            if len(tds) < 10: continue
            
            # 提取数据字段
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
        st.error(f"期次 {issue} 获取失败: {e}")
        return None

# --- UI 界面 ---
st.title("⚽ 14场胜负彩往期数据查询")

# 侧边栏：期次选择
st.sidebar.header("查询设置")
with st.sidebar:
    issues = get_issue_list()
    if issues:
        selected_issue = st.selectbox("请选择期次：", issues)
    else:
        st.error("无法获取期次列表")
        selected_issue = None

if selected_issue:
    st.info(f"当前查看：第 {selected_issue} 期")
    
    # 自动执行抓取
    df = fetch_zucai_data(selected_issue)
    
    if df is not None and not df.empty:
        # 显示表格
        st.dataframe(df, use_container_width=True)
        
        # 导出功能
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            md_string = df.to_markdown(index=False)
            st.download_button(
                label=f"📥 导出第 {selected_issue} 期 Markdown",
                data=md_string,
                file_name=f"zucai_{selected_issue}.md",
                mime="text/markdown",
            )
        
        with col2:
            # Excel 导出
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button(
                label=f"📊 导出第 {selected_issue} 期 Excel",
                data=output.getvalue(),
                file_name=f"zucai_{selected_issue}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            
        with st.expander("查看 Markdown 源码"):
            st.code(df.to_markdown(index=False), language="markdown")
    else:
        st.warning("该期次暂无数据或页面结构已变化。")
