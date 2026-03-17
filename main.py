from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List

app = FastAPI()

# ---------------- DATA ----------------

products = [
    {"id": 1, "name": "Wireless Mouse", "price": 499, "category": "Electronics", "in_stock": True},
    {"id": 2, "name": "Notebook", "price": 356, "category": "Stationery", "in_stock": True},
    {"id": 3, "name": "USB HUB", "price": 649, "category": "Electronics", "in_stock": False},
    {"id": 4, "name": "pen set", "price": 199, "category": "stationery", "in_stock": False}
]

cart = []
orders = []
order_counter = 1


# ---------------- MODELS ----------------

class CartItem(BaseModel):
    product_id: int
    quantity: int


# ---------------- BASIC ----------------

@app.get("/")
def home():
    return {"message": "Welcome to Store API"}


@app.get("/products")
def get_products():
    return {"products": products}


# ---------------- Q1 SEARCH ----------------

@app.get("/products/search/{keyword}")
def search_products(keyword: str):
    result = [
        p for p in products
        if keyword.lower() in p["name"].lower()
    ]

    if not result:
        return {"message": "No products found"}

    return {"keyword": keyword, "results": result}


# ---------------- Q2 SORT ----------------

@app.get("/products/sort")
def sort_products(sort_by: str = "price", order: str = "asc"):

    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    reverse = True if order == "desc" else False

    sorted_products = sorted(
        products,
        key=lambda x: x[sort_by].lower() if sort_by == "name" else x[sort_by],
        reverse=reverse
    )

    return {"products": sorted_products}


# ---------------- Q3 PAGINATION ----------------

@app.get("/products/page")
def paginate_products(page: int = 1, limit: int = 2):
    total = len(products)
    total_pages = (total + limit - 1) // limit

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total_products": total,
        "total_pages": total_pages,
        "products": products[start:end]
    }


# ---------------- Q5 CATEGORY SORT ----------------

@app.get("/products/sort-by-category")
def sort_by_category():
    sorted_products = sorted(
        products,
        key=lambda x: (x["category"].lower(), x["price"])
    )
    return {"products": sorted_products}


# ---------------- Q6 BROWSE (MAIN) ----------------

@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 4
):
    result = products.copy()

    # FILTER
    if keyword:
        result = [
            p for p in result
            if keyword.lower() in p["name"].lower()
        ]

    # SORT VALIDATION
    if sort_by not in ["price", "name"]:
        raise HTTPException(status_code=400, detail="Invalid sort_by field")

    # SORT
    reverse = True if order == "desc" else False

    result.sort(
        key=lambda x: x[sort_by].lower() if sort_by == "name" else x[sort_by],
        reverse=reverse
    )

    # PAGINATION
    total = len(result)
    total_pages = (total + limit - 1) // limit

    start = (page - 1) * limit
    end = start + limit

    return {
        "keyword": keyword,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total_found": total,
        "total_pages": total_pages,
        "products": result[start:end]
    }


# ---------------- CART ----------------

@app.post("/cart/add")
def add_to_cart(item: CartItem):

    product = next((p for p in products if p["id"] == item.product_id), None)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["in_stock"]:
        raise HTTPException(status_code=400, detail="Out of stock")

    for c in cart:
        if c["product_id"] == item.product_id:
            c["quantity"] += item.quantity
            return {"message": "Cart updated", "cart": cart}

    cart.append(item.dict())
    return {"message": "Added", "cart": cart}


@app.get("/cart")
def view_cart():
    items = []
    total = 0
    count = 0

    for c in cart:
        p = next(p for p in products if p["id"] == c["product_id"])
        subtotal = p["price"] * c["quantity"]

        total += subtotal
        count += c["quantity"]

        items.append({
            "product": p["name"],
            "qty": c["quantity"],
            "subtotal": subtotal
        })

    return {
        "items": items,
        "item_count": count,
        "grand_total": total
    }


@app.post("/cart/checkout")
def checkout():
    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart empty")

    items = []
    total = 0

    for c in cart:
        p = next(p for p in products if p["id"] == c["product_id"])
        subtotal = p["price"] * c["quantity"]
        total += subtotal

        items.append({
            "product": p["name"],
            "qty": c["quantity"],
            "subtotal": subtotal
        })

    order = {
        "order_id": order_counter,
        "customer_name": f"Customer{order_counter}",
        "items": items,
        "grand_total": total
    }

    orders.append(order)
    order_counter += 1
    cart.clear()

    return {"message": "Order placed", "order": order}


# ---------------- Q4 ORDER SEARCH ----------------

@app.get("/orders/search/{name}")
def search_orders(name: str):
    result = [
        o for o in orders
        if name.lower() in o["customer_name"].lower()
    ]
    return {"results": result}


# ---------------- BONUS PAGINATION ----------------

@app.get("/orders/page")
def paginate_orders(page: int = 1, limit: int = 3):
    total = len(orders)
    total_pages = (total + limit - 1) // limit

    start = (page - 1) * limit
    end = start + limit

    return {
        "page": page,
        "limit": limit,
        "total_orders": total,
        "total_pages": total_pages,
        "orders": orders[start:end]
    }