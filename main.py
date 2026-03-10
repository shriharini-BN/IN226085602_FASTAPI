from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 599, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 99, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "Pen Set", "price": 49, "category": "Stationery", "in_stock": True},
    {"id": 4, "name": "USB Cable", "price": 199, "category": "Electronics", "in_stock": False},
    {"id": 5, "name": "Laptop Stand", "price": 1299, "category": "Electronics", "in_stock": True},
    {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "category": "Electronics", "in_stock": True},
    {"id": 7, "name": "Webcam", "price": 1899, "category": "Electronics", "in_stock": False}
]

class Feedback(BaseModel):
    customer_name: str
    product_id: int
    rating: int
    comment: Optional[str] = None

feedback_list = []

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
    filtered_products = []

    for product in products:
        if product["category"].lower() == category_name.lower():
            filtered_products.append(product)

    return {
        "category": category_name,
        "products": filtered_products
    }


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
        if product["in_stock"] == True:
            instock.append(product)

    return {
        "in_stock_products": instock,
        "count": len(instock)
    }


@app.get("/store/summary")
def store_summary():
    total = len(products)
    instock = 0
    outstock = 0
    categories = set()
    most_expensive = products[0]

    for product in products:
        categories.add(product["category"])

        if product["in_stock"]:
            instock += 1
        else:
            outstock += 1

        if product["price"] > most_expensive["price"]:
            most_expensive = product

    return {
        "total_products": total,
        "in_stock": instock,
        "out_of_stock": outstock,
        "categories": list(categories),
        "most_expensive_product": most_expensive["name"],
        "price": most_expensive["price"]
    }


@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    result = []

    for product in products:
        if keyword.lower() in product["name"].lower():
            result.append(product)

    return {
        "keyword": keyword,
        "results": result
    }


@app.get("/products/{product_id}/price")
def get_product_price(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return {
                "name": product["name"],
                "price": product["price"]
            }

    return {"error": "Product not found"}

@app.get("/products/summary")
def products_summary():

    total_products = len(products)
    in_stock_count = 0
    out_of_stock_count = 0
    categories = set()

    most_expensive = products[0]
    cheapest = products[0]

    for product in products:

        categories.add(product["category"])

        if product["in_stock"]:
            in_stock_count += 1
        else:
            out_of_stock_count += 1

        if product["price"] > most_expensive["price"]:
            most_expensive = product

        if product["price"] < cheapest["price"]:
            cheapest = product

    return {
        "total_products": total_products,
        "in_stock_count": in_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "most_expensive": {
            "name": most_expensive["name"],
            "price": most_expensive["price"]
        },
        "cheapest": {
            "name": cheapest["name"],
            "price": cheapest["price"]
        },
        "categories": list(categories)
    }

@app.get("/products/filter")
def filter_products(min_price: int = 0, max_price: int = 10000):

    result = []

    for product in products:
        if product["price"] >= min_price and product["price"] <= max_price:
            result.append(product)

    return {
        "filters": {
            "min_price": min_price,
            "max_price": max_price
        },
        "results": result
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
                "reason": f'{product["name"]} is out of stock'
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