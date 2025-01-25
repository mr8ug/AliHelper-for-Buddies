import bs4 as bs
import selenium.webdriver as webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service

from time import sleep
from datetime import datetime

import os
import json

from tkinter import messagebox

import requests
from dotenv import load_dotenv, dotenv_values

from fpdf import FPDF
import pandas as pd

class AliHelper:
    def __init__(self, localUser:str="", user_data_dir:str="", useChrome:bool=False, useEdge:bool=True, showAlerts:bool=True):
        """Initialize the AliHelper class, this class will help you to get orders from Aliexpress and store them in a list of dictionaries with the following structure:
        {
            "order_id": "",
            "order_date": "",
            "shop_name": "",
            "product_name": "",
            "product_price": "",
            "product_quantity": "",
            "total_price": "",
            "status": "",
            "tracking_link": "",
            "tracking_number": "",
            "tracking_status": "",
            "tracking_process": "",
            "image_references": [],
            "property":""
        }

        Args:
            localUser (str, optional): In case no localUser name be provided will use localmachine as property value to orders. Defaults to "".
            user_data_dir (str, optional): In case no user data path is provided, will use defaults path for User Data Path for chrome or edge. Defaults to "".
            useChrome (bool, optional): By default Edge is used, but if ChromeFlag is on, the precedence will be Chrome->Edge. Defaults to False.
            useEdge (bool, optional): In case useChrome flag is not True, will be used Edge. Defaults to True.
            showAlerts (bool, optional): Some alerts will display, but you can turn of this when you know what this do. Defaults to True.
        """
        self.url_orders = "https://www.aliexpress.com/p/order/index.html"
        self.driver = None
        self.chrome_options = None
        self.service = None
        self.driverType = ""
        self.showAlerts = showAlerts
        if localUser == "":
            self.localUser = os.getlogin()
        else:
            self.localUser = localUser
            
        if user_data_dir == "":
            print("User data dir not provided, using default")

            if useChrome:
                useEdge = False
                self.user_data_dir = "C:/Users/"+self.localUser+"/AppData/Local/Google/Chrome/User Data"
                self.driverType = "chrome"
            #edge
            if useEdge:
                self.user_data_dir = "C:/Users/"+self.localUser+"/AppData/Local/Microsoft/Edge/User Data"
                self.driverType = "edge"
            
        else:
            self.user_data_dir = user_data_dir
            
        
            
        print(f"Actual user: {self.localUser}")
        print(f"User data dir: {self.user_data_dir}")
        
        self.orders = []
        self.items=[]
        
        load_dotenv()
        
        
    def setEnviroment(self, headless:bool=False):
        """Run program on headlessmode

        Args:
            headless (bool, optional): You can try to load this scrapper on headless mode, this will run in background. Defaults to False.
        """
        
        #close all instance
        self.driver_options = None
        self.service = None
        selected = None
        if self.driverType == "chrome":
            if self.showAlerts:
               selected = messagebox.askokcancel("Warning", "I need to close all Chrome instances, please save your work...")
               
            if selected == False:
                exit()
            
            os.system("taskkill /f /im chrome.exe")
            self.driver_options = webdriver.ChromeOptions()        
            self.service = Service("./chromedriver.exe")
            
        elif self.driverType == "edge":
            if self.showAlerts:
                selected = messagebox.askokcancel("Warning", "I need to close all Microsoft Edge instances, please save your work...")
            if selected == False:
                exit()
            os.system("taskkill /f /im msedge.exe")
            self.driver_options = webdriver.EdgeOptions()
        
    
        self.driver_options.add_argument("--user-data-dir="+self.user_data_dir)
        self.driver_options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver_options.add_experimental_option("useAutomationExtension", False)
        self.driver_options.add_experimental_option("excludeSwitches",["enable-automation"])
        self.driver_options.add_experimental_option("excludeSwitches",["enable-logging"])
        #add headless
        if headless:
            self.driver_options.add_argument("--headless")
        else:
            #maximize driver
            self.driver_options.add_argument("--start-maximized")
        
        if self.driverType == "chrome":
            self.driver = webdriver.Chrome(
                service=self.service,
                options=self.driver_options
            )
        
        elif self.driverType == "edge":
            self.driver = webdriver.Edge(
                options=self.driver_options
            )

    def getOrders(self, category:str="Shipped", max_orders:int=-1, asJson:bool=False, requireToLogin:bool=False, page_zoom:int=75)->list:
        """Get orders from Aliexpress and store them in a list based on the category provided (Shipped, To Pay, Processed, View All) and the max_orders to get
        In case of requireToLogin, the user will need to login to Aliexpress and press Enter to continue

        Args:
            category (str, optional): On english can be (Shipped, To Pay, Processed, View All). Defaults to "Shipped".
            max_orders (int, optional): Define the number of orders to bring back or load. Defaults to -1.
            asJson (bool, optional): In case json structure needed to be returned. Defaults to False.
            requireToLogin (bool, optional): In case no userdata where loaded you will need to login first. Defaults to False.

        Returns:
            list: return a list of orders
        """
        if self.driver == None:
            print("Driver not set, please set enviroment first")
            return []
        
        self.driver.get(self.url_orders)
        
        if requireToLogin:
            print("Please login to Aliexpress and press Enter to continue...")
            input()
            
            self.driver.get(self.url_orders)
        
        #categorias (View All, To Pay, Shipped, Processed)
        div_categorias = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "comet-tabs-nav")
        )
        
        lista_categorias = div_categorias.find_elements(By.CLASS_NAME, "comet-tabs-nav-item")
        for categoria in lista_categorias:
            if str(categoria.text).startswith(category):
                categoria.click()
                sleep(2)
                break
        
        element_count = 0
        while True:
            items_loaded = self.driver.find_elements(By.CLASS_NAME, "order-item")
            element_count = len(items_loaded)
            if element_count >= max_orders and max_orders != -1:
                break
            
            div_more = None
            try:
                div_more = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                    lambda d: d.find_element(By.CLASS_NAME, "order-more")
                )
            except:
                print("No more orders to load")
                break
            
            if div_more == None:
                print("No more orders to load")
                break
            
            button_viewOrders = div_more.find_element(By.CLASS_NAME, "comet-btn")
            
            if button_viewOrders != None:
                self.driver.execute_script("arguments[0].scrollIntoView();", button_viewOrders)
                self.driver.execute_script("arguments[0].click();", button_viewOrders)
                # button_viewOrders.click()
                sleep(4)
            
        #wait for the page to load
        
        order_container = self.driver.find_elements(By.CLASS_NAME, "order-item")
        print(f"Orders detected at {category} : {len(order_container)}")
        
        #print bar progress
        
        for order_item in order_container[:max_orders]:
            #print progress bar for each order with percentage
            # print(f"Fetching Orders: {order_container.index(order_item)+1}/{len(order_container)}", end="\r")
            print(f"Fetching Orders: {round(((order_container.index(order_item)+1)/len(order_container))*100,2)}%", end="\r")
            orden ={
                "order_id": "",
                "order_date": "",
                "shop_name": "",
                "product_name": "",
                "product_price": "",
                "product_quantity": "",
                "total_price": "",
                "status": "",
                "tracking_link": "",
                "tracking_number": "",
                "tracking_status": "",
                "tracking_process": "",
                "image_references": [], #almacenara urls de imagenes
                "property":""
            }   
            
            #informacion de fecha y id de orden
            order_item_header = order_item.find_element(By.CSS_SELECTOR,"div[data-pl='order_item_header_info']")
            if order_item_header != None:
                elements = order_item_header.find_elements(By.TAG_NAME, "div")
                for e in elements:
                    if str(e.text).startswith("Order ID"):
                        orden["order_id"] = e.text.split(":")[1].strip().replace("\nCopy", "")
                    if str(e.text).startswith("Order date"):
                        orden["order_date"] = e.text.split(":")[1].strip()
            
            #order status text
            order_status = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-header-status-text']")
            if order_status != None:
                orden["status"] = order_status.text
                
            #order shop text
            order_shop = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-store-name']")
            if order_shop != None:
                orden["shop_name"] = order_shop.text
            
            #order total price
            order_total_price = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-content-opt-price-total']")
            if order_total_price != None:
                price = order_total_price.text
                if price.startswith("Total:"):
                    orden["total_price"] = price.split(":")[1].strip()
                    
            ##buscar imagenes de referencia
            order_item_images = order_item.find_elements(By.CSS_SELECTOR, "div[class='order-item-content-img']")
            #url se encuentra dentro del style
            for img in order_item_images:
                style = img.get_attribute("style")
                url = style.split("(")[1].split(")")[0].replace("\"", "")
                
                # orden["image_references"].append(url.replace("\"", ""))
                
                img_save_path = f"./img/{orden['order_id']}/"
                if not os.path.exists(img_save_path):
                    os.makedirs(img_save_path)
                
                index_img = order_item_images.index(img)
                img_path = img_save_path + f"img_{index_img}.png"

                #check if exists
                if not os.path.exists(img_path):
                    orden["image_references"].append(self.downloadImage(url, img_path))
                else:
                    orden["image_references"].append(img_path)
            
            
            #find order detail link
            order_detail = order_item.find_element(By.CSS_SELECTOR, "a[data-pl='order_item_header_detail'")
            order_url = order_detail.get_attribute("href")
            
            
            #save order detail screenshot
            order_detail_save_path = f"./detail/"
            if not os.path.exists(order_detail_save_path):
                os.makedirs(order_detail_save_path)
                
            detail_path = order_detail_save_path + str(orden['order_id'])+"_detail.png"
            # if not os.path.exists(detail_path):
            self.saveOrderScreenshot(url=order_url, save_path=detail_path,zoom=page_zoom)
            
            if len(orden["image_references"]) == 1:
                #obtener el nombre ya que si aparece
                nombre_producto = ""
                order_product_name = order_item.find_element(By.CSS_SELECTOR, "div[class='order-item-content-info-name']")
                if order_product_name != None:
                    orden["product_name"] = str(order_product_name.text).strip()[0:50]
                
                try:
                    order_product_sku = order_item.find_element(By.CSS_SELECTOR, "div[class='order-item-content-info-sku']")
                    if order_product_sku != None:
                        orden["product_sku"] = str(order_product_sku.text).strip()
                        
                    nombre_producto = str(orden["product_name"])[0:50] + " - "  + orden["product_sku"]
                    orden["product_name"] = nombre_producto
                except:
                    
                    pass
                    
                
                order_product_price = order_item.find_element(By.CSS_SELECTOR, "div[class='es--wrap--2p8eS4Q notranslate']")
                if order_product_price != None:
                    orden["product_price"] = str(order_product_price.text).strip()
                
                order_product_quantity = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-content-info-number-quantity']")
                if order_product_quantity != None:
                    orden["product_quantity"] = str(order_product_quantity.text).replace("x", "").strip()
            else:
                orden["product_name"] = "Multiple Products"
                orden["product_quantity"] = str(len(orden["image_references"]))
            
            #get the tracking link
            order_buttons = order_item.find_elements(By.CLASS_NAME, "order-item-btns")
            for button in order_buttons:
                if "track order" in button.text.lower():
                    orden["tracking_link"] = button.find_element(By.TAG_NAME, "a").get_attribute("href")
        
                
            #get trackin link info
            if orden["tracking_link"] != "":
                tracking_info = self.getTrackingNumber(orden["tracking_link"])
                orden["tracking_number"] = tracking_info["tracking_number"]
                orden["tracking_status"] = tracking_info["tracking_status"]    
                orden["tracking_process"] = tracking_info["tracking_process"]

                
            else:
                orden["tracking_number"] = "No tracking number"
                orden["tracking_status"] = "No tracking status"
                orden["tracking_process"] = "No tracking process"
                
            self.orders.append(orden)
        
        if asJson:
            return json.dumps(self.orders, indent=4)    
    
        return self.orders
    
    def getOrdersNew(self, category:str="Shipped", max_orders:int=-1, asJson:bool=False, requireToLogin:bool=False, page_zoom:int=75)->list:
        """Get orders from Aliexpress and store them in a list based on the category provided (Shipped, To Pay, Processed, View All) and the max_orders to get
        In case of requireToLogin, the user will need to login to Aliexpress and press Enter to continue

        Args:
            category (str, optional): On english can be (Shipped, To Pay, Processed, View All). Defaults to "Shipped".
            max_orders (int, optional): Define the number of orders to bring back or load. Defaults to -1.
            asJson (bool, optional): In case json structure needed to be returned. Defaults to False.
            requireToLogin (bool, optional): In case no userdata where loaded you will need to login first. Defaults to False.

        Returns:
            list: return a list of orders
        """
        if self.driver == None:
            print("Driver not set, please set enviroment first")
            return []
        
        self.driver.get(self.url_orders)
        
        if requireToLogin:
            print("Please login to Aliexpress and press Enter to continue...")
            input()
            
            self.driver.get(self.url_orders)
        
        #categorias (View All, To Pay, Shipped, Processed)
        div_categorias = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "comet-tabs-nav")
        )
        
        lista_categorias = div_categorias.find_elements(By.CLASS_NAME, "comet-tabs-nav-item")
        for categoria in lista_categorias:
            if str(categoria.text).startswith(category):
                categoria.click()
                sleep(2)
                break
        
        element_count = 0
        
        ##load orders till max_orders
        while True:
            items_loaded = self.driver.find_elements(By.CLASS_NAME, "order-item")
            element_count = len(items_loaded)
            if element_count >= max_orders and max_orders != -1:
                break
            
            div_more = None
            try:
                div_more = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                    lambda d: d.find_element(By.CLASS_NAME, "order-more")
                )
            except:
                print("No more orders to load")
                break
            
            if div_more == None:
                print("No more orders to load")
                break
            
            button_viewOrders = div_more.find_element(By.CLASS_NAME, "comet-btn")
            
            if button_viewOrders != None:
                self.driver.execute_script("arguments[0].scrollIntoView();", button_viewOrders)
                self.driver.execute_script("arguments[0].click();", button_viewOrders)
                # button_viewOrders.click()
                sleep(4)
            
        #wait for the page to load
        
        order_container = self.driver.find_elements(By.CLASS_NAME, "order-item")
        print(f"Orders detected at {category} : {len(order_container)}")
        
        #print bar progress
        
        for order_item in order_container[:max_orders]:
            order_items = []
            #orders has same order date, order id, and track_link
            #print progress bar for each order with percentage
            # print(f"Fetching Orders: {order_container.index(order_item)+1}/{len(order_container)}", end="\r")
            print(f"Fetching Orders: {round(((order_container.index(order_item)+1)/len(order_container))*100,2)}%", end="\r")
            
            orden ={
                "order_id": "",
                "order_date": "",
                "shop_name": "",
                "product_name": "",
                "product_price": "",
                "product_quantity": "",
                "total_price": "",
                "status": "",
                "tracking_link": "",
                "tracking_number": "",
                "tracking_status": "",
                "tracking_process": "",
                "image_references": [], #almacenara urls de imagenes
                "property":""
            }   
            
            #informacion de fecha y id de orden
            order_item_header = order_item.find_element(By.CSS_SELECTOR,"div[data-pl='order_item_header_info']")
            if order_item_header != None:
                elements = order_item_header.find_elements(By.TAG_NAME, "div")
                for e in elements:
                    if str(e.text).startswith("Order ID"):
                        orden["order_id"] = e.text.split(":")[1].strip().replace("\nCopy", "")
                    if str(e.text).startswith("Order date"):
                        orden["order_date"] = e.text.split(":")[1].strip()
            
            #order status text
            order_status = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-header-status-text']")
            if order_status != None:
                orden["status"] = order_status.text
                
            #order shop text
            order_shop = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-store-name']")
            if order_shop != None:
                orden["shop_name"] = order_shop.text
            
            #order total price
            order_total_price = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-content-opt-price-total']")
            if order_total_price != None:
                price = order_total_price.text
                if price.startswith("Total:US $"):
                    orden["total_price"] = price.split("$")[1].strip()
                                
            #find order detail link
            order_detail = order_item.find_element(By.CSS_SELECTOR, "a[data-pl='order_item_header_detail'")
            order_url = order_detail.get_attribute("href")
            
            detail_path = f"./detail/{orden['order_id']}_detail.png"
            
            
            # if not os.path.exists(detail_path):
            screenshot = self.saveOrderScreenshot(url=order_url, save_path=detail_path,zoom=page_zoom)
            
            order_subtotal = 0
            for s in screenshot["products"]:
                order_subtotal += float(s["product_price"]) * int(s["product_quantity"])
        
            
            
            for s in screenshot["products"]:
                orden["product_name"] = s["product_name"]
                orden["product_price"] = s["product_price"]
                orden["product_quantity"] = s["product_quantity"]
                orden["product_sku"] = s["product_sku"]
                orden["product_final_price"] = s["product_final_price"]
                orden["product_delivery_date"] = s["product_delivery_date"]
                orden["product_tracking_info"] = s["product_tracking_info"]
                orden["image_references"] = s["image_references"]
                #para calcular el total de la orden
                
                # (product_price * product_quantity / subtotal ) * total_price ) 
                orden["product_final_price"] = round((float(s["product_price"]) * int(s["product_quantity"]) / order_subtotal) * float(orden["total_price"]),2)
                
                if orden["product_tracking_info"] != "No tracking info":
                    orden["tracking_number"] = s["product_tracking_info"]["tracking_number"]
                    orden["tracking_status"] = s["product_tracking_info"]["tracking_status"]
                    orden["tracking_process"] = s["product_tracking_info"]["tracking_process"]
                else:
                    orden["tracking_number"] = "No tracking number"
                    orden["tracking_status"] = "No tracking status"
                    orden["tracking_process"] = "No tracking process"
                
                self.orders.append(orden)
        
        if asJson:
            return json.dumps(self.orders, indent=4)    
    
        return self.orders
    
    def getTrackingNumber(self, tracking_link:str, expectedItem:str, expectedSku:str)->dict:
        """Receive a tracking link and return the tracking number, status and process

        Args:
            tracking_link (str): tracking link/url

        Returns:
            dict: returns a dictionary with the tracking number, status and process
        """
        tracker_info = {
            "tracking_number": "",
            "tracking_status": "",
            "tracking_date": ""
        }
        #abrir nueva pestaña
        # if self.driver.window_handles:
        #     if len(self.driver.window_handles) > 1:
        #         self.driver.switch_to.window(self.driver.window_handles[2])
        #         self.driver.close()
        #         self.driver.switch_to.window(self.driver.window_handles[1])
        return_window =self.driver.current_window_handle
        self.driver.execute_script("window.open('');")
        actual_window = self.driver.window_handles.pop()
        self.driver.switch_to.window(actual_window)
        self.driver.get(tracking_link)
        
        #find if page has various packages
        try:
            tab_packages = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                lambda d: d.find_elements(By.CLASS_NAME, "tab-list-v2--tab--1o2e9r7")
            )
            for tp in tab_packages:
                if str(tp.text).lower().startswith("package"):
                    tp.click()
                    
                    #compare names
                    packaged_product = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                        lambda d: d.find_element(By.CLASS_NAME, "package-items-v2--productTitle--6090gOp")
                    ).text
                    
                    packaged_sku = ""
                    try:
                        packaged_sku = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                            lambda d: d.find_element(By.CLASS_NAME, "package-items-v2--skuText--2UwaJJO")
                        ).text
                        if packaged_product == expectedItem and str(packaged_sku).endswith(expectedSku):
                            #package number
                            print("Packaged and SKU match", tab_packages.index(tp))
                            break
                    except:
                        if packaged_product == expectedItem :
                        #package number
                            print("Only Packaged match", tab_packages.index(tp))
                            break     
        except:
            # packaged_product = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            #             lambda d: d.find_element(By.CLASS_NAME, "package-items-v2--productTitle--6090gOp")
            #         ).text
            # if packaged_product == expectedItem:
            #             #package number
            #     print("Packaged item found" )
                        
            pass
        
        
        number = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info-v2--mailNo--3TCkYIM")
        )
        tracker_info["tracking_number"] = str(number.text).replace("Tracking number:", "").replace("\nCopy","").strip()
        
        status = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info-v2--nodeDesc--2U3A3Yt")
        )
        tracker_info["tracking_status"] = str(status.text).strip()
        
        process = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info-v2--track--1nqL7Vl")
        )
        #save html
        process_txt = str(process.text).split("\n")
        
        #pass to an html tags
        process_html = "<div class=\"tracking-process\">"
        for p in process_txt:
            process_html += f"<p class=\"tracking-line\">{p}</p>"
        process_html += "</div>"
        
        
        tracker_info["tracking_process"] = process_html
        self.driver.close()
        self.driver.switch_to.window(return_window)

        return tracker_info
    
    def downloadImage(self, url:str, save_path:str)->str:
        """Download an image from a url and save it on the save_path

        Args:
            url (str): url of the image
            save_path (str): where should be saved the image
            
        Returns:
            str: return the save_path
        """
         #abrir nueva pestaña
        # if self.driver.window_handles:
        #     if len(self.driver.window_handles) > 1:
        #         self.driver.switch_to.window(self.driver.window_handles[2])
        #         self.driver.close()
        #         self.driver.switch_to.window(self.driver.window_handles[1])
        return_window = self.driver.current_window_handle
        self.driver.execute_script("window.open('');")
        actual_window = self.driver.window_handles.pop()
        self.driver.switch_to.window(actual_window)
        self.driver.get(url)
        
        #take screenshot of body
        body = self.driver.find_element(By.TAG_NAME, "img")
        body.screenshot(save_path)
        self.driver.close()
        self.driver.switch_to.window(return_window)
        
        return save_path
    
    def saveOrderScreenshot(self, url:str, save_path:str, zoom:int=75)->str:
        """Take a screenshot of the order detail for a specific order provided by the url

        Args:
            url (str): url of order detail
            save_path (str): where should be saved the screenshot
            zoom (int, optional): If order details doesnt display properly, page will need an adjust, with a 1920x1080 display 75% works fine. Defaults to 75.
            
        Returns:
            str: return the save_path
        """
        #abrir nueva pestaña
        
        obtainedInfo = {
            "save_path": save_path,
            "products": [],
            "order_total": "",
        }
        
        # if self.driver.window_handles:
        #     if len(self.driver.window_handles) > 1:
        #         self.driver.switch_to.window(self.driver.window_handles[1])
        #         self.driver.close()
        #         self.driver.switch_to.window(self.driver.window_handles[0])
        return_window = self.driver.current_window_handle
        self.driver.execute_script("window.open('');")
        actual_window = self.driver.window_handles.pop()
        self.driver.switch_to.window(actual_window)
        self.driver.get(url)
        self.driver.execute_script(f"document.body.style.zoom = '{zoom}%'")
        
        #find expand details button
    # try:
    
        order_price_div = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "div[class='order-price']")
        )
        expand = order_price_div.find_element(By.CSS_SELECTOR, "span[class='comet-icon comet-icon-arrowdown switch-icon']")
            
        
        self.driver.execute_script("arguments[0].style.border = '3px solid red';", expand)
        self.driver.execute_script("arguments[0].scrollIntoView();", expand)
        self.driver.execute_script("arguments[0].click();", expand)
        # expand.click()
        # self.driver.execute_script("arguments[0].click();", expand)
        sleep(1)
        #save screenshot on url
        
        order_detail_info_item = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "div[class='order-detail-info-item']")
        )
        
        self.driver.execute_script("arguments[0].scrollIntoView();", order_detail_info_item)
        order = self.driver.find_element(By.TAG_NAME, "body")
        #save screenshot
        order.screenshot(save_path)
        
        
        store_name_container = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CSS_SELECTOR, "span[class='store-name']")
        )
        store_name = store_name_container.text
        
        order_products = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "div[class='order-detail-item-content-wrap']")
        )
        
        order_info = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_elements(By.CSS_SELECTOR, "div[class='info-row']")
        )
        order_id = ""
        for info in order_info:
            if info.text.startswith("Order ID"):
                order_id = info.text.split(":")[1].replace("Copy","").strip()
                break
            
        
        
        
        
        order_total_price = ""
        for op in order_products:
            # print("Product found ", order_products.index(op))  
            product = {
                "product_name": "",
                "product_price": "",
                "product_quantity": "",
                "product_sku": "",
                "product_final_price": "",
                "product_delivery_date": ""
                
            }
            
            product_name = op.find_element(By.CSS_SELECTOR, "div[class='item-title']").text
            product["product_name"] = product_name
            
            
            
            product_quantity = op.find_element(By.CSS_SELECTOR, "span[class='item-price-quantity']").text
            product["product_quantity"] = product_quantity.replace("x", "").strip()
            
            product_price = op.find_element(By.CSS_SELECTOR, "div[class='item-price']").text
            product["product_price"] = product_price.replace("$","").replace("US","").replace(product_quantity, "").strip()
            try:
                
                product_sku = op.find_element(By.CSS_SELECTOR, "div[class='item-sku-attr']").text
                product["product_sku"] = product_sku
            except:
                product["product_sku"] = ""
                
            try:
                product_delivery_date = op.find_element(By.CSS_SELECTOR, "div[class='order-detail-item-track-eta-text']").text
                product["product_delivery_date"] = product_delivery_date.replace("Estimated delivery date: ", "").strip()
            except:
                product["product_delivery_date"] = ""
            
            
            #image
            ##buscar imagenes de referencia
            order_item_images = op.find_elements(By.CSS_SELECTOR, "a[class='order-detail-item-content-img']")
            #url se encuentra dentro del style
            img = order_item_images[0]
            style = img.get_attribute("style")
            url = style.split("(")[1].split(")")[0].replace("\"", "")
            
            # orden["image_references"].append(url.replace("\"", ""))
            
            img_save_path = f"./img/{order_id}/"
            if not os.path.exists(img_save_path):
                os.makedirs(img_save_path)
            
            index_img = order_item_images.index(img)
            img_path = img_save_path + f"img_{index_img}.png"

            #check if exists
            if not os.path.exists(img_path):
                product["image_references"]= self.downloadImage(url, img_path)
            else:
                product["image_references"] = img_path
            #scrap tracking info
            try:
                tracking_link = op.find_element(By.CSS_SELECTOR, "a[class='order-detail-item-track-info track-detail']").get_attribute("href")
                product["product_tracking_info"] = self.getTrackingNumber(tracking_link, product_name, product["product_sku"])
            except:
                product["product_tracking_info"] = "No tracking info"
            
            obtainedInfo["products"].append(product)
            
            
            
                
        self.driver.close()
        self.driver.switch_to.window(return_window)
        return obtainedInfo
        
    # except:
    #     self.driver.switch_to.window(self.driver.window_handles[0])
    #     return "error_saving_order"
        
    
    def exportOrders(self, filename:str="orders.json")->bool:
        """In case needed as to export data to server or other utilities, you can export the orders to a json file

        Args:
            filename (str, optional): Path where file should be saved. Defaults to "orders.json".

        Returns: True if file was saved
        """
        if len(self.orders) == 0:
            print("No orders to export")
            return False
        
        
        with open(filename, "w") as file:
            json.dump(self.orders, file, indent=4)
            print(f"Orders exported to {filename}")
            return True
    
    def printTrackByOrderList(self,orderList:list=[], fromFile:bool=False, filePath:str="orders.json", export:bool=True)->bool:
        """Print the tracking numbers of the orders in the orderList provided, the tracking numbers will be printed and saved in a txt file if export is True

        Args:
            orderList (list, optional): Order string lists. Defaults to [].
            fromFile (bool, optional): In case you need to use a file instead self program. Defaults to False.
            filePath (str, optional): In case you use fromFile a filePath will be required by default it uses sames as last generated. Defaults to "orders.json".
            export (bool, optional): In cases export needed, will be saved on root directory. Defaults to True.

        Returns: True if tracking numbers were printed
            
        """
        print("Printing tracking numbers")
        fileData = []
        if len(orderList) == 0:
            print("No orders to print")
            return False
        
        data = []
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
            
        if len(data) == 0:
            print("No orders to print")
            return False
        
        for o in orderList:
            for d in data:
                if d["order_id"] == str(o):
                    # data.remove(d)
                    print(f"{d['tracking_number']}")
                    fileData.append(d['tracking_number'])
                    break
        if export:
            with open("tracking_numbers.txt", "w") as file:
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(f"Generated on: {date}\n")
                for d in fileData:
                    file.write(f"{d}\n")
                # json.dump(fileData, file, indent=4)
                file.write("----------------------")
                
        print("----------------------")
        return True
    
    def printTrackingStatusByOrderList(self,orderList:list=[], fromFile:bool=False, filePath:str="orders.json", export:bool=True)->bool:
        """Return the tracking status of the orders in the orderList provided, the status will be printed and saved in a txt file if export is True

        Args:
            orderList (list, optional): Order string lists. Defaults to [].
            fromFile (bool, optional): In case you need to use a file instead self program. Defaults to False.
            filePath (str, optional): In case you use fromFile a filePath will be required by default it uses sames as last generated. Defaults to "orders.json".
            export (bool, optional): In cases export needed, will be saved on root directory. Defaults to True.

        Returns: True if tracking status were printed
        """
        print("Printing tracking status...")
        if len(orderList) == 0:
            print("No orders to print")
            return False
        
        data = []
        fileData = []
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
            
        if len(data) == 0:
            print("No orders to print")
            return False
        
        counter = -1
        for o in orderList:
            counter += 1
            for d in data:
                if d["order_id"] == str(o):
                    # data.remove(d)
                    print(f"{d['tracking_status']}")
                    fileData.append(d['tracking_status'])
                    break
        if export:
            with open("tracking_status.txt", "w") as file:
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(f"Generated on: {date}\n")
                for d in fileData:
                    file.write(f"{d}\n")
                # json.dump(fileData, file, indent=4)
                file.write("----------------------")
        print("----------------------")
        
        return True
    
    def printTrackingStatusByTrackingNumber(self, trackingList:list=[], fromFile:bool=False, filePath:str="orders.json", export:bool=True)->bool:
        """Return the tracking status of the orders in the orderList provided, the status will be printed and saved in a txt file if export is True

        Args:
            orderList (list, optional): Order string lists. Defaults to [].
            fromFile (bool, optional): In case you need to use a file instead self program. Defaults to False.
            filePath (str, optional): In case you use fromFile a filePath will be required by default it uses sames as last generated. Defaults to "orders.json".
            export (bool, optional): In cases export needed, will be saved on root directory. Defaults to True.

        Returns: True if tracking status were printed
        """
        print("Printing tracking status...")
        if len(trackingList) == 0:
            print("No orders to print")
            return False
        
        data = []
        fileData = []
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file) 
                
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
            
        if len(data) == 0:
            print("No orders to print")
            return False
        
        counter = -1
        for o in trackingList:
            counter += 1
            for d in data:
                if d["tracking_number"] == str(o):
                    # data.remove(d)
                    print(f"{d['tracking_status']}")
                    fileData.append(d['tracking_status'])
                    break
        if export:
            with open("tracking_status.txt", "w") as file:
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                file.write(f"Generated on: {date}\n")
                for d in fileData:
                    file.write(f"{d}\n")
                # json.dump(fileData, file, indent=4)
                file.write("----------------------")
        print("----------------------")
        
        return True
        
    def pushOrdersToServer(self, fromFile:bool=False, filePath:str="orders.json")->bool:
        """If you need to push orders to a server, you can use this method to push the orders to a server, modify the url from .env file on root directory

        Args:
            fromFile (bool, optional): In case you need to push data from a file. Defaults to False.
            filePath (str, optional): If fromFile flag is True, you need to provide the filePath. Defaults to "orders.json".

        Returns: True if orders were pushed 
        """
        #make a post request to mr8ugger.pythonanywhere.com/aliOrdersUpdate
        data = []
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                    
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to push")
                return False
        
        if len(data) == 0:
            print("No orders to push")
            return False
        
        #make the post request
        print("Pushing orders to server...")
        url = os.getenv("ALI_ORDERS_UPDATE")
        try:
            post_response = requests.post(url, json={"ali_orders":data, "date":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
        except:
            print("Error pushing orders")
            return False
        print("Status: "+str(post_response.status_code))
        return True
    

    
    
    def generateOrderDetailPDF(self, orderList:list=[], fromFile:bool=False, filePath:str="orders.json")->bool:
        #will group orders by tracking number and generate a pdf for each tracking number with png images
        
        data = []
        fileData = []
        groups = {}
        
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
            
        if len(data) == 0:
            print("No orders to print")
            return False
        
        #fill orderList with orders from file
        orderList = []
        for d in data:
            orderList.append(d["order_id"])
            
        if len(orderList) == 0:
            print("No orders number received, please provide a list of orders")
            
        for o in orderList:
            for d in data:
                if d["order_id"] == str(o):
                    if str(d["tracking_number"]) not in groups:
                        groups[str(d["tracking_number"])] = {
                            "captures":[],
                            "last_status":d["tracking_status"]
                        }
                        
                    groups[str(d["tracking_number"])]["captures"].append(str(o)+"_detail.png")        
                    groups[str(d["tracking_number"])]["last_status"] = d["tracking_status"]
                    
                    fileData.append(d['tracking_status'])
                    break
        print("----------------------")
        #generate pdfs
        for key in groups:
            
            print(f"Generating PDF order detail for {key}")
            
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True,margin=15)
            pdf.set_font("Arial", size=11)
            pdf.add_page()
            pdf.set_fill_color(200, 220, 255)
            pdf.set_text_color(0)
            pdf.set_draw_color(0)
            pdf.set_line_width(0.3)
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, f"Tracking: {key}", 0, 1, "C")
            pdf.set_font("Arial", "B", 10)
            pdf.cell(50, 10, f"Orders: {len(groups[key]["captures"])}", 1, 0, "C",1)
            pdf.cell(70, 10, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 1, 1, "C")
            pdf.set_font("Arial", "", 8)
            pdf.cell(70, 10, f"Last Status: {groups[key]['last_status']}", 0, 1, "T")
            pdf.cell(70, 10, "Nota: Los articulos que se encuentran en este documento pertenecen al mismo numero de tracking. ", 0, 1, "T")
            pdf.set_font("Arial", "B", 10)
            pdf.set_fill_color(200, 220, 255)
            # pdf.cell(50, 10, "Order", 1, 0, "C", 1)
            # pdf.cell(50, 10, "Detail", 1, 1, "C", 1)
            pdf.set_fill_color(255, 255, 255)
            pdf.set_font("Arial", "", 10)
            for img in groups[key]["captures"]:
                if groups[key]["captures"].index(img) % 2 == 0 and groups[key]["captures"].index(img) != 0:
                    pdf.add_page()
                #two per page
                pdf.cell(100, 10, "Tracking: " + key, 1, 0, "C")
                pdf.cell(60, 10,"Orden: " + img.split("_")[0], 1, 1, "C")
                
                # pdf.cell(40, 10, img, 1, 1, "C")
                # pdf.ln(10)
                pdf.image(f"./detail/{img}", x=10, w=190)
                pdf.ln(10)
                
            
            pdf.output(f"./pdf/{key}.pdf")
        print("----------------------")
        
        return True
    
    def generateExcelData(self, fromFile:bool=False, filePath:str="orders.json")->bool:
        #will pass the data to an excel file, using attributes as columns with pandas
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                    
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
        #generate excel file
        
        df = pd.DataFrame(data)
        df.to_excel("orders.xlsx", index=False)
        if os.path.exists("orders.xlsx"):
            print("Excel Orders file generated")
        return True
    
    def generateExcelByOrder(self, orderList:list=[], fromFile:bool=False, filePath:str="orders.json")->bool:
        #will pass the data to an excel file, using attributes as columns with pandas
        if fromFile:
            if filePath != "":
                with open(filePath, "r") as file:
                    data = json.load(file)
                    
        else:
            data = self.orders
            if len(data) == 0:
                print("No orders to print")
                return False
            
        #generate excel file
        data_set = []
        for o in orderList:
            for d in data:
                if d["order_id"] == str(o):
                    # data.remove(d)
                    data_set.append({"order_id":d["order_id"],"tracking_number":d["tracking_number"], "tracking_status":d["tracking_status"]})
                    break
                
        df = pd.DataFrame(data_set)
        df.to_excel("orders_status.xlsx", index=True)
        if os.path.exists("orders_status.xlsx"):
            print("Excel Order Status file generated")
        return True
    
    
    
            
        
