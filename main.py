import pywifi
import math
from colorama import Fore, Style
import subprocess
import requests
import time

def calculate_distance(signal_strength, frequency):
    exp = (27.55 - (20 * math.log10(frequency)) + abs(signal_strength)) / 20.0
    distance = pow(10.0, exp)
    return distance

def save_to_file(file_name, content):
    with open(file_name, "a") as file:
        file.write(content + "\n")

def ping_device(ip_address):
    result = subprocess.run(['ping', '-n', '1', ip_address], capture_output=True)
    return result.returncode == 0

def get_device_vendor(mac_address):
    url = "https://api.macvendors.com/" + mac_address
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.text.strip()
    except requests.exceptions.RequestException:
        pass
    return "Nieznany"

def get_security_type(profile):
    akm_suites = profile.akm
    cipher_suites = profile.cipher

    if pywifi.const.AKM_TYPE_WPA2 in akm_suites:
        return "WPA2"
    elif pywifi.const.AKM_TYPE_WPA in akm_suites:
        return "WPA"
    elif pywifi.const.CIPHER_TYPE_WEP == cipher_suites:
        return "WEP"
    elif pywifi.const.AKM_TYPE_NONE in akm_suites:
        return "Brak zabezpieczeń"
    else:
        return "Nieznane"

def get_internet_provider(ssid):
    providers = {
        "WIFI_PROVIDER_1": "Dostawca 1",
        "WIFI_PROVIDER_2": "Dostawca 2",
        "WIFI_PROVIDER_3": "Dostawca 3"
        # Dodaj więcej dostawców i odpowiadające im nazwy sieci (SSID)
    }

    for network_ssid, provider in providers.items():
        if network_ssid.lower() in ssid.lower():
            return provider

    return "Nieznany"

def is_password_protected(profile):
    return profile.akm != pywifi.const.AKM_TYPE_NONE

def get_operating_system(mac_address):
    url = "https://macvendors.co/api/" + mac_address + "/json"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            json_data = response.json()
            return json_data.get("result").get("company")
    except requests.exceptions.RequestException:
        pass
    return "Nieznany"

def measure_speed(ip_address):
    try:
        response = requests.get("http://" + ip_address, timeout=5)
        return response.elapsed.total_seconds()
    except requests.exceptions.RequestException:
        return -1

def scan_networks():
    wifi = pywifi.PyWiFi()
    iface = wifi.interfaces()[0]

    iface.scan()
    networks = iface.scan_results()

    if networks:
        log_content = "Znaleziono dostępne sieci Wi-Fi:"
        print(log_content)
        save_to_file("wifi_log.txt", log_content)
        for network in networks:
            ssid = network.ssid
            signal_strength = network.signal
            frequency = network.freq / 1000  # Przeliczamy na GHz
            distance = calculate_distance(signal_strength, frequency)
            log_content = "Nazwa: " + Fore.BLUE + "{}, Sygnał: ".format(ssid) + Fore.GREEN + "{} dBm".format(signal_strength) + Style.RESET_ALL + ", Częstotliwość: {} GHz, Odległość: ".format(frequency) + Fore.MAGENTA + Style.BRIGHT + "{:.2f} metrów".format(distance) + Style.RESET_ALL
            print(log_content)
            save_to_file("wifi_log.txt", log_content)

            # Pingowanie urządzenia
            ip_address = network.bssid
            start_time = time.time()
            ping_result = ping_device(ip_address)
            end_time = time.time()
            elapsed_time = end_time - start_time
            if ping_result:
                print("Ping do urządzenia {} udany.".format(ip_address))
                save_to_file("wifi_log.txt", "Ping do urządzenia {} udany.".format(ip_address))
            else:
                print("Ping do urządzenia {} nieudany.".format(ip_address))
                save_to_file("wifi_log.txt", "Ping do urządzenia {} nieudany.".format(ip_address))

            # Pomiar szybkości połączenia
            speed = measure_speed(ip_address)
            if speed >= 0:
                print("Szybkość połączenia z urządzeniem {}: {:.2f} s".format(ip_address, speed))
                save_to_file("wifi_log.txt", "Szybkość połączenia z urządzeniem {}: {:.2f} s".format(ip_address, speed))
            else:
                print("Nie można zmierzyć szybkości połączenia z urządzeniem {}".format(ip_address))
                save_to_file("wifi_log.txt", "Nie można zmierzyć szybkości połączenia z urządzeniem {}".format(ip_address))

            # Rozpoznawanie urządzenia na podstawie adresu MAC
            device_vendor = get_device_vendor(network.bssid)
            print("Producent urządzenia: {}".format(device_vendor))
            save_to_file("wifi_log.txt", "Producent urządzenia: {}".format(device_vendor))

            # Dodanie profilu sieciowego do interfejsu
            profile = iface.add_network_profile(network)

            # Wykrywanie rodzaju zabezpieczeń
            security_type = get_security_type(profile)
            print("Rodzaj zabezpieczenia: {}".format(security_type))
            save_to_file("wifi_log.txt", "Rodzaj zabezpieczenia: {}".format(security_type))

            # Sprawdzanie czy sieć jest zabezpieczona hasłem
            is_protected = is_password_protected(profile)
            print("Czy sieć jest zabezpieczona hasłem: {}".format(is_protected))
            save_to_file("wifi_log.txt", "Czy sieć jest zabezpieczona hasłem: {}".format(is_protected))

            # Rozpoznawanie dostawcy internetu
            internet_provider = get_internet_provider(ssid)
            print("Dostawca internetu: {}".format(internet_provider))
            save_to_file("wifi_log.txt", "Dostawca internetu: {}".format(internet_provider))

            # Rozpoznawanie systemu operacyjnego
            operating_system = get_operating_system(network.bssid)
            print("System operacyjny: {}".format(operating_system))
            save_to_file("wifi_log.txt", "System operacyjny: {}".format(operating_system))

            # Wyświetlanie czasu przeskanowania urządzenia
            elapsed_time = round(elapsed_time, 2)
            elapsed_time_str = Fore.RED + "{:.2f} s".format(elapsed_time) + Style.RESET_ALL
            print("Czas przeskanowania urządzenia: {}".format(elapsed_time_str))
            save_to_file("wifi_log.txt", "Czas przeskanowania urządzenia: {}".format(elapsed_time_str))

            print()

    else:
        log_content = "Nie znaleziono żadnych dostępnych sieci Wi-Fi."
        print(log_content)
        save_to_file("wifi_log.txt", log_content)

scan_networks()
