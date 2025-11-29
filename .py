from flask import Flask, redirect, request, session, url_for, render_template_string
import requests

app = Flask(__name__)
app.secret_key = "GeorgeWashingTon"

# Discord OAuth app details
CLIENT_ID = "1444265407665016843"
CLIENT_SECRET = "Ze1IUzNtBFzOyhBOn1jrCAASRC6dZ827"
REDIRECT_URI = "http://localhost:5000/callback"
GUILD_ID = "1085860680982347858"
BOT_TOKEN = "MTQ0NDI2NTQwNzY2NTAxNjg0Mw.GcDay-.x50iLCbsUhoCyg8WgB-5BrWrzJUUepHqTXHvgk"
CHANNEL_ID = "1421922556696465582"

AUTH_SCOPE = "identify guilds"
AUTH_URL = (
    f"https://discord.com/api/oauth2/authorize?client_id={CLIENT_ID}"
    f"&redirect_uri={REDIRECT_URI}"
    f"&response_type=code&scope={AUTH_SCOPE.replace(' ', '%20')}"
)

# Store authorized Roblox UserIds
authorized_users = set()

def get_user_info(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get("https://discord.com/api/users/@me", headers=headers).json()

def get_user_guilds(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    return requests.get("https://discord.com/api/users/@me/guilds", headers=headers).json()

def give_channel_access(user_id):
    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/permissions/{user_id}"
    headers = {
        "Authorization": f"Bot {BOT_TOKEN}",
        "Content-Type": "application/json"
    }
    data = {
        "allow": 1024,   # VIEW_CHANNEL
        "deny": 0,
        "type": 1        # 1 = member overwrite
    }
    r = requests.put(url, headers=headers, json=data)
    if r.status_code == 204:
        print(f"✅ User {user_id} now has access to channel {CHANNEL_ID}")
    else:
        print("❌ Failed to give channel access:", r.text)

@app.route("/")
def index():
    return redirect(AUTH_URL)

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
    tokens = r.json()
    session["access_token"] = tokens["access_token"]

    # Check membership
    access_token = session["access_token"]
    user = get_user_info(access_token)
    guilds = get_user_guilds(access_token)
    in_server = any(g["id"] == GUILD_ID for g in guilds)

    if in_server:
        give_channel_access(user["id"])
        # Show form to enter Roblox UserId
        return render_template_string("""
            <h1>Authorized ✅</h1>
            <p>Welcome {{username}}#{{discriminator}}</p>
            <form action="/register_roblox" method="post">
                <label>Enter your Roblox UserId:</label>
                <input type="text" name="roblox_userid">
                <button type="submit">Register</button>
            </form>
        """, username=user["username"], discriminator=user["discriminator"])
    else:
        return "❌ Not authorized (not in server)", 403

@app.route("/register_roblox", methods=["POST"])
def register_roblox():
    if "access_token" not in session:
        return "Not authorized", 403
    roblox_userid = request.form.get("roblox_userid")
    if roblox_userid:
        authorized_users.add(int(roblox_userid))
        print(f"✅ Registered Roblox UserId {roblox_userid} as authorized")
        return "Roblox UserId registered! You can now export the Lua script."
    return "Missing UserId", 400

@app.route("/export_lua")
def export_lua():
    lua_table = "local authorizedUsers = {\n"
    for uid in authorized_users:
        lua_table += f"    [{uid}] = true,\n"
    lua_table += "}\n\n"
    lua_table += """game.Players.PlayerAdded:Connect(function(player)
    local auth = authorizedUsers[player.UserId] or false
    if auth then
        print(player.Name .. " is authorized ✅")
        -- Give them a VIP tool
        local tool = Instance.new("Tool")
        tool.Name = "VIP Sword"
        tool.RequiresHandle = false
        tool.Parent = player.Backpack

        -- Teleport to VIP zone if exists
        local vipArea = workspace:FindFirstChild("VIPZone")
        if vipArea then
            player.CharacterAdded:Connect(function(char)
                char:WaitForChild("HumanoidRootPart").CFrame = vipArea.CFrame
            end)
        end
    else
        print(player.Name .. " is not authorized ❌")
        player:Kick("You are not authorized")
    end
end)"""
    return lua_table, 200, {"Content-Type": "text/plain"}

if __name__ == "__main__":
    app.run(debug=True)