ali = AliHelper(showAlerts=False) 
# #PARA ACTUALIZAR INFO
ali.setEnviroment(headless=False)
ali.getOrdersNew(category="Shipped", max_orders=11, page_zoom=75)
ali.exportOrders("orders.json")


# orderList =[8197887115647491,8197887115667491,8197887115687491,8197887115547491,8197887115707491,8197887115727491,8197887115567491,8197887115747491,8197887115607491,8197887115767491,8197887115587491,8197472202557491,8197472202577491,8197472202597491,8197472202617491,8197472202637491,8197472202657491,8197887115627491,8197472202677491,8196809692487491]
orderList = [8198008051977491,8198008051997491,8198008052017491,8198008052037491,8198008052057491,8198008052077491,8198008051937491,8198008052097491,8198008051957491,8197254807227491,8198008052117491]
# trackingList = []


ali.printTrackByOrderList(orderList=orderList, fromFile=True)
ali.printTrackingStatusByOrderList(orderList=orderList, fromFile=True)
# ali.printTrackingStatusByTrackingNumber(trackingList=trackingList, fromFile=True)
ali.generateOrderDetailPDF(orderList=orderList, fromFile=True, filePath="orders.json")
# ali.pushOrdersToServer(fromFile=True)
ali.generateExcelData(fromFile=True)
ali.generateExcelByOrder(orderList=orderList, fromFile=True)

# tracking_numbers=["420331729212490362719153543181","LQ835416399CN","LP00671472073489","LR152035762CN","CNUSUP00003994120","CNUSUP00004010899"]
# ali.printTrackingStatusByTrackingNumber(trackingList=tracking_numbers, fromFile=True)
# #PARA IMPRIMIR TRACKING
# # # input("Press Enter to continue...")

