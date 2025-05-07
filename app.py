import streamlit as st #za web prilojeniq
import requests #za vruzka s API
import pandas as pd #za tablici
import matplotlib.pyplot as plt #za vizualizacii
from datetime import datetime

API_KEY = "a77d7131abc8110bdf258dc669f6b257"
URL_FORECAST = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={API_KEY}&units=metric"

URL_AIR = "http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API key}"

CITY = "Plovdiv"
LAT = 42.1354
LON = 24.7453


NORMALS = {
    "April": {"temp": 14, "rain_days": 7},
    "May": {"temp": 18, "rain_days": 9}
}


response = requests.get(URL_FORECAST)
if response.status_code != 200:
    st.error("❌ Неуспешно изтегляне на данни за времето.")
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


st.subheader("📈 Графики на температурата и валежите")


fig, ax = plt.subplots()
ax.plot(daily["date"], daily["avg_temp"], marker='o', color='orange')
ax.set_title("Средна температура по дни")
ax.set_ylabel("Температура (°C)")
ax.set_xlabel("Дата")
plt.xticks(rotation=45)
st.pyplot(fig)


st.bar_chart(daily.set_index("date")["total_rain"], use_container_width=True)


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


st.subheader("🌫️ Качество на въздуха")
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
