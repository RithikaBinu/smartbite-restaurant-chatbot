import re
from database import fetch_menu, save_order

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
}

class RestaurantEngine:
    def __init__(self):
        self.menu = fetch_menu()

    def extract_entities(self, text):
        normalized = text.lower()
        for word, num in WORD_NUMBERS.items():
            normalized = re.sub(rf"\b{word}\b", str(num), normalized)

        orders_found = []
        for item in self.menu.keys():
            if item in normalized:
                pattern = rf"(\d+)?\s*(?:portions?|plates?|cups?|x)?\s*{re.escape(item)}"
                match = re.search(pattern, normalized)
                qty = int(match.group(1)) if (match and match.group(1)) else 1
                orders_found.append((item, qty))

        return orders_found

    def format_menu(self):
        lines = ["--- TODAY'S FRESH MENU ---"]
        for name, price in self.menu.items():
            lines.append(f"• {name.title():<18} Rs. {price:.2f}")
        lines.append("\nTip: Type what you'd like (e.g., '2 Chicken Burgers and 1 Coke') to add to your cart.")
        return "\n".join(lines)

    def get_how_to_order(self):
        return (
            "Ordering is simple:\n\n"
            "1. Type the food name and quantity, like:\n"
            "   'Add 2 Chicken Burgers and 1 Coke'\n"
            "2. Your items will immediately show in your cart on the right.\n"
            "3. When you are ready, click 'Checkout Order' or type 'Checkout'!"
        )

    def get_discount_info(self):
        return (
            "Today's Active Offers:\n\n"
            "• Free delivery on all orders over Rs. 2,000.\n"
            "• Buy any 2 Pizzas and get a free Coke (applied automatically at counter)!"
        )

    def get_recommendation(self):
        return (
            "Chef's Top Picks Today:\n\n"
            "1. Chicken Burger (Rs. 650) - Crispy seasoned chicken fillet\n"
            "2. Cheese Pizza (Rs. 1,200) - Loaded mozzarella with fresh herbs\n"
            "3. French Fries (Rs. 400) - Golden crispy and salted"
        )

    def get_delivery_info(self):
        return "Delivery Information:\nStandard delivery takes 30 to 45 minutes to your doorstep."

    def get_payment_info(self):
        return "Payment Methods:\nWe accept Cash on Delivery (COD) as well as Debit/Credit Cards upon delivery."