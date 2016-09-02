import requests


URL = "http://www.opentable.com/restaurant/profile/106969/search"

def post():
    payload = { 'covers': '2', 'dateTime': '2016-09-17 19:00', 'restref': 106969 }
    r = requests.post(URL, payload)
    return r
    
if __name__ == '__main__':
    main()
