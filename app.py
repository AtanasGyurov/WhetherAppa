import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from datetime import date

API_KEY = "a77d7131abc8110bdf258dc669f6b257"  # OpenWeatherMap
STORMGLASS_API_KEY = "7df8e3e2-2b28-11f0-b92e-0242ac130003-7df8e446-2b28-11f0-b92e-0242ac130003"  # Replace with your actual key

NORMALS = {
    "April": {"temp": 14, "rain_days": 7},
    "May": {"temp": 18, "rain_days": 9}
}

st.title("🌦️ Време и Морски Условия (за рибари)")
city = st.text_input("Въведи град:", "Plovdiv")

# --- Геолокация ---
geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
geo_resp = requests.get(geo_url).json()
if not geo_resp:
    st.error("❌ Неуспешно намиране на града.")
    st.stop()
lat = geo_resp[0]["lat"]
lon = geo_resp[0]["lon"]

# --- Прогноза за времето ---
st.header("📅 Прогноза за времето и анализ")
forecast_url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&units=metric"
response = requests.get(forecast_url)
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

# --- Визуализации ---
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

# --- Въздух ---
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
    st.write(f"AQI: **{aqi}** - {AQI_LEVELS.get(aqi, 'Неизвестно')}")
else:
    st.warning("⚠️ Няма информация за качеството на въздуха.")

# --- Морски условия ---
st.header("🌊 Морски условия (за рибари)")
today = date.today().isoformat()
storm_url = f"https://api.stormglass.io/v2/weather/point?lat={lat}&lng={lon}&params=waveHeight,waterTemperature,windSpeed&start={today}&end={today}"
headers = {'Authorization': STORMGLASS_API_KEY}
marine_resp = requests.get(storm_url, headers=headers)

if marine_resp.status_code == 200:
    marine_data = marine_resp.json()["hours"][0]
    wave_height = marine_data["waveHeight"]["noaa"]
    water_temp = marine_data["waterTemperature"]["noaa"]
    wind_speed = marine_data["windSpeed"]["noaa"]

    st.metric("🌊 Височина на вълните", f"{wave_height:.1f} m")
    st.metric("🌡️ Температура на водата", f"{water_temp:.1f} °C")
    st.metric("💨 Скорост на вятъра", f"{wind_speed:.1f} m/s")

    if wave_height > 1.5:
        st.warning("⚠️ Вълните са високи – не се препоръчва излизане за риболов.")
    else:
        st.success("✅ Морските условия са добри за риболов.")
else:
    st.warning("⚠️ Неуспешно изтегляне на морски данни. Провери API ключа.")
