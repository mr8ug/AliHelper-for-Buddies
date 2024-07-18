function loadLocal() {
    //load json from root folder
    fetch('orders.json')
        .then(response => response.json())
        .then(data => {
            data.sort((a, b) => {
                if (a.tracking_number < b.tracking_number) {
                    return -1;
                }
                if (a.tracking_number > b.tracking_number) {
                    return 1;
                }
                return 0;
            });

            // data.map((order) => {
            //     // console.log(order);

            //     let order_html = `
            //     <div class="order-item order-${order.order_id}">
            //         <div class="order-base order-${order.order_id}">
            //             <div class="order-info order-${order.order_id}">
            //                 <div class="order-id order-${order.order_id}">Order ID: ${order.order_id}</div>
            //                 <div class="order-date order-${order.order_id}">Order Date: ${order.order_date}</div>
            //             </div>

            //             <div class="order-product order-${order.order_id}">
            //                 <div class="order-product-name order-${order.order_id}">Product: ${order.product_name}</div>
            //                 <div class="order-ali-status order-${order.order_id}">Total: ${order.total_price}</div>
            //             </div>
            //         </div>

            //         <div class="order-images order-${order.order_id}">
            //             ${order.image_references.map((image, index) => {
            //         return `<img class="order-item-content-img" src="${image}" alt="product image ${order.order_id + "-" + index}"></img>`
            //     }).join('')}
            //         </div>

            //         <div class="order-track order-${order.order_id}">
            //             <div class="order-status order-${order.order_id}">AliExpress Status: ${order.status}</div>
            //             <div class="order-tracking order-${order.order_id}"><strong>Tracking: <a href="https://t.17track.net/es#nums=${order.tracking_number}">${order.tracking_number}</a></strong></div>
            //             <div class="order-tracking-status order-${order.order_id}">Tracking Status: ${order.tracking_status}</div>
            //         </div>
            //     </div>
            //     `;
            //     document.getElementById('order-list').innerHTML += order_html;
            // });




            let groupedOrders = data.reduce((groups, order) => {
                const key = order.tracking_number;
                if (!groups[key]) {
                    groups[key] = [];
                }
                groups[key].push(order);
                return groups;
            }, {});


            let orderListElement = document.getElementById('order-list');
            orderListElement.innerHTML = '';

            Object.keys(groupedOrders).forEach(tracking_number => {
                const orders = groupedOrders[tracking_number];

                let group_html = `<div class="order-group tracking-${tracking_number}">
                     <h5><a href="https://t.17track.net/es#nums=${tracking_number}">${tracking_number}</a></h5>`;

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
                                </div>
                            </div>

                            <div class="order-images order-${order.order_id}">
                                ${order.image_references.map((image, index) => {
                                        return `<img class="order-item-content-img" src="${image}" alt="product image ${order.order_id + "-" + index}"></img>`;
                                    }).join('')}
                            </div>

                            <div class="order-track order-${order.order_id}">
                                <div class="order-status order-${order.order_id}">AliExpress Status: ${order.status}</div>
                                <div class="order-tracking order-${order.order_id}"><strong>Tracking: <a href="https://t.17track.net/es#nums=${order.tracking_number}">${order.tracking_number}</a></strong></div>
                                <div class="order-tracking-status order-${order.order_id}">Tracking Status: ${order.tracking_status}</div>
                                
                            </div>
                            <div class="order-tracking-process"> ${order.tracking_process}</div>
                            
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
