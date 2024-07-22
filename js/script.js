function loadLocal() {
    //load json from root folder
    //fetch from "http://mr8ugger.pythonanywhere.com/aliOrdersGet"

    fetch("https://mr8ugger.pythonanywhere.com/aliOrdersGet")
        .then(response => response.json())
        .then(data => {
            
            let orders = data.orders; //dictionary with orders
            //get all keys from dictionary
            
            //get all values from dictionary
            let values = Object.values(orders);
            //get all entries from dictionary

            ordersList = values.map((order, index) => {
                return {
                    order_id: order.order_id,
                    order_date: order.order_date,
                    product_name: order.product_name,
                    total_price: order.total_price,
                    product_quantity: order.product_quantity,
                    image_references: order.image_references,
                    status: order.status,
                    tracking_number: order.tracking_number,
                    tracking_status: order.tracking_status,
                    tracking_process: order.tracking_process
                };
            });
            ordersList.sort((a, b) => {
                if (a.tracking_number < b.tracking_number) {
                    return -1;
                }
                if (a.tracking_number > b.tracking_number) {
                    return 1;
                }
                return 0;
            });


            let groupedOrders = ordersList.reduce((groups, order) => {
                const key = order.tracking_number;
                if (!groups[key]) {
                    groups[key] = [];
                }
                groups[key].push(order);
                return groups;
            }, {});

            let button = document.getElementById('loadLocal');
            // button.style.display = 'none';

            //concat groups as group;group;group
            let trackingNumbers = Object.keys(groupedOrders).join(',');

            let orderListMenu = document.getElementById('order-list-menu');
            
            /*for each grouped Orders append into orderListMenu html an href to direct element*/
            orderListMenu.innerHTML = '';
            Object.keys(groupedOrders).forEach(tracking_number => {
                orderListMenu.innerHTML += `<li><a href="#${tracking_number}" class="order-list-menu-item">${tracking_number} (${groupedOrders[tracking_number].length})</a></li>`;
            });

            let orderListElement = document.getElementById('order-list');
            
            orderListMenu.innerHTML +=  '<li>'+ `<a href="https://t.17track.net/es#nums=${trackingNumbers}" target="_blank" id="allTracks">Rastrear todos</a><br>`;

            Object.keys(groupedOrders).forEach(tracking_number => {
                const orders = groupedOrders[tracking_number].sort((a, b) => {
                    if (a.order_id < b.order_id) {
                        return -1;
                    }
                    if (a.order_id > b.order_id) {
                        return 1;
                    }
                    return 0;
                });
                
                let group_html = `<div class="accordion-item order-group tracking-${tracking_number}" id="${tracking_number}">
                     <h5  class=" accordion-header text"><a href="https://t.17track.net/es#nums=${tracking_number}" target="_blank">${tracking_number} (${orders.length})</a></h5>`;
                    
                orders.forEach(order => {
                    group_html += `
                        <div class="order-item order-${order.order_id}">
                            <div class="order-base order-${order.order_id}">
                                <div class="order-info order-${order.order_id}">
                                    <div class="order-id order-${order.order_id}">Order ID: ${order.order_id}</div>
                                    <div class="order-date order-${order.order_id}">Order Date: ${order.order_date}</div>
                                    
                                </div>
                                
                                <div class="order-product order-${order.order_id}">
                                    <div class="order-product-name order-${order.order_id}">Product: ${order.product_name}</div>
                                    
                                    <div class="order-ali-status order-${order.order_id}"><strong>Total: ${order.total_price}</strong></div>
                                    <div class="order-ali-status order-${order.order_id}"><strong>Items: ${order.product_quantity}</strong></div>

                                </div>

                                
                            </div>

                            
                            <div class="order-images order-${order.order_id}">
                                ${order.image_references.map((image, index) => {
                                        return `<img class="order-item-content-img" src="${image}" alt="product image ${order.order_id + "-" + index}"></img>`;
                                    }).join('')}
                            </div>
                            
                            <div class="order-track order-${order.order_id}">
                                <div class="order-status order-${order.order_id}">AliExpress Status: ${order.status}</div>
                                <div class="order-tracking order-${order.order_id}"><strong>Tracking: ${order.tracking_number}</strong></div>
                                <div class="order-tracking-status order-${order.order_id}">Tracking Status: ${order.tracking_status}</div>
                            
                            
                            
                            </div>

                            ${order.tracking_process}
                            
                            
                        </div>
                        
        `;
                });

                group_html += `</div>`;
                orderListElement.innerHTML += group_html;
            });



        }
        )
        .catch(error => {
            console.error('Error al cargar el archivo JSON:', error);
        });
}
