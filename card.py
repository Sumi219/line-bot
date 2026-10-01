# ========== card.py：把天氣資料排成一張 Flex 卡片 ==========
# 想改樣子：改下面 THEME 的顏色（填你 Canva 選單用的色碼），或把 bubble 的內容整段貼到
# Flex Message Simulator（https://developers.line.biz/flex-simulator/）拖拉修改，再貼回來
THEME = {
    '主色': '#2E7D6B',    # 卡片頂端的底色
    '字色': '#FFFFFF',    # 頂端的字
    '強調': '#F4A340',    # 溫度數字、按鈕
}

WEATHER_ICON = {'晴': '☀️', '雲': '⛅', '陰': '☁️', '雨': '🌧️', '雷': '⛈️', '霧': '🌫️'}
AQI_COLOR = ['#3CB371', '#E6B800', '#FF8C00', '#E53935', '#8E24AA', '#6D1B1B']   # 良好、普通…危害


def icon(weather):
    for word in ['雷', '雨', '霧', '陰', '雲', '晴']:   # 越嚴重的排越前面，先找到先用
        if word in weather:
            return WEATHER_ICON[word]
    return '🌡️'


def row(name, value):   # 一列「名稱 …… 數值」
    return {'type': 'box', 'layout': 'horizontal', 'contents': [
        {'type': 'text', 'text': name, 'size': 'sm', 'color': '#888888', 'flex': 2},
        {'type': 'text', 'text': value or '—', 'size': 'sm', 'color': '#333333', 'flex': 5, 'wrap': True}]}


def weather_card(d, title='現在天氣'):
    aqi_color = AQI_COLOR[min(int(d['AQI']) // 50, 5)] if d['AQI'] else '#AAAAAA'
    bubble = {
        'type': 'bubble',
        'header': {'type': 'box', 'layout': 'vertical', 'backgroundColor': THEME['主色'], 'contents': [
            {'type': 'text', 'text': title, 'size': 'sm', 'color': THEME['字色']},
            {'type': 'text', 'text': d['地點'], 'size': 'xl', 'weight': 'bold', 'color': THEME['字色']}]},
        'body': {'type': 'box', 'layout': 'vertical', 'spacing': 'md', 'contents': [
            {'type': 'box', 'layout': 'horizontal', 'contents': [
                {'type': 'text', 'text': icon(d['天氣']), 'size': '3xl', 'flex': 0},
                {'type': 'text', 'text': (d['溫度'] + '°C') if d['溫度'] else '—', 'size': '3xl',
                 'weight': 'bold', 'color': THEME['強調'], 'align': 'end', 'gravity': 'center'}]},
            row('天氣', d['天氣']),
            row('濕度', (d['濕度'] + '%') if d['濕度'] else ''),
            row('降雨機率', (d['降雨'] + '%') if d['降雨'] else ''),
            {'type': 'box', 'layout': 'horizontal', 'contents': [
                {'type': 'text', 'text': '空氣', 'size': 'sm', 'color': '#888888', 'flex': 2},
                {'type': 'text', 'text': f"AQI {d['AQI']} {d['空氣']}" if d['AQI'] else '—',
                 'size': 'sm', 'color': aqi_color, 'weight': 'bold', 'flex': 5}]},
            {'type': 'separator'},
            {'type': 'text', 'text': d['預報'] or '沒有抓到預報', 'size': 'xs', 'color': '#666666', 'wrap': True}]},
        'footer': {'type': 'box', 'layout': 'horizontal', 'spacing': 'sm', 'contents': [
            {'type': 'button', 'style': 'primary', 'color': THEME['強調'], 'height': 'sm',
             'action': {'type': 'message', 'label': '雷達回波', 'text': '雷達回波圖'}},
            {'type': 'button', 'style': 'secondary', 'height': 'sm',
             'action': {'type': 'uri', 'label': '換個地點', 'uri': 'https://line.me/R/nv/location/'}}]},
    }
    return bubble
