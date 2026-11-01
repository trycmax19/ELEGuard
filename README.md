

---

# 🐘 ELEGuard - Railway Corridor Encroachment & Elephant Herd Early-Warning System

> An AI-powered Early Warning System to prevent human-elephant conflicts and railway accidents.

*Problem Statement 05 / 10 | RAIL SAFETY · WILDLIFE · EARLY WARNING*

### 🎯 THE CHALLENGE
Build a decision-support prototype combining responsibly collected field observations, corridor maps, and time-sensitive reports to flag possible encroachment or elephant movement near railway corridors.

### 💡 OUR SOLUTION
*3-Layer System:*
1. *Detection:* YOLOv8 + Camera Traps + Field Reports
2. *Verification:* GIS Corridor Match + Confidence Score (No fake alerts)
3. *Alert:* Gemma AI se concise alert banta hai - Example:
`[VERIFIED] Herd of 12 elephants towards Moran Corridor (KM 45). Last seen 15 mins ago. Suggest speed restriction.`

*Gemma PLUS Point:* Gemma summarizes incident reports and drafts concise alerts. Safety-critical warnings are verified by authorities.

### ✨ Features
- 🗺️ Live Corridor Map Dashboard
- 🐘 Herd Tracking & Predictive Path
- 🚨 Smart Verified Alerts
- 📱 Dashboard for Forest + Railway Teams
- 🚂 Railway Speed Regulation Suggestion

### 🏗️ Architecture
`Field Input -> YOLO Detection -> GIS Match -> Verification -> Gemma Summary -> Alert Dashboard`

### 🛠️ Tech Stack
Python, YOLOv8, OpenCV, Gemma 2B, FastAPI, React, Leaflet Maps, Firebase

### 📦 Installation
git clone https://github.com/trycmax19/ELEGuard.git
cd ELEGuard
pip install -r requirements.txt
python main.py
Poora detailed file main bana chuka hu. Chahiye toh main tujhe iska *PDF ya DOCX* bana ke bhi de du?
