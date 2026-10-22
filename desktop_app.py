import customtkinter as ctk
import joblib
import os
import time
from database import init_db, save_order
from bot_engine import RestaurantEngine


ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("green")

class RestaurantChatbotApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmartBite Bistro — Order Desk")
        self.geometry("1020x700")
        self.minsize(880, 600)
        self.configure(fg_color="#F8F6F0")

        
        init_db()
        self.engine = RestaurantEngine()

        if not os.path.exists("intent_model.joblib"):
            from train import train_model
            train_model()
        self.model = joblib.load("intent_model.joblib")

        self.cart = {}
        self.is_typing = False

        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self._build_chat_panel()
        self._build_cart_panel()

        
        self.after(300, lambda: self._animate_bot_message(
            "Hello and welcome to SmartBite Bistro!\n\n"
            "I'm your digital dining assistant. You can check out our fresh menu, "
            "ask for specials, or directly order by typing (e.g., '2 Cheese Pizza and 1 Coke')."
        ))

    def _build_chat_panel(self):
        chat_container = ctk.CTkFrame(self, fg_color="#F8F6F0", corner_radius=0)
        chat_container.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        chat_container.grid_rowconfigure(1, weight=1)
        chat_container.grid_columnconfigure(0, weight=1)

        
        header = ctk.CTkFrame(chat_container, fg_color="#FFFFFF", corner_radius=0, height=65)
        header.grid(row=0, column=0, sticky="ew")
        
        title_box = ctk.CTkFrame(header, fg_color="transparent")
        title_box.pack(side="left", padx=24, pady=10)

        ctk.CTkLabel(
            title_box,
            text="SmartBite Bistro",
            font=ctk.CTkFont(family="Segoe UI", size=19, weight="bold"),
            text_color="#2B2D42"
        ).pack(anchor="w")

        ctk.CTkLabel(
            title_box,
            text="Fresh Kitchen • Daily Service: 10:00 AM - 11:00 PM",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8D99AE"
        ).pack(anchor="w")

        status_badge = ctk.CTkLabel(
            header,
            text="● KITCHEN OPEN",
            font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
            text_color="#2A9D8F",
            fg_color="#E8F5F3",
            corner_radius=20,
            padx=12,
            pady=4
        )
        status_badge.pack(side="right", padx=24)

        
        self.chat_scroll = ctk.CTkScrollableFrame(chat_container, fg_color="#F4F1EA", corner_radius=12)
        self.chat_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=(15, 8))
        self.chat_scroll.grid_columnconfigure(0, weight=1)

        
        quick_bar = ctk.CTkFrame(chat_container, fg_color="transparent")
        quick_bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        chips = [
            ("📋 Today's Menu", "Show menu"),
            ("⭐ Chef's Specials", "What do you recommend?"),
            ("🏷️ Active Offers", "Any discounts today?"),
            ("⏱️ Delivery Time", "How long does delivery take?"),
            ("❓ How to Order", "How do I order?")
        ]

        for text, command in chips:
            ctk.CTkButton(
                quick_bar,
                text=text,
                height=30,
                corner_radius=15,
                fg_color="#FFFFFF",
                hover_color="#EDE7DC",
                text_color="#4A4E69",
                border_width=1,
                border_color="#D8D2C2",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda cmd=command: self._send_user_message(cmd)
            ).pack(side="left", padx=(0, 6))

        
        input_container = ctk.CTkFrame(chat_container, fg_color="#FFFFFF", corner_radius=24, border_width=1, border_color="#E2DCD5")
        input_container.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 18))
        input_container.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkEntry(
            input_container,
            placeholder_text="Message your order (e.g. '2 Beef Burger and 1 Iced Tea')...",
            placeholder_text_color="#9A8C98",
            height=46,
            border_width=0,
            fg_color="transparent",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#22223B"
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(18, 8), pady=4)
        self.input_entry.bind("<Return>", lambda event: self._send_user_message())

        self.send_button = ctk.CTkButton(
            input_container,
            text="Send",
            width=80,
            height=36,
            corner_radius=18,
            fg_color="#E76F51",
            hover_color="#D85A3C",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=self._send_user_message
        )
        self.send_button.grid(row=0, column=1, padx=(0, 6), pady=4)

    def _build_cart_panel(self):
        self.cart_frame = ctk.CTkFrame(self, width=310, fg_color="#FFFFFF", corner_radius=0, border_width=1, border_color="#EADDCF")
        self.cart_frame.grid(row=0, column=1, sticky="nsew")
        self.cart_frame.grid_rowconfigure(1, weight=1)

        cart_header = ctk.CTkFrame(self.cart_frame, fg_color="transparent")
        cart_header.grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))

        ctk.CTkLabel(
            cart_header,
            text="Dining Basket",
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            text_color="#2B2D42"
        ).pack(side="left")

        self.item_count_badge = ctk.CTkLabel(
            cart_header,
            text="0 items",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#E76F51",
            fg_color="#FDF0ED",
            corner_radius=10,
            padx=8,
            pady=2
        )
        self.item_count_badge.pack(side="right")

        
        self.cart_items_scroll = ctk.CTkScrollableFrame(self.cart_frame, fg_color="#FAF8F5", corner_radius=10)
        self.cart_items_scroll.grid(row=1, column=0, sticky="nsew", padx=14, pady=5)
        self.cart_items_scroll.grid_columnconfigure(0, weight=1)

        
        checkout_box = ctk.CTkFrame(self.cart_frame, fg_color="#FFFFFF")
        checkout_box.grid(row=2, column=0, sticky="ew", padx=16, pady=18)

        total_row = ctk.CTkFrame(checkout_box, fg_color="transparent")
        total_row.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(
            total_row,
            text="Grand Total",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#6C757D"
        ).pack(side="left")

        self.total_display = ctk.CTkLabel(
            total_row,
            text="Rs. 0.00",
            font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold"),
            text_color="#2A9D8F"
        )
        self.total_display.pack(side="right")

        checkout_btn = ctk.CTkButton(
            checkout_box,
            text="Complete Order",
            height=40,
            corner_radius=20,
            fg_color="#2A9D8F",
            hover_color="#21867A",
            text_color="#FFFFFF",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            command=lambda: self._send_user_message("checkout")
        )
        checkout_btn.pack(fill="x", pady=(0, 6))

        clear_btn = ctk.CTkButton(
            checkout_box,
            text="Clear Basket",
            height=30,
            corner_radius=15,
            fg_color="transparent",
            hover_color="#F1EFEA",
            text_color="#8D99AE",
            font=ctk.CTkFont(size=12),
            command=self._clear_cart
        )
        clear_btn.pack(fill="x")

        self._render_cart()

    def _append_user_message(self, text):
        wrapper = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        wrapper.pack(fill="x", pady=6)

        
        lines = text.count('\n') + max(1, len(text) // 40)
        box_height = max(40, lines * 22 + 16)

        bubble = ctk.CTkTextbox(
            wrapper,
            fg_color="#E76F51",
            text_color="#FFFFFF",
            corner_radius=16,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=min(440, max(120, len(text) * 9 + 30)),
            height=box_height,
            wrap="word",
            activate_scrollbars=False
        )
        bubble.insert("1.0", text)
        bubble.configure(state="disabled")  
        bubble.pack(side="right", padx=(60, 4))
        self._scroll_bottom()
    def _animate_bot_message(self, full_text):
        self.is_typing = True
        wrapper = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        wrapper.pack(fill="x", pady=6)

       
        lines = full_text.count('\n') + max(1, len(full_text) // 48)
        box_height = max(45, lines * 22 + 20)

        bubble = ctk.CTkTextbox(
            wrapper,
            fg_color="#FFFFFF",
            text_color="#2B2D42",
            corner_radius=16,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            width=440,
            height=box_height,
            wrap="word",
            activate_scrollbars=False
        )
        bubble.pack(side="left", padx=(4, 60))

        def step(index=0):
            bubble.configure(state="normal")
            if index <= len(full_text):
                bubble.delete("1.0", "end")
                bubble.insert("1.0", full_text[:index])
                bubble.configure(state="disabled")
                self._scroll_bottom()
                self.after(8, step, index + 3)
            else:
                bubble.delete("1.0", "end")
                bubble.insert("1.0", full_text)
                bubble.configure(state="disabled")  
                self.is_typing = False
                self._scroll_bottom()

        step(0)
    def _scroll_bottom(self):
        self.chat_scroll.update_idletasks()
        self.chat_scroll._parent_canvas.yview_moveto(1.0)

    def _render_cart(self):
        for child in self.cart_items_scroll.winfo_children():
            child.destroy()

        total_count = sum(self.cart.values())
        self.item_count_badge.configure(text=f"{total_count} items")

        if not self.cart:
            empty_box = ctk.CTkFrame(self.cart_items_scroll, fg_color="transparent")
            empty_box.pack(pady=40)
            ctk.CTkLabel(
                empty_box,
                text="Your basket is empty\nItems you order appear here.",
                font=ctk.CTkFont(family="Segoe UI", size=12),
                text_color="#A0AAB2"
            ).pack()
            self.total_display.configure(text="Rs. 0.00")
            return

        grand_total = 0.0
        for item, qty in self.cart.items():
            price = self.engine.menu[item] * qty
            grand_total += price

            item_card = ctk.CTkFrame(self.cart_items_scroll, fg_color="#FFFFFF", corner_radius=10, border_width=1, border_color="#EBE7DE")
            item_card.pack(fill="x", pady=4, padx=2)

            info_col = ctk.CTkFrame(item_card, fg_color="transparent")
            info_col.pack(side="left", padx=10, pady=8)

            ctk.CTkLabel(
                info_col,
                text=f"{item.title()}",
                font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                text_color="#2B2D42"
            ).pack(anchor="w")

            ctk.CTkLabel(
                info_col,
                text=f"{qty} portion(s) • Rs. {price:.2f}",
                font=ctk.CTkFont(family="Segoe UI", size=11),
                text_color="#8D99AE"
            ).pack(anchor="w")

            del_btn = ctk.CTkButton(
                item_card,
                text="✕",
                width=24,
                height=24,
                corner_radius=12,
                fg_color="#FDF0ED",
                hover_color="#F8D7DA",
                text_color="#E76F51",
                font=ctk.CTkFont(size=11, weight="bold"),
                command=lambda it=item: self._remove_item(it)
            )
            del_btn.pack(side="right", padx=10)

        self.total_display.configure(text=f"Rs. {grand_total:.2f}")

    def _remove_item(self, item_name):
        if item_name in self.cart:
            del self.cart[item_name]
            self._render_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._render_cart()

    def _send_user_message(self, message_text=None):
        if self.is_typing:
            return 

        content = message_text if message_text else self.input_entry.get().strip()
        if not content:
            return

        if not message_text:
            self.input_entry.delete(0, "end")

        self._append_user_message(content)
        
       
        self.after(150, lambda: self._process_and_reply(content))

    def _process_and_reply(self, content):
        bot_response = self._get_bot_response(content)
        self._animate_bot_message(bot_response)

    def _get_bot_response(self, text):
        cleaned = text.lower().strip()

        
        entities = self.engine.extract_entities(text)
        removal_keywords = ["remove", "delete", "cancel", "take out", "drop"]
        is_removal = any(kw in cleaned for kw in removal_keywords)

       
        if entities and not is_removal:
            added = []
            for item, qty in entities:
                self.cart[item] = self.cart.get(item, 0) + qty
                added.append(f"{qty}x {item.title()}")

            self._render_cart()
            return f"Delicious choice! Added {', '.join(added)} to your dining basket."

       
        tag = self.model.predict([cleaned])[0]
        prob = max(self.model.predict_proba([cleaned])[0])

        if prob < 0.28:
            return (
                "I'm not quite sure about that inquiry.\n\n"
                "You can ask to view our menu, check active discounts, or tell me "
                "what dishes you'd like to order!"
            )

        if tag == "greeting":
            return "Hello! How can I assist you with your dining experience today? Type 'menu' or choose a quick option below."

        elif tag == "how_to_order":
            return self.engine.get_how_to_order()

        elif tag == "discounts":
            return self.engine.get_discount_info()

        elif tag == "view_menu":
            return self.engine.format_menu()

        elif tag == "remove_item":
            if "clear" in cleaned or "everything" in cleaned:
                self._clear_cart()
                return "Your basket has been cleared."

            removed = []
            for item in list(self.cart.keys()):
                if item in cleaned:
                    del self.cart[item]
                    removed.append(item.title())

            if removed:
                self._render_cart()
                return f"Removed {', '.join(removed)} from your basket."
            return "That item doesn't appear to be in your active basket."

        elif tag == "view_cart":
            if not self.cart:
                return "Your basket is currently empty! Feel free to explore our menu and select a meal."
            lines = ["Your Active Order:"]
            total = 0.0
            for item, qty in self.cart.items():
                cost = self.engine.menu[item] * qty
                total += cost
                lines.append(f"• {item.title()} (x{qty}) — Rs. {cost:.2f}")
            lines.append(f"\nSubtotal: Rs. {total:.2f}")
            return "\n".join(lines)

        elif tag == "recommendations":
            return self.engine.get_recommendation()

        elif tag == "delivery_time":
            return self.engine.get_delivery_info()

        elif tag == "payment_methods":
            return self.engine.get_payment_info()

        elif tag == "checkout":
            if not self.cart:
                return "Your basket is empty. Please add some dishes from the menu first!"

            total = sum(self.engine.menu[item] * qty for item, qty in self.cart.items())
            summary_str = ", ".join([f"{item} (x{qty})" for item, qty in self.cart.items()])
            order_id = save_order(summary_str, total)
            self._clear_cart()

            return (
                f"Thank you! Your order has been placed successfully.\n\n"
                f"• Order Reference: #{order_id}\n"
                f"• Dishes: {summary_str}\n"
                f"• Total Paid: Rs. {total:.2f}\n\n"
                f"Recorded in our SQLite kitchen system. Your meal will be prepared shortly!"
            )

        elif tag == "goodbye":
            return "Thank you for visiting SmartBite Bistro! Have a wonderful day ahead."

        return "How can I help you with your order?"

if __name__ == "__main__":
    app = RestaurantChatbotApp()
    app.mainloop()