import requests

candidates = [
    "https://static.codatta.io/static/robotics/berkeley_rpt_converted_externally_to_rlds_ep000000.gif",
    "https://static.codatta.io/static/images/berkeley_rpt_converted_externally_to_rlds_ep000000.gif",
    "https://static.codatta.io/robotics/berkeley_rpt_converted_externally_to_rlds_ep000000.gif",
    "https://codatta-static.oss-ap-southeast-1.aliyuncs.com/berkeley_rpt_converted_externally_to_rlds_ep000000.gif",
]
for url in candidates:
    try:
        r = requests.head(url, timeout=10, allow_redirects=True)
        print(r.status_code, url)
    except Exception as e:
        print("ERR", url, e)
