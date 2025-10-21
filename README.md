# 🧩 String Analyzer API

A simple **FastAPI** service that analyzes strings and stores their computed properties such as length, palindrome status, unique characters, and more.

Deployed Live At:  
👉 **[http://hng-env.eba-yapigicb.us-west-2.elasticbeanstalk.com](http://hng-env.eba-yapigicb.us-west-2.elasticbeanstalk.com)**

---

## 🚀 Overview

This API analyzes any given string and returns useful computed properties.  
It also supports filtering (via query parameters or natural language) and allows you to retrieve or delete specific strings.

### 🔍 Key Features

- Analyze any string and store its computed data.
- Detect **palindromes** (case-insensitive).
- Compute **unique characters** and **character frequencies**.
- Retrieve and filter analyzed strings with **query parameters** or **natural language**.
- Delete any string from the in-memory database.
- Designed to be beginner-friendly, clean, and easy to deploy on AWS Elastic Beanstalk.

---

## 🧠 Technologies Used

- **FastAPI** — web framework  
- **Uvicorn** — ASGI server  
- **Python 3.9+**  
- **AWS Elastic Beanstalk** — for deployment  

---

## ⚙️ Installation (Local Setup)

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/yourusername/string-analyzer-api.git
cd string-analyzer-api
