function loadLocal() {
    //load json from root folder
    fetch('orders.json')
        .then(response => response.json())
        .then(data => {
            console.log(data); // Aquí puedes trabajar con los datos cargados
            let order_lenght = data.length;
            for (let i = 0; i < order_lenght; i++) {
                let order = data[i];
                let order_id = order.order_id;
                let order_date = order.order_date;
                let order_product = order.product_name;
                let order_ali_status = order.status;
                let order_status = order.status;
                let order_tracking = order.tracking_number;
                let order_tracking_status = order.tracking_status;
                let order_tracking_url = order.tracking_link;
                let images = order.image_references;

                let image_html = '';
                for (let j = 0; j < images.length; j++) {
                    image_html += `<div class="order-item-content-img" style="background-image: url(&quot;${String(images[j])}&quot;);" alt="product image ${order_id +"-"+ j}" ></div>`;
                }


                let order_html = `
                <div class="order-item order-${order_id}">
                    <div class="order-id">Order ID: ${order_id}</div>
                    <div class="order-date">Order Date: ${order_date}</div>
                    <div class="order-product-name">Customer: ${order_product}</div>
                    <div class="order-ali-status">Total: ${order_ali_status}</div>
                    <div class="order-status">AliStatus: ${order_status}</div>
                    <div class="order-tracking">Tracking: <a href="https://t.17track.net/es#nums=${order_tracking}">${order_tracking}</a></div>
                    <div class="order-tracking-status">Tracking Status: ${order_tracking_status}</div>
                    <div class="order-images">${image_html}</div>
                    
                </div>
                `;
                document.getElementById('order-list').innerHTML += order_html;
            }
        }
        )
        .catch(error => {
            console.error('Error al cargar el archivo JSON:', error);
        });
}
 