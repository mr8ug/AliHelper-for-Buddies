import bs4 as bs
import selenium.webdriver as webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.service import Service

from time import sleep

import os
import json

class AliHelper:
    def __init__(self, localUser:str="", user_data_dir:str=""):
        self.url_orders = "https://www.aliexpress.com/p/order/index.html"
        self.driver = None
        self.chrome_options = None
        self.service = None
        if localUser == "":
            self.localUser = os.getlogin()
        else:
            self.localUser = localUser
            
        if user_data_dir == "":
            print("User data dir not provided, using default")
            self.user_data_dir = "C:/Users/"+self.localUser+"/AppData/Local/Google/Chrome/User Data"
        else:
            self.user_data_dir = user_data_dir
            
        
            
        print(f"Actual user: {self.localUser}")
        print(f"User data dir: {self.user_data_dir}")
        
        self.orders = []
        
        
    def setEnviroment(self):
        
        #close all instance
        os.system("taskkill /f /im chrome.exe")
        
        self.chrome_options = webdriver.ChromeOptions()        
        self.chrome_options.add_argument("--user-data-dir="+self.user_data_dir)
        self.chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        self.chrome_options.add_experimental_option("useAutomationExtension", False)
        self.chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])
        self.chrome_options.add_experimental_option("excludeSwitches",["enable-logging"])
        
        self.service = Service("./chromedriver.exe")
        
        self.driver = webdriver.Chrome(
            service=self.service,
            options=self.chrome_options
        )
        
    def getOrders(self, category:str="Shipped", max_orders:int=10, asJson:bool=False)->list:
        
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
            if element_count >= max_orders:
                break
            
            div_more = None
            try:
                div_more = WebDriverWait(self.driver, timeout=5, poll_frequency=1).until(
                    lambda d: d.find_element(By.CLASS_NAME, "order-more")
                )
            except:
                break
            
            if div_more == None:
                break
            
            button_viewOrders = div_more.find_element(By.CLASS_NAME, "comet-btn")
            
            if button_viewOrders != None:
                self.driver.execute_script("arguments[0].scrollIntoView();", button_viewOrders)
                self.driver.execute_script("arguments[0].click();", button_viewOrders)
                # button_viewOrders.click()
                sleep(4)
            
        #wait for the page to load
        
        order_items = self.driver.find_elements(By.CLASS_NAME, "order-item")
        print(f"Orders detected: {len(order_items)}")
        
        
        for order_item in order_items[:max_orders]:
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
                "image_references": [] #almacenara urls de imagenes
                
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
    
                
                orden["image_references"].append(self.downloadImage(url, img_path))
                    
            
            
            if len(orden["image_references"]) == 1:
                #obtener el nombre ya que si aparece
                nombre_producto = ""
                order_product_name = order_item.find_element(By.CSS_SELECTOR, "div[class='order-item-content-info-name']")
                if order_product_name != None:
                    orden["product_name"] = str(order_product_name.text).strip()
                
                try:
                    order_product_sku = order_item.find_element(By.CSS_SELECTOR, "div[class='order-item-content-info-sku']")
                    if order_product_sku != None:
                        orden["product_sku"] = str(order_product_sku.text).strip()
                        
                    nombre_producto = orden["product_name"] + " - "  + orden["product_sku"]
                        
                except:
                    nombre_producto = orden["product_name"]
                
                order_product_price = order_item.find_element(By.CSS_SELECTOR, "div[class='es--wrap--2p8eS4Q notranslate']")
                if order_product_price != None:
                    orden["product_price"] = str(order_product_price.text).strip()
                
                order_product_quantity = order_item.find_element(By.CSS_SELECTOR, "span[class='order-item-content-info-number-quantity']")
                if order_product_quantity != None:
                    orden["product_quantity"] = str(order_product_quantity.text).replace("x", "").strip()
            else:
                orden["product_name"] = "Multiple Products"
            
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

                self.orders.append(orden)
        
        if asJson:
            return json.dumps(self.orders, indent=4)    
    
        return self.orders
    
    def getTrackingNumber(self, tracking_link:str)->dict:
        tracker_info = {
            "tracking_number": "",
            "tracking_status": "",
            "tracking_date": ""
        }
        #abrir nueva pestaña
        if self.driver.window_handles:
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(tracking_link)
        
        
        number = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info--mailNo-pc--3cTqcXe")
        )
        tracker_info["tracking_number"] = str(number.text).replace("Tracking number", "").replace("\nCopy","").strip()
        
        status = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info--nodeDesc--Pa3Wnop")
        )
        tracker_info["tracking_status"] = str(status.text).strip()
        
        process = WebDriverWait(self.driver, timeout=10, poll_frequency=1).until(
            lambda d: d.find_element(By.CLASS_NAME, "logistic-info--track--WBcFzsd")
        )
        #save html
        tracker_info["tracking_process"] = process.get_attribute("outerHTML")
    
        self.driver.switch_to.window(self.driver.window_handles[0])

        return tracker_info
    
    def downloadImage(self, url:str, save_path:str):
         #abrir nueva pestaña
        if self.driver.window_handles:
            if len(self.driver.window_handles) > 1:
                self.driver.switch_to.window(self.driver.window_handles[1])
                self.driver.close()
                self.driver.switch_to.window(self.driver.window_handles[0])
                
        self.driver.execute_script("window.open('');")
        self.driver.switch_to.window(self.driver.window_handles[1])
        self.driver.get(url)
        
        #take screenshot of body
        body = self.driver.find_element(By.TAG_NAME, "img")
        body.screenshot(save_path)
        
        self.driver.switch_to.window(self.driver.window_handles[0])
        
        return save_path
    
    def exportOrders(self, filename:str="orders.json"):
        if len(self.orders) == 0:
            print("No orders to export")
            return False
        
        
        with open(filename, "w") as file:
            json.dump(self.orders, file, indent=4)
            print(f"Orders exported to {filename}")
            return True
        
        

ali = AliHelper()
ali.setEnviroment()
ali.getOrders(max_orders=39)
ali.exportOrders("orders.json")

# # input("Press Enter to continue...")