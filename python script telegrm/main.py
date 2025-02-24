import json
import os
import asyncio
import random
import time
from telethon import TelegramClient, events
from config import API_ID, API_HASH, USERS_FILE

# अगर users.json फाइल नहीं है, तो इसे बनाएं
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump([], f)

# सभी यूजर्स को लोड करें
def load_users():
    with open(USERS_FILE, "r") as f:
        return json.load(f)

# नया यूजर जोड़ें
def add_user(phone, session_name):
    users = load_users()
    users.append({"phone": phone, "session": session_name, "source_chats": [], "destination_chats": []})
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# सेशन बनाने का फंक्शन
async def create_session():
    phone = input("\n📞 अपना Telegram नंबर डालें (उदाहरण: +917878066868): ").strip()
    if not phone.startswith("+") or not phone[1:].isdigit():
        print("❌ कृपया सही फ़ॉर्मेट में नंबर डालें (जैसे: +917878066868)")
        return

    session_name = phone.replace("+", "").replace(" ", "")
    
    # सेशन फोल्डर बनाएँ
    if not os.path.exists("sessions"):
        os.makedirs("sessions")

    client = TelegramClient(f"sessions/{session_name}", API_ID, API_HASH)

    await client.start(phone)
    print("✅ नया सेशन सफलतापूर्वक बनाया गया!")
    add_user(phone, session_name)
    await client.disconnect()

# मैसेज फॉरवर्डिंग के लिए सेटअप
async def setup_forwarding():
    users = load_users()
    if not users:
        print("⚠️ कोई भी यूजर लॉगिन नहीं है, पहले नया सेशन बनाएं।")
        return

    phone = input("📞 जिस नंबर का फॉरवर्डिंग सेटअप करना है, उसे दर्ज करें: ").strip()
    user = next((u for u in users if u["phone"] == phone), None)

    if not user:
        print("❌ यह नंबर पहले लॉगिन नहीं हुआ! पहले नया सेशन बनाएं।")
        return

    session_name = user["session"]
    client = TelegramClient(f"sessions/{session_name}", API_ID, API_HASH)
    await client.start()

    try:
        source_chats = list(map(int, input("📥 SOURCE_CHAT IDs (कॉमा से अलग करें): ").split(",")))
        destination_chats = list(map(int, input("📤 DESTINATION_CHAT IDs (कॉमा से अलग करें): ").split(",")))
    except ValueError:
        print("❌ कृपया केवल संख्याएँ दर्ज करें!")
        return

    user["source_chats"] = source_chats
    user["destination_chats"] = destination_chats
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

    print("✅ फॉरवर्डिंग सेटअप पूरा हो गया!")
    await client.disconnect()

# सभी क्लाइंट्स को स्टार्ट करने का फंक्शन
async def start_forwarding():
    users = load_users()
    if not users:
        print("⚠️ कोई भी यूजर लॉगिन नहीं है, पहले नया सेशन बनाएं।")
        return

    clients = []

    for user in users:
        if not user.get("source_chats") or not user.get("destination_chats"):
            print(f"⚠️ {user['phone']} के लिए फॉरवर्डिंग सेटअप नहीं है!")
            continue

        client = TelegramClient(f"sessions/{user['session']}", API_ID, API_HASH)
        await client.start()

        @client.on(events.NewMessage(chats=user["source_chats"]))
        async def handler(event, user=user):
            print(f"📩 नया मैसेज {user['phone']} से आया: {event.message.text}")

            for dest in user["destination_chats"]:
                try:
                    await client.send_message(dest, event.message)
                    print(f"✅ मैसेज {dest} को फॉरवर्ड कर दिया गया!")

                    # **सुरक्षित फॉरवर्डिंग लिमिट** (3-5 सेकंड के बीच का रैंडम डिले)
                    delay = random.uniform(3, 5)
                    print(f"⏳ अगला मैसेज भेजने से पहले {delay:.2f} सेकंड का इंतजार कर रहे हैं...")
                    await asyncio.sleep(delay)

                except Exception as e:
                    print(f"⚠️ {dest} को मैसेज भेजने में दिक्कत: {str(e)}")

        clients.append(client)

    print("🚀 सभी यूजर्स के लिए बॉट लाइव है!")

    await asyncio.gather(*(client.run_until_disconnected() for client in clients))

# मेन ऑप्शन दिखाना
async def main():
    while True:
        print("\n🔹 Telegram Forwarding Bot 🔹\n")
        print("1️⃣ नया Telegram सेशन बनाएं")
        print("2️⃣ मैसेज फॉरवर्डिंग सेट करें")
        print("3️⃣ बॉट को शुरू करें")
        print("4️⃣ एग्ज़िट करें")

        choice = input("➡️ अपना ऑप्शन चुनें (1/2/3/4): ").strip()

        if choice == "1":
            await create_session()
        elif choice == "2":
            await setup_forwarding()
        elif choice == "3":
            await start_forwarding()
        elif choice == "4":
            print("👋 बॉट बंद किया जा रहा है।")
            break
        else:
            print("❌ गलत इनपुट! कृपया 1, 2, 3, या 4 चुनें।")

# बॉट को स्टार्ट करें
if __name__ == "__main__":
    asyncio.run(main())
