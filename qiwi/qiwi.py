import os

import requests


class QiwiApi:
    """
    Класс реализующий запросы к КИВИ для получения информации по платежам
    """

    def __init__(self):
        self.api_access_token = os.environ.get('api_access_token')
        self.session = requests.Session()
        self.session.headers = {
            'Accept': 'application/json',
            'authorization': 'Bearer ' + self.api_access_token,
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 '
                          'Safari/537.36 '
        }

    def pay_status(self, pay_id):
        response = self.session.get(
            f'https://api.qiwi.com/partner/bill/v1/bills/{pay_id}',
        ).json()
        if not response.get('status'):
            return None
        return response['status']['value']

    def create_payment(self, pay_id, amount):
        data = {
            "amount": {
                "currency": "RUB",
                "value": f"{amount}.00"
            },
            "expirationDateTime": "2023-12-10T09:02:00+03:00"
        }
        response = requests.put(f'https://api.qiwi.com/partner/bill/v1/bills/{pay_id}', json=data).json()
        if response.get('payUrl'):
            return response
        return None
