import sqlite3
import math
from turtledemo.penrose import start

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen

import self
from kivy.lang import Builder
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy_garden.mapview import MapView, MapMarkerPopup, MapMarker
from kivy.core.window import Window
from kivymd.app import MDApp
from kivymd.color_definitions import colors
from kivymd.uix.screen import MDScreen
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.list import OneLineIconListItem
from kivymd.uix.button import MDFlatButton
from kivy.clock import Clock
import requests
from plyer import gps
from kivy.utils import platform
from kivy.graphics import Color, Line
import re
from kivy.uix.dropdown import DropDown

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in kilometers
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = R * c
    return distance

class MapScreen(MDScreen):
    current_route = None
    route_points = []
    list_of_lines = []
    getting_pharmacy_timer = None
    pharmacyname = []
    connection = None
    cursor = None
    user_lat = None
    user_lon = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.map_view = pharmacymapview()  # Make sure you're using the correct class for the map
        self.add_widget(self.map_view)
        self.app = App.get_running_app()
        self.app.on_start()
        self.initialize_map_view_functions()


    def initialize_map_view_functions(self):
        self.map_view.center_on_location(26.11272178718283, 91.72465681076355)


        pharmacy_data = {'latitude': 26.1127, 'longitude': 91.7246, 'name': 'Pharmacy 1'}
        pharmacy_marker = PharmacyMarker(pharmacy=pharmacy_data, map_view=self.map_view)
        self.map_view.add_widget(pharmacy_marker)
        self.map_view.add_pharmacies(pharmacy_data, is_nearest=True)

    def close_popup(self, *args):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def on_release(self, button_layout=None):
        print("Marker clicked!")
        if self.map_view.current_route:
            print("Clearing existing route...")
            self.map_view.clear_route_lines()
        ...
        if self.map_view.current_route:
            self.map_view.clear_route_lines()
        if self.popup is None:
            if self.map_view.current_route:
                for line in self.map_view.current_route:
                    self.map_view.canvas.remove(line)
                self.map_view.current_route = []
            if self.popup is None:
                if button_layout is None:
                    button_layout = BoxLayout(orientation='horizontal', padding=5, spacing=10, size_hint_y=None,
                                              height='40dp')

                box = BoxLayout(orientation='vertical', padding=7)

                name_label = Label(
                    text=f"Name: {self.pharmacy['name']}",
                    font_size=20,
                    size_hint_y=None,
                    height='40dp',
                    text_size=(self.width * 0.7, None),
                    halign='center',
                    valign='middle'
                )
                name_label.bind(size=name_label.setter('text_size'))
                box.add_widget(name_label)

                address_label = Label(
                    text=f"Address: {self.pharmacy['address']}",
                    font_size=16,
                    size_hint_y=None,
                    height='40dp',
                    text_size=(self.width * 0.7, None),
                    halign='center',
                    valign='middle'
                )
                address_label.bind(size=address_label.setter('text_size'))
                box.add_widget(address_label)

                self.popup = Popup(content=box, size_hint=(0.5, 0.3), auto_dismiss=False)

                def show_route_and_close(instance):
                    self.get_route()
                    self.close_popup(instance)

                show_route_button = Button(text="Show Route")
                show_route_button.bind(on_press=show_route_and_close)
                button_layout.add_widget(show_route_button)

                close_button = Button(text="Close")
                close_button.bind(on_press=self.close_popup)
                button_layout.add_widget(close_button)
                box.add_widget(button_layout)
                self.popup.open()
    def get_route(self, *args):
        self.map_view.clear_route_lines()
        user_lat = self.map_view.user_lat
        user_lon = self.map_view.user_lon

        pharmacy_lat = self.pharmacy['latitude']
        pharmacy_lon = self.pharmacy['longitude']
        self.route_points = []
        self.list_of_lines = []

        body = {"coordinates": [[user_lon, user_lat], [pharmacy_lon, pharmacy_lat]]}
        headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': '5b3ce3597851110001cf624849b2804d9b6444cab620914003876d94',
            'Content-Type': 'application/json; charset=utf-8'
        }


        self.call = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/gpx', json=body,
                                  headers=headers)
        print(self.call.text)
        string_res = self.call.text
        print(string_res)
        tag = 'rtept'
        reg_str = '</' + tag + '>(.*?)' + '>'
        res = re.findall(reg_str, string_res)
        print(res)
        print('__________________________________')
        string1 = str(res)
        tag1 = '"'
        reg_str1 = '"' + '(.*?)' + '"'
        res1 = re.findall(reg_str1, string1)
        print(res1)

        for i in range(0, len(res1) - 1, 2):
            self.points_lat = res1[i]  #
            self.points_lon = res1[i + 1]
            self.points_pop = MapMarkerPopup(lat=self.points_lat, lon=self.points_lon,
                                             source='output-onlinepngtools.png')
            self.route_points.append(self.points_pop)
            self.map_view.add_widget(self.points_pop)

        with self.canvas:

            Color(0.055, 0.400, 1.0, 1.0)
            for j in range(0, len(self.route_points) - 1, 1):
                self.lines = Line(points=(self.route_points[j].pos[0], self.route_points[j].pos[1],
                                          self.route_points[j + 1].pos[0], self.route_points[j + 1].pos[1]),
                                  width=3)
                self.list_of_lines.append(self.lines)

        Clock.schedule_interval(self.update_route_lines, 1 / 30)
    def update_route_lines(self, *args):
            for j in range(0,len(self.route_points),1):
                self.list_of_lines[j - 1].points = [
                    self.route_points[j - 1].pos[0], self.route_points[j - 1].pos[1],
                    self.route_points[j].pos[0], self.route_points[j].pos[1]
                ]

    def find_nearest_pharmacy(self, medicine_id):
        self.cursor.execute("SELECT latitude, longitude, name, address, id FROM pharmacies")
        pharmacies = self.cursor.fetchall()

        user_lat = self.root.ids.map_view.user_lat
        user_lon = self.root.ids.map_view.user_lon

        if user_lat is None or user_lon is None:
            print("User coordinates are not set.")
            return

        # Sort pharmacies by distance from the user
        pharmacies_with_distances = [
            (pharmacy, haversine(user_lat, user_lon, pharmacy[0], pharmacy[1]))
            for pharmacy in pharmacies if pharmacy[0] is not None and pharmacy[1] is not None
        ]
        pharmacies_with_distances.sort(key=lambda x: x[1])


        nearest_pharmacy = None
        for pharmacy, distance in pharmacies_with_distances:
            pharmacy_id = pharmacy[4]
            self.cursor.execute("SELECT 1 FROM pharmacy_medicines WHERE pharmacy_id = ? AND medicine_id = ?",
                                (pharmacy_id, medicine_id))
            if self.cursor.fetchone():
                nearest_pharmacy = pharmacy
                nearest_distance = distance
                break  # Stop when the first pharmacy with the medicine is found

        if nearest_pharmacy:
            print(
                f"Nearest Pharmacy with Medicine: {nearest_pharmacy[2]}, "
                f"Address: {nearest_pharmacy[3]}, Distance: {nearest_distance:.2f} km"
            )
            self.root.ids.map_view.add_pharmacies({
                'name': nearest_pharmacy[2],
                'address': nearest_pharmacy[3],
                'latitude': nearest_pharmacy[0],
                'longitude': nearest_pharmacy[1]
            }, is_nearest=True)
        else:
            print("No pharmacy found with the requested medicine.")

    def on_start(self):
        self.connection = sqlite3.connect("pharmacy_medicine.db")
        self.cursor = self.connection.cursor()

    def on_status(self, stype, status):
        print(f"GPS status: {stype}, {status}")

    def build(self):
        Window.clearcolor = (.8, 0.8, 0.9, 1)
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(MapScreen(name="map_screen"))
        return sm

    def get_medicine_id(self, medicine_name):
        """Retrieve the medicine ID based on the medicine name."""
        self.cursor.execute("SELECT id FROM medicines WHERE medicine_name = ?", (medicine_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def search_medicine(self, medicine_name):
        self.dropdown.clear_widgets()
        medicine_id = self.get_medicine_id(medicine_name)  # Your method to retrieve the medicine ID
        if medicine_id:
            # Now pass the medicine_id to find the nearest pharmacy
            self.find_nearest_pharmacy(medicine_id)
        else:
            print("Medicine not found")
        self.cursor.execute("SELECT medicine_name FROM medicines WHERE medicine_name LIKE ?", (f"%{medicine_name}%",))
        medicines = self.cursor.fetchall()
        if medicines:

            for medicine in medicines:
                suggestion_btn = Button(
                    text=medicine[0],
                    size_hint_y=None,
                    height=40
                )
                suggestion_btn.bind(on_release=lambda btn: self.on_suggestion_select(btn.text))
                self.dropdown.add_widget(suggestion_btn)

            self.dropdown.open(self.root.ids.search_input)
        else:
            print("No suggestions found.")

    def on_suggestion_select(self, medicine_name):
        self.root.ids.search_input.text = medicine_name
        self.dropdown.dismiss()
        self.clear_and_add_pharmacies(medicine_name)

    def clear_and_add_pharmacies(self, medicine_name):
        self.root.ids.map_view.clear_markers()

        self.cursor.execute("SELECT id FROM medicines WHERE medicine_name LIKE ?", (medicine_name,))
        medicine = self.cursor.fetchone()

        if medicine:
            medicine_id = medicine[0]
            sql_statement = """
            SELECT p.* FROM pharmacies p
            INNER JOIN pharmacy_medicines pm ON p.id = pm.pharmacy_id
            WHERE pm.medicine_id = ?
            """
            self.cursor.execute(sql_statement, (medicine_id,))
            pharmacies = self.cursor.fetchall()

            print("Pharmacies with the searched medicine:", pharmacies)

            for pharmacy in pharmacies:
                self.root.ids.map_view.add_pharmacies({
                    'name': pharmacy[1],
                    'address': pharmacy[4],
                    'latitude': pharmacy[2],
                    'longitude': pharmacy[3]
                })
        else:
            print(f"No medicine found with the name: {medicine_name}")
        self.find_nearest_pharmacy(medicine_id)



class PharmacyMarker(MapMarkerPopup):
    def __init__(self, pharmacy, map_view, **kwargs):
        super().__init__(**kwargs)
        self.pharmacy = pharmacy
        self.map_view = map_view
        self.popup = None
        self.route_points = []
        self.list_of_lines = []
        if not hasattr(self.map_view, 'current_route') or self.map_view.current_route is None:
            self.map_view.current_route = []

    def close_popup(self, *args):
        if self.popup:
            self.popup.dismiss()
            self.popup = None

    def on_release(self, button_layout=None):
        print("Marker clicked!")
        if self.map_view.current_route:
            print("Clearing existing route...")
            self.map_view.clear_route_lines()
        ...
        if self.map_view.current_route:
            self.map_view.clear_route_lines()
        if self.popup is None:
            if self.map_view.current_route:
                for line in self.map_view.current_route:
                    self.map_view.canvas.remove(line)
                self.map_view.current_route = []
            if self.popup is None:
                if button_layout is None:
                    button_layout = BoxLayout(orientation='horizontal', padding=5, spacing=10, size_hint_y=None,
                                              height='40dp')

                box = BoxLayout(orientation='vertical', padding=7)

                name_label = Label(
                    text=f"Name: {self.pharmacy['name']}",
                    font_size=20,
                    size_hint_y=None,
                    height='40dp',
                    text_size=(self.width * 0.7, None),
                    halign='center',
                    valign='middle'
                )
                name_label.bind(size=name_label.setter('text_size'))
                box.add_widget(name_label)

                address_label = Label(
                    text=f"Address: {self.pharmacy['address']}",
                    font_size=16,
                    size_hint_y=None,
                    height='40dp',
                    text_size=(self.width * 0.7, None),
                    halign='center',
                    valign='middle'
                )
                address_label.bind(size=address_label.setter('text_size'))
                box.add_widget(address_label)

                self.popup = Popup(content=box, size_hint=(0.5, 0.3), auto_dismiss=False)

                def show_route_and_close(instance):
                    self.get_route()
                    self.close_popup(instance)

                show_route_button = Button(text="Show Route")
                show_route_button.bind(on_press=show_route_and_close)
                button_layout.add_widget(show_route_button)

                close_button = Button(text="Close")
                close_button.bind(on_press=self.close_popup)
                button_layout.add_widget(close_button)
                box.add_widget(button_layout)
                self.popup.open()

    def get_route(self, *args):
        self.map_view.clear_route_lines()
        user_lat = self.map_view.user_lat
        user_lon = self.map_view.user_lon

        pharmacy_lat = self.pharmacy['latitude']
        pharmacy_lon = self.pharmacy['longitude']
        self.route_points = []
        self.list_of_lines = []

        body = {"coordinates": [[user_lon, user_lat], [pharmacy_lon, pharmacy_lat]]}
        headers = {
            'Accept': 'application/json, application/geo+json, application/gpx+xml, img/png; charset=utf-8',
            'Authorization': '5b3ce3597851110001cf624849b2804d9b6444cab620914003876d94',
            'Content-Type': 'application/json; charset=utf-8'
        }


        self.call = requests.post('https://api.openrouteservice.org/v2/directions/driving-car/gpx', json=body,
                                  headers=headers)
        print(self.call.text)
        string_res = self.call.text
        print(string_res)
        tag = 'rtept'
        reg_str = '</' + tag + '>(.*?)' + '>'
        res = re.findall(reg_str, string_res)
        print(res)
        print('__________________________________')
        string1 = str(res)
        tag1 = '"'
        reg_str1 = '"' + '(.*?)' + '"'
        res1 = re.findall(reg_str1, string1)
        print(res1)

        for i in range(0, len(res1) - 1, 2):
            self.points_lat = res1[i]  #
            self.points_lon = res1[i + 1]
            self.points_pop = MapMarkerPopup(lat=self.points_lat, lon=self.points_lon,
                                             source='output-onlinepngtools.png')
            self.route_points.append(self.points_pop)
            self.map_view.add_widget(self.points_pop)

        with self.canvas:

            Color(0.055, 0.400, 1.0, 1.0)
            for j in range(0, len(self.route_points) - 1, 1):
                self.lines = Line(points=(self.route_points[j].pos[0], self.route_points[j].pos[1],
                                          self.route_points[j + 1].pos[0], self.route_points[j + 1].pos[1]),
                                  width=3)
                self.list_of_lines.append(self.lines)

        Clock.schedule_interval(self.update_route_lines, 1 / 30)


    def update_route_lines(self, *args):
            for j in range(0,len(self.route_points),1):
                self.list_of_lines[j - 1].points = [
                    self.route_points[j - 1].pos[0], self.route_points[j - 1].pos[1],
                    self.route_points[j].pos[0], self.route_points[j].pos[1]
                ]



class pharmacymapview(MapView):
    current_route = None
    route_points = []
    list_of_lines = []
    getting_pharmacy_timer = None
    pharmacyname = []


    def center_on_location(self, lat, lon):
        self.center_on(lat, lon)
        self.zoom = 13
        self.pin = MapMarkerPopup(lat=26.11272178718283, lon=91.72465681076355, source='user1.png')
        self.pin.size = (50, 50)
        self.add_widget(self.pin)
        self.bind(zoom=self.on_zoom_change)

    def on_zoom_change(self, *args):
        pass
         #self.update_route_lines()

    def add_pharmacies(self, pharmacy,is_nearest=False):
        print("Pharmacy Data:", pharmacy)
        lat = pharmacy.get('latitude')
        lon = pharmacy.get('longitude')

        if lat is None or lon is None:
            print("Error: 'lat' or 'lon' not found in pharmacy data:", pharmacy)
            return


        marker_source = 'circle1.png' if is_nearest else 'pharmacy1.png'

        marker = PharmacyMarker(pharmacy=pharmacy, map_view=self, lat=lat, lon=lon)
        print(f"Adding marker at lat: {lat}, lon: {lon}")
        marker.source = marker_source
        marker.source = marker_source  # Use the marker_source for nearest pharmacy
        self.add_widget(marker)
        self.pharmacyname.append(pharmacy['name'])

    def clear_markers(self):
        for child in self.children[:]:
            if isinstance(child, PharmacyMarker):
                child.on_remove()
                self.remove_widget(child)
        self.pharmacyname.clear()

    def on_touch_down(self, touch):
        if touch.button == 'right':
            return True
        return super().on_touch_down(touch)

    def clear_route_lines(self):
        print("clear_route_lines() called, lines to remove:", len(self.list_of_lines))
        for line in self.list_of_lines:
            try:
                self.canvas.remove(line)
                print("Line removed:", line)
            except Exception as e:
                print("Error removing line:", e)

        self.list_of_lines.clear()

class MergedApp(MDApp):
    connection = None
    cursor = None
    user_lat = None
    user_lon = None

    def find_nearest_pharmacy(self, medicine_id):
        self.cursor.execute("SELECT latitude, longitude, name, address, id FROM pharmacies")
        pharmacies = self.cursor.fetchall()

        user_lat = self.root.ids.map_view.user_lat
        user_lon = self.root.ids.map_view.user_lon

        if user_lat is None or user_lon is None:
            print("User coordinates are not set.")
            return

        # Sort pharmacies by distance from the user
        pharmacies_with_distances = [
            (pharmacy, haversine(user_lat, user_lon, pharmacy[0], pharmacy[1]))
            for pharmacy in pharmacies if pharmacy[0] is not None and pharmacy[1] is not None
        ]
        pharmacies_with_distances.sort(key=lambda x: x[1])

        # Check each pharmacy for the medicine
        nearest_pharmacy = None
        for pharmacy, distance in pharmacies_with_distances:
            pharmacy_id = pharmacy[4]
            self.cursor.execute("SELECT 1 FROM pharmacy_medicines WHERE pharmacy_id = ? AND medicine_id = ?",
                                (pharmacy_id, medicine_id))
            if self.cursor.fetchone():
                nearest_pharmacy = pharmacy
                nearest_distance = distance
                break  # Stop when the first pharmacy with the medicine is found

        if nearest_pharmacy:
            print(
                f"Nearest Pharmacy with Medicine: {nearest_pharmacy[2]}, "
                f"Address: {nearest_pharmacy[3]}, Distance: {nearest_distance:.2f} km"
            )
            self.root.ids.map_view.add_pharmacies({
                'name': nearest_pharmacy[2],
                'address': nearest_pharmacy[3],
                'latitude': nearest_pharmacy[0],
                'longitude': nearest_pharmacy[1]
            }, is_nearest=True)
        else:
            print("No pharmacy found with the requested medicine.")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dropdown = DropDown()

    def on_start(self):
        self.connection = sqlite3.connect("pharmacy_medicine.db")
        self.cursor = self.connection.cursor()

    def on_status(self, stype, status):
        print(f"GPS status: {stype}, {status}")

    def build(self):
        Window.clearcolor = (.8, 0.8, 0.9, 1)
        sm = ScreenManager()
        Builder.load_file("mainmapscreen.kv")
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(MapScreen(name="map_screen"))
        return sm

    def get_medicine_id(self, medicine_name):
        """Retrieve the medicine ID based on the medicine name."""
        self.cursor.execute("SELECT id FROM medicines WHERE medicine_name = ?", (medicine_name,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    def search_medicine(self, medicine_name):
        self.dropdown.clear_widgets()
        medicine_id = self.get_medicine_id(medicine_name)  # Your method to retrieve the medicine ID
        if medicine_id:
            # Now pass the medicine_id to find the nearest pharmacy
            self.find_nearest_pharmacy(medicine_id)
        else:
            print("Medicine not found")
        self.cursor.execute("SELECT medicine_name FROM medicines WHERE medicine_name LIKE ?", (f"%{medicine_name}%",))
        medicines = self.cursor.fetchall()
        if medicines:

            for medicine in medicines:
                suggestion_btn = Button(
                    text=medicine[0],
                    size_hint_y=None,
                    height=40
                )
                suggestion_btn.bind(on_release=lambda btn: self.on_suggestion_select(btn.text))
                self.dropdown.add_widget(suggestion_btn)

            self.dropdown.open(self.root.ids.search_input)
        else:
            print("No suggestions found.")

    def on_suggestion_select(self, medicine_name):
        self.root.ids.search_input.text = medicine_name
        self.dropdown.dismiss()
        self.clear_and_add_pharmacies(medicine_name)

    def clear_and_add_pharmacies(self, medicine_name):
        self.root.ids.map_view.clear_markers()

        self.cursor.execute("SELECT id FROM medicines WHERE medicine_name LIKE ?", (medicine_name,))
        medicine = self.cursor.fetchone()

        if medicine:
            medicine_id = medicine[0]
            sql_statement = """
            SELECT p.* FROM pharmacies p
            INNER JOIN pharmacy_medicines pm ON p.id = pm.pharmacy_id
            WHERE pm.medicine_id = ?
            """
            self.cursor.execute(sql_statement, (medicine_id,))
            pharmacies = self.cursor.fetchall()

            print("Pharmacies with the searched medicine:", pharmacies)

            for pharmacy in pharmacies:
                self.root.ids.map_view.add_pharmacies({
                    'name': pharmacy[1],
                    'address': pharmacy[4],
                    'latitude': pharmacy[2],
                    'longitude': pharmacy[3]
                })
        else:
            print(f"No medicine found with the name: {medicine_name}")
        self.find_nearest_pharmacy(medicine_id)

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super(LoginScreen, self).__init__(**kwargs)
        self.add_widget(Label(text="Username", pos_hint={'center_x': 0.5, 'center_y': 0.7}))
        self.username = TextInput(multiline=False, pos_hint={'center_x': 0.5, 'center_y': 0.6}, size_hint=(0.5, 0.1))
        self.add_widget(self.username)
        self.add_widget(Label(text="Password", pos_hint={'center_x': 0.5, 'center_y': 0.5}))
        self.password = TextInput(multiline=False, password=True, pos_hint={'center_x': 0.5, 'center_y': 0.4}, size_hint=(0.5, 0.1))
        self.add_widget(self.password)
        self.login_button = Button(text="Login", pos_hint={'center_x': 0.5, 'center_y': 0.3}, size_hint=(0.3, 0.1))
        self.login_button.bind(on_press=self.verify_credentials)
        self.add_widget(self.login_button)

    def verify_credentials(self, instance):
        if self.username.text == "user" and self.password.text == "pass":  # Example credentials
            self.manager.current = "map_screen"
        else:
            self.add_widget(Label(text="Invalid credentials", pos_hint={'center_x': 0.5, 'center_y': 0.2}, color=(1, 0, 0, 1)))

if __name__ == '__main__':
    MergedApp().run()