from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 356, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB HUB", "price": 649, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "pen set", "price": 199, "category": "Electronics", "in_stock": False}
]

feedback_list = []

class Feedback(BaseModel):
    customer_name: str
    product_id: int
    rating: int
    comment: Optional[str] = None

class Product(BaseModel):
    name: str
    price: int
    category: str
    in_stock: bool

class OrderItem(BaseModel):
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=1, le=50)

class BulkOrder(BaseModel):
    company_name: str = Field(..., min_length=2)
    contact_email: str = Field(..., min_length=5)
    items: List[OrderItem]


@app.get("/")
def home():
    return {"message": "Welcome to my store API"}


@app.get("/products")
def get_products():
    return {"products": products, "total": len(products)}


@app.get("/products/category/{category_name}")
def get_products_by_category(category_name: str):

    filtered = []

    for product in products:
        if product["category"].lower() == category_name.lower():
            filtered.append(product)

    return {"category": category_name, "products": filtered}


@app.post("/feedback")
def submit_feedback(feedback: Feedback):

    feedback_list.append(feedback.dict())

    return {
        "message": "Feedback added",
        "data": feedback,
        "total_feedback": len(feedback_list)
    }


@app.get("/products/instock")
def get_instock_products():

    instock = []

    for product in products:
        if product["in_stock"]:
            instock.append(product)

    return {"in_stock_products": instock, "count": len(instock)}


@app.get("/products/search/{keyword}")
def search_products(keyword: str):

    result = []

    for product in products:
        if keyword.lower() in product["name"].lower():
            result.append(product)

    return {"keyword": keyword, "results": result}


@app.get("/products/filter")
def filter_products(min_price: int = 0, max_price: int = 10000):

    result = []

    for product in products:
        if min_price <= product["price"] <= max_price:
            result.append(product)

    if len(result) == 0:
        return {"message": "No products found"}

    return {
        "filters": {"min_price": min_price, "max_price": max_price},
        "results": result
    }


@app.get("/products/summary")
def products_summary():

    total = len(products)
    instock = 0
    outstock = 0
    categories = set()

    most_expensive = products[0]
    cheapest = products[0]

    for p in products:

        categories.add(p["category"])

        if p["in_stock"]:
            instock += 1
        else:
            outstock += 1

        if p["price"] > most_expensive["price"]:
            most_expensive = p

        if p["price"] < cheapest["price"]:
            cheapest = p

    return {
        "total_products": total,
        "in_stock_count": instock,
        "out_of_stock_count": outstock,
        "most_expensive": {"name": most_expensive["name"], "price": most_expensive["price"]},
        "cheapest": {"name": cheapest["name"], "price": cheapest["price"]},
        "categories": list(categories)
    }


@app.get("/products/audit")
def products_audit():

    total_products = len(products)
    in_stock_count = 0
    out_stock_count = 0
    total_stock_value = 0

    most_expensive = products[0]

    for product in products:

        if product["in_stock"]:
            in_stock_count += 1
            total_stock_value += product["price"]
        else:
            out_stock_count += 1

        if product["price"] > most_expensive["price"]:
            most_expensive = product

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_stock_count,
        "total_stock_value": total_stock_value,
        "most_expensive_product": most_expensive["name"]
    }


@app.post("/products", status_code=201)
def add_product(product: Product):

    for p in products:
        if p["name"].lower() == product.name.lower():
            raise HTTPException(status_code=404, detail="Product already exists")

    new_id = len(products) + 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "in_stock": product.in_stock
    }

    products.append(new_product)

    return {"message": "Product added", "product": new_product}


@app.put("/products/{product_id}")
def update_product(product_id: int, price: Optional[int] = None, in_stock: Optional[bool] = None):

    for product in products:

        if product["id"] == product_id:

            if price is not None:
                product["price"] = price

            if in_stock is not None:
                product["in_stock"] = in_stock

            return {"message": "Product updated", "product": product}

    raise HTTPException(status_code=404, detail="Product not found")


@app.delete("/products/{product_id}")
def delete_product(product_id: int):

    for product in products:

        if product["id"] == product_id:
            products.remove(product)

            return {"message": f'{product["name"]} removed successfully'}

    raise HTTPException(status_code=404, detail="Product not found")


@app.put("/apply-discount")
def apply_discount(category: str, discount_percent: int):

    updated_products = []

    for product in products:

        if product["category"].lower() == category.lower():

            discount = product["price"] * discount_percent / 100
            product["price"] = int(product["price"] - discount)

            updated_products.append(product)

    return {
        "category": category,
        "discount_percent": discount_percent,
        "updated_products": updated_products
    }

@app.post("/orders/bulk")
def bulk_order(order: BulkOrder):

    confirmed = []
    failed = []
    grand_total = 0

    for item in order.items:

        product = None

        for p in products:
            if p["id"] == item.product_id:
                product = p
                break

        if product is None:

            failed.append({
                "product_id": item.product_id,
                "reason": "Product not found"
            })

        elif not product["in_stock"]:

            failed.append({
                "product_id": item.product_id,
                "reason": f"{product['name']} is out of stock"
            })

        else:

            subtotal = product["price"] * item.quantity
            grand_total += subtotal

            confirmed.append({
                "product": product["name"],
                "qty": item.quantity,
                "subtotal": subtotal
            })

    return {
        "company": order.company_name,
        "confirmed": confirmed,
        "failed": failed,
        "grand_total": grand_total
    }