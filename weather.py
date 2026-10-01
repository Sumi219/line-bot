# ========== weather.py：到氣象署、環境部抓資料（第 3 課的函式，改成回傳「一包資料」給卡片用）==========
import os, time, requests
import urllib3
urllib3.disable_warnings()   # 氣象署、環境部網站的憑證格式較舊，下面抓資料都加 verify=False

CWA_KEY = os.environ.get('CWA_KEY', '')   # 中央氣象署授權碼（第 ① 格填）
AQI_KEY = os.environ.get('AQI_KEY', '')   # 環境部 API 金鑰（第 ① 格填）


# ---- 地震：回傳 [地震文字說明, 地震報告圖網址] ----
def earth_quake():
    try:
        url1 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0016-001?Authorization={CWA_KEY}'  # 小區域
        url2 = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/E-A0015-001?Authorization={CWA_KEY}'  # 顯著有感
        eq1 = requests.get(url1, verify=False, timeout=10).json()['records']['Earthquake'][0]
        eq2 = requests.get(url2, verify=False, timeout=10).json()['records']['Earthquake'][0]
        eq = eq1   # 先用小區域地震，顯著有感比較近發生就換成它
        if eq2['EarthquakeInfo']['OriginTime'] > eq1['EarthquakeInfo']['OriginTime']:
            eq = eq2
        return [eq['ReportContent'], eq['ReportImageURI']]
    except Exception as e:
        print('地震抓取失敗：', e)
        return ['抓取失敗...', '']


# ---- 監視器：地點名稱 → 網址（找不到回傳空字串）----
CAMERAS = {   # 高雄市交通監視器
    '夢時代': 'https://cctv1.kctmc.nat.gov.tw/27e5c086/',
    '鼓山渡輪站': 'https://cctv3.kctmc.nat.gov.tw/ddb9fc98/',
    '中正交流道': 'https://cctv3.kctmc.nat.gov.tw/166157d9/',
    '五福愛河': 'https://cctv4.kctmc.nat.gov.tw/335e2702/',
}

def cctv(msg):
    return CAMERAS.get(msg, '')


# ---- 天氣：傳入地址，回傳一包資料（字典），抓不到的欄位是空字串 ----
FORECAST_ID = {"宜蘭縣":"F-D0047-001","桃園市":"F-D0047-005","新竹縣":"F-D0047-009","苗栗縣":"F-D0047-013",
    "彰化縣":"F-D0047-017","南投縣":"F-D0047-021","雲林縣":"F-D0047-025","嘉義縣":"F-D0047-029",
    "屏東縣":"F-D0047-033","臺東縣":"F-D0047-037","花蓮縣":"F-D0047-041","澎湖縣":"F-D0047-045",
    "基隆市":"F-D0047-049","新竹市":"F-D0047-053","嘉義市":"F-D0047-057","臺北市":"F-D0047-061",
    "高雄市":"F-D0047-065","新北市":"F-D0047-069","臺中市":"F-D0047-073","臺南市":"F-D0047-077",
    "連江縣":"F-D0047-081","金門縣":"F-D0047-085"}

def weather_data(address):
    address = address.replace('台', '臺')
    data = {'地點': '', '天氣': '', '溫度': '', '濕度': '', '預報': '', '降雨': '', 'AQI': '', '空氣': ''}

    # 1. 即時天氣（氣象觀測站）
    try:
        for dataset in ['O-A0001-001', 'O-A0003-001']:
            url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{dataset}?Authorization={CWA_KEY}'
            for s in requests.get(url, verify=False, timeout=10).json()['records']['Station']:
                place = s['GeoInfo']['CountyName'] + s['GeoInfo']['TownName']
                if place in address and data['地點'] == '':      # 同一個地方只用第一個測站
                    w = s['WeatherElement']
                    data.update({'地點': place, '天氣': w['Weather'],
                                 '溫度': w['AirTemperature'], '濕度': w['RelativeHumidity']})
    except Exception as e:
        print('即時天氣抓取失敗：', e)

    # 2. 未來三小時預報
    try:
        city_id = ''
        for name in FORECAST_ID:
            if name in address:
                city_id = FORECAST_ID[name]
        t = time.time() + 28800   # Colab 和 Vercel 都用世界標準時間，要加八小時
        now = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(t))
        later = time.strftime('%Y-%m-%dT%H:%M:%S', time.gmtime(t + 10800))
        url = f'https://opendata.cwa.gov.tw/api/v1/rest/datastore/{city_id}?Authorization={CWA_KEY}&timeFrom={now}&timeTo={later}'
        loc = requests.get(url, verify=False, timeout=10).json()['records']['Locations'][0]
        for i in loc['Location']:
            place = loc['LocationsName'] + i['LocationName']
            if place in address:
                e = {x['ElementName']: x['Time'][0]['ElementValue'][0] for x in i['WeatherElement']}   # 用名稱找資料
                data['預報'] = e['天氣預報綜合描述']['WeatherDescription']
                data['降雨'] = e['3小時降雨機率']['ProbabilityOfPrecipitation']
                if data['地點'] == '':
                    data['地點'] = place
    except Exception as e:
        print('預報抓取失敗：', e)

    # 3. 空氣品質（環境部）
    try:
        url = f'https://data.moenv.gov.tw/api/v2/aqx_p_432?api_key={AQI_KEY}&limit=1000&sort=ImportDate%20desc&format=JSON'
        records = requests.get(url, verify=False, timeout=10).json()
        if 'records' in records:
            records = records['records']
        for item in records:
            if item['aqi'] != '' and item['county'] + item['sitename'] in address:
                aqi = int(item['aqi'])
                data['AQI'] = str(aqi)
                data['空氣'] = ['良好','普通','對敏感族群不健康','對所有族群不健康','非常不健康','危害'][min(aqi // 50, 5)]
                break
    except Exception as e:
        print('空氣品質抓取失敗：', e)

    if data['地點'] == '':
        data['地點'] = address
    return data
