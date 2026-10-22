import streamlit as st
import joblib
import os
from database import init_db, save_order
from bot_engine import RestaurantEngine


st.set_page_config(
    page_title="SmartBite | AI Restaurant Assistant",
    page_icon="🍔",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    /* Gradient Banner */
    .hero-banner {
        background: linear-gradient(135deg, #FF4B4B 0%, #FF8533 100%);
        padding: 24px 30px;
        border-radius: 16px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 8px 24px rgba(255, 75, 75, 0.2);
    }
    .hero-banner h1 {
        color: white;
        margin: 0;
        font-size: 30px;
        font-weight: 800;
    }
    .hero-banner p {
        margin: 6px 0 0 0;
        opacity: 0.95;
        font-size: 14px;
    }
    /* Sidebar Cart Card */
    .cart-item-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(150, 150, 150, 0.2);
        padding: 12px 16px;
        border-radius: 10px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)


init_db()
engine = RestaurantEngine()

@st.cache_resource
def load_model():
    if not os.path.exists("intent_model.joblib"):
        from train import train_model
        train_model()
    return joblib.load("intent_model.joblib")

model = load_model()


if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 **Welcome to SmartBite!**\n\nI can show you our menu, answer delivery and payment questions, and take your order directly. How can I help you today?"}
    ]

if "cart" not in st.session_state:
    st.session_state.cart = {}  # {item_name: quantity}

def handle_user_query(text):
    cleaned = text.lower().strip()
    predicted_tag = model.predict([cleaned])[0]
    confidence = max(model.predict_proba([cleaned])[0])

    if confidence < 0.35:
        return "🤔 I didn't quite catch that. Try asking to see the menu, ordering food (e.g. *'two chicken burgers'*), or checking out!"

    if predicted_tag == "greeting":
        return "Hello! What can I get for you today? Type **'show menu'** or use the quick buttons below!"

    elif predicted_tag == "view_menu":
        return engine.format_menu_markdown()

    elif predicted_tag == "order_item":
        entities = engine.extract_entities(text)
        if not entities:
            return "⚠️ I couldn't recognize that menu item. Please check the menu for our dish names."
        
        added_list = []
        for item, qty in entities:
            st.session_state.cart[item] = st.session_state.cart.get(item, 0) + qty
            added_list.append(f"**{qty}x {item.title()}**")
        return f"✅ Added {', '.join(added_list)} to your order cart!"

    elif predicted_tag == "remove_item":
        if "clear" in cleaned or "everything" in cleaned:
            st.session_state.cart.clear()
            return "🗑️ Your cart has been cleared."
        
        removed = []
        for item in list(st.session_state.cart.keys()):
            if item in cleaned:
                del st.session_state.cart[item]
                removed.append(item.title())
        
        if removed:
            return f"🗑️ Removed {', '.join(removed)} from your cart."
        return "⚠️ That item isn't in your cart."

    elif predicted_tag == "view_cart":
        if not st.session_state.cart:
            return "🛒 Your cart is currently empty."
        
        lines = ["### 🛒 Your Active Cart\n"]
        total = 0.0
        for item, qty in st.session_state.cart.items():
            cost = engine.menu[item] * qty
            total += cost
            lines.append(f"- **{item.title()}** × {qty} = `Rs. {cost:.2f}`")
        lines.append(f"\n**Total: Rs. {total:.2f}**")
        return "\n".join(lines)

    elif predicted_tag == "recommendations":
        return engine.get_recommendation()

    elif predicted_tag == "delivery_time":
        return engine.get_delivery_info()

    elif predicted_tag == "payment_methods":
        return engine.get_payment_info()

    elif predicted_tag == "restaurant_hours":
        return engine.get_hours_info()

    elif predicted_tag == "checkout":
        if not st.session_state.cart:
            return "⚠️ Your cart is empty! Add items before placing an order."
        
        total = sum(engine.menu[item] * qty for item, qty in st.session_state.cart.items())
        summary_str = ", ".join([f"{item} (x{qty})" for item, qty in st.session_state.cart.items()])
        order_id = save_order(summary_str, total)
        st.session_state.cart.clear()
        
        return (
            f"🎉 **Order Placed Successfully!**\n\n"
            f"- **Order ID:** `#{order_id}`\n"
            f"- **Items:** {summary_str}\n"
            f"- **Total Amount:** `Rs. {total:.2f}`\n"
            f"- **Status:** Confirmed & Recorded in SQLite Database\n\n"
            f"*Thank you for dining with SmartBite!*"
        )

    elif predicted_tag == "goodbye":
        return "👋 Have a wonderful day! Hope to see you again soon."

    return "How may I help with your order?"


with st.sidebar:
    st.markdown("### 🛒 Live Order Cart")
    
    if not st.session_state.cart:
        st.info("Your cart is currently empty.")
    else:
        cart_total = 0.0
        for item, qty in list(st.session_state.cart.items()):
            price = engine.menu[item] * qty
            cart_total += price
            c1, c2 = st.columns([3, 1])
            with c1:
                st.write(f"**{item.title()}** × {qty}")
                st.caption(f"Rs. {price:.2f}")
            with c2:
                if st.button("✕", key=f"del_{item}"):
                    del st.session_state.cart[item]
                    st.rerun()

        st.markdown(f"#### Subtotal: **Rs. {cart_total:.2f}**")
        if st.button("💳 Confirm & Checkout", type="primary", use_container_width=True):
            st.session_state.messages.append({"role": "user", "content": "checkout"})
            resp = handle_user_query("checkout")
            st.session_state.messages.append({"role": "assistant", "content": resp})
            st.rerun()
            
        if st.button("Clear Basket", use_container_width=True):
            st.session_state.cart.clear()
            st.rerun()

    st.markdown("---")
    st.markdown("### ⚡ Quick Suggestions")
    if st.button("📋 View Full Menu", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "show menu"})
        st.session_state.messages.append({"role": "assistant", "content": engine.format_menu_markdown()})
        st.rerun()

    if st.button("⭐ Best Sellers", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "what do you recommend?"})
        st.session_state.messages.append({"role": "assistant", "content": engine.get_recommendation()})
        st.rerun()

    if st.button("🕒 Hours & Delivery", use_container_width=True):
        st.session_state.messages.append({"role": "user", "content": "what are your opening hours and delivery time?"})
        st.session_state.messages.append({"role": "assistant", "content": f"{engine.get_hours_info()}\n\n{engine.get_delivery_info()}"})
        st.rerun()


st.markdown("""
<div class="hero-banner">
    <h1>🍔 SmartBite Ordering Assistant</h1>
    <p>100% Offline Python Chatbot • Natural Language Processing • SQLite Persistence</p>
</div>
""", unsafe_allow_html=True)


for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


if prompt := st.chat_input("Type your order (e.g. 'Add two chicken burgers and one coke')..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    reply = handle_user_query(prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
    st.rerun()