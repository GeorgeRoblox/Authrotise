from flask import Flask, redirect, request, session, url_for, jsonify
import requests
import webbrowser
import threading

app = Flask(__name__)
app.secret_key = "GeorgeWashingTon"

CLIENT_ID = "1444265407665016843"
CLIENT_SECRET = "Ze1IUzNtBFzOyhBOn1jrCAASRC6dZ827"
REDIRECT_URI = "http://localhost:5000/callback"
GUILD_ID = "1398030847432458260"
INVITE_LINK = "https://discord.gg/YXvPe6p8Ek"

AUTH_SCOPE = "identify guilds"
AUTH_URL = (
    f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code&scope={AUTH_SCOPE.replace(' ', '%20')}"
)

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://discord.com/api/users/@me", headers=headers)
    r.raise_for_status()
    return r.json()

def get_user_guilds(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get("https://discord.com/api/users/@me/guilds", headers=headers)
    r.raise_for_status()
    return r.json()

@app.route("/")
def index():
    if "access_token" in session:
        access_token = session["access_token"]
        user = get_user_info(access_token)
        guilds = get_user_guilds(access_token)
        in_server = any(g["id"] == GUILD_ID for g in guilds)

        status = "✅ Authorized" if in_server else "❌ Not authorized"
        return f"<h1>{status}</h1><p>User: {user['username']}#{user['discriminator']}</p>"
    return f'<h1>Welcome</h1><p><a href="{AUTH_URL}">Login with Discord</a></p>'

@app.route("/callback")
def callback():
    code = request.args.get("code")
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "scope": AUTH_SCOPE,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    r = requests.post("https://discord.com/api/oauth2/token", data=data, headers=headers)
    r.raise_for_status()
    tokens = r.json()
    session["access_token"] = tokens["access_token"]
    return redirect(url_for("index"))

# 👇 New endpoint for Roblox to check
@app.route("/kick/<roblox_user_id>")
def kick(roblox_user_id):
    if "access_token" not in session:
        return jsonify({"kick": False, "reason": "Not authorized"})
    access_token = session["access_token"]
    guilds = get_user_guilds(access_token)
    in_server = any(g["id"] == GUILD_ID for g in guilds)
    if in_server:
        return jsonify({"kick": True, "reason": "testing"})
    else:
        return jsonify({"kick": False, "reason": "Not in Discord server"})

@app.route("/logout")
def logout():
    session.clear()
    return "<h1>Logged out</h1><p><a href='/'>Home</a></p>"

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(debug=False, use_reloader=False)).start()
    webbrowser.open("http://localhost:5000")
