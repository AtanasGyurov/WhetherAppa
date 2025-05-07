import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

API_KEY = "a77d7131abc8110bdf258dc669f6b257"

NORMALS = {
    "April": {"temp": 14, "rain_days": 7},
    "May": {"temp": 18, "rain_days": 9}
}

# --- UI ---
st.title("🌦️ Времето в избран град + климатичен анализ")
city = st.text_input("Въведи град:", "Plovdiv")

# --- Get coordinates ---
geocode_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
geo_resp = requests.get(geocode_url).json()
if not geo_resp:
    st.error("❌ Неуспешно намиране на града.")
    st.stop()

lat = geo_resp[0]["lat"]
lon = geo_resp[0]["lon"]

# --- Fetch forecast data ---
URL_FORECAST = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
response = requests.get(URL_FORECAST)
if response.status_code != 200:
    st.error("❌ Неуспешно изтегляне на прогноза.")
    st.stop()

data = response.json()
weather_data = []
for entry in data["list"]:
    dt = datetime.fromtimestamp(entry["dt"])
    temp = entry["main"]["temp"]
    rain = entry.get("rain", {}).get("3h", 0)
    weather_data.append({
        "date": dt.date(),
        "temp": temp,
        "rain": rain
    })

df = pd.DataFrame(weather_data)
daily = df.groupby("date").agg(
    avg_temp=("temp", "mean"),
    total_rain=("rain", "sum"),
    rain_occurred=("rain", lambda x: (x > 0).any())
).reset_index()

# --- Visualization ---
st.subheader("📈 Графики на температурата и валежите")
fig, ax = plt.subplots()
ax.plot(daily["date"], daily["avg_temp"], marker='o', color='orange')
ax.set_title("Средна температура по дни")
ax.set_ylabel("Температура (°C)")
ax.set_xlabel("Дата")
plt.xticks(rotation=45)
st.pyplot(fig)

st.bar_chart(daily.set_index("date")["total_rain"], use_container_width=True)

# --- Анализ ---
current_month = datetime.today().strftime("%B")
norm_temp = NORMALS.get(current_month, {}).get("temp", None)
norm_rain_days = NORMALS.get(current_month, {}).get("rain_days", None)

avg_temp = round(daily["avg_temp"].mean(), 1)
rain_days = daily["rain_occurred"].sum()

st.subheader("📊 Седмичен анализ")
st.write(f"Средна температура: **{avg_temp}°C**")
st.write(f"Дъждовни дни: **{rain_days}**")

if norm_temp:
    if avg_temp > norm_temp + 2:
        st.warning(f"⚠️ Температурите са необичайно високи (+{avg_temp - norm_temp}°C над нормата за {current_month})")
    elif avg_temp < norm_temp - 2:
        st.warning(f"⚠️ Температурите са необичайно ниски ({norm_temp - avg_temp}°C под нормата)")
    else:
        st.success("✅ Температурите са в норма.")

if norm_rain_days:
    if rain_days > norm_rain_days:
        st.warning("🌧️ Повече дъждовни дни от обичайното.")
    else:
        st.info("☀️ Броят на дъждовните дни е в рамките на нормата.")

# --- Air Quality ---
st.subheader("🌫️ Качество на въздуха")
URL_AIR = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
air_response = requests.get(URL_AIR)
if air_response.status_code == 200:
    air_data = air_response.json()
    aqi = air_data["list"][0]["main"]["aqi"]
    AQI_LEVELS = {
        1: "Добро",
        2: "Приемливо",
        3: "Умерено",
        4: "Нездравословно",
        5: "Опасно"
    }
    st.write(f"Индекс на качеството на въздуха (AQI): **{aqi}** - {AQI_LEVELS.get(aqi, 'Неизвестно')}")
else:
    st.warning("⚠️ Неуспешно изтегляне на данни за въздуха.")
