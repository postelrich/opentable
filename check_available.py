import argparse
import datetime
import requests
import time
import traceback
from bs4 import BeautifulSoup
from functools import partial
from twilio.rest import TwilioRestClient


URL = "http://www.opentable.com/restaurant/profile/{}/search"

def check_opentable(restaurant_id, num_people, date_str):
    payload = { 'covers': num_people, 'dateTime': date_str, 'restref': restaurant_id }
    r = requests.post(URL.format(restaurant_id), payload)
    return r


def parse_response(s):
    soup = BeautifulSoup(s, 'html.parser')
    result_text = soup.findAll('h4', {'class': 'dtp-result-text'})
    if not result_text:
        return None
    if not result_text[0].contents:
        return None
    return result_text[0].contents[0]


def is_available(s):
    return not s.startswith('No tables are available')


def send_twilio_text(twilio_sid, twilio_token, to, from_, msg):
    client = TwilioRestClient(twilio_sid, twilio_token)
    client.messages.create(to=to, from_=from_, body=msg)


def _args():
    parser = argparse.ArgumentParser('Check restaurant for open reservations.')
    parser.add_argument('--twilio_sid', required=True, help='Twilio account SID')
    parser.add_argument('--twilio_token', required=True, help='Twilio Auth Token')
    parser.add_argument('--to', required=True, help='number to send text to')
    parser.add_argument('--from_num', required=True, help='number to send text from')
    parser.add_argument('opentable_id', metavar='OID', type=str,
                        help='OpenTable restaurant id')
    parser.add_argument('num_people', metavar='PEOPLE', type=str,
                        help='number of people for reservation')
    parser.add_argument('res_date', metavar='DATE', type=str,
                        help='reservation date to check YYYY-MM-DD HH:MM')
    return parser.parse_args()


def main():
    args = _args()
    print("OpenTable reservation availability service starting...")
    try:
        send_text = partial(send_twilio_text, args.twilio_sid, args.twilio_token, args.to, args.from_num)
        loop_count = 0
        no_available_count = 0
        errors = dict()
        while True:
            try:
                loop_count += 1
                print('Attempt #{}'.format(loop_count))
                available = is_available(parse_response(check_opentable(args.opentable_id,
                                                                        args.num_people,
                                                                        args.res_date).text))
                if available:
                    print('Availability found on attempt #{}'.format(loop_count))
                    send_text('Found available reservations. HURRY AND CHECK')
                elif no_available_count > 6 * 4:
                    error_txt = ' | '.join('{0}: {1}'.format(k, v) for k, v in errors.items())
                    send_text("Nothing yet, but I'm still looking. Errors: {}".format(error_txt))
                    no_available_count = 0
                    errors = dict()
                print('Nothing found on attempt #{}'.format(loop_count))
                no_available_count += 1
                time.sleep(60 * 10)
            except Exception as e:
                traceback.print_exc()
                errors[type(e)] = str(e)
    except KeyboardInterrupt:
        print("Exiting...")


if __name__ == '__main__':
    main()
