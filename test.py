
from utils.pesapal import Pesapal

if __name__ == '__main__':
    pesapal = Pesapal()
    
    pesapal.register_IPN_URL()
    pesapal.get_IPN_list()
