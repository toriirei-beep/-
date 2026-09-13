import sys, os, json, asyncio, secrets, time, hmac, hashlib, requests, uuid
import discord
from discord import app_commands, ui
from discord.ext import commands
from dotenv import load_dotenv
from bcsfe import core


sys.stdout.reconfigure(line_buffering=True); sys.stderr.reconfigure(line_buffering=True)
sys.modules['audioop'] = type('audioop', (object,), {'mul': lambda *a: None, 'max': lambda *a: None})

class DM:
    def __getattr__(self, n): return DM()
    def __call__(self, *a, **k): return DM()
    def __int__(self): return 0
    def __bool__(self): return False
    def __iter__(self): return iter([])
    def __len__(self): return 0
    def __getitem__(self, k): return DM()
    def __setitem__(self, k, v): pass
    def get(self, *a, **k): return DM()

try:
    if not hasattr(core, "core_data"): core.core_data = DM()
    if not hasattr(core.core_data, "config"): core.core_data.config = core.Config()
    core.core_data.config.set(core.ConfigKey.MAX_BACKUPS, 0)
    core.core_data.config.set(core.ConfigKey.UNLOCK_CAT_ON_EDIT, True)
    core.SaveFile.calculate_user_rank = lambda self: secrets.randbelow(3000) + 6000
except: pass

load_dotenv()
TKN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
GV = "15.4.0"
MY_USER_ID = 1483116477698539670


class NSig:
    def __init__(self, iq, d): self.iq, self.d = iq, d
    def s(self, h, d, algo): return h + hmac.new((self.iq + h).encode(), d.encode(), algo).hexdigest()
    def g1(self): return self.s(secrets.token_hex(32), self.d, hashlib.sha256)
    def g2(self): return self.s(secrets.token_hex(20), self.d * 2, hashlib.sha1)

class CEd:
    def __init__(self, tc, pin):
        self.tc, self.pin, self.s = tc, pin, requests.Session()
        self.sf, self.pw, self.err = None, "", ""

    def hdrs(self, iq, d): return {"Content-Type": "application/json", "Nyanko-Signature": NSig(iq, d).g1(), "Nyanko-Timestamp": str(int(time.time())), "Nyanko-Signature-Version": "1", "Nyanko-Signature-Algorithm": "HMACSHA256", "User-Agent": "Dalvik/2.1.0"}

    def dl(self):
        b = json.dumps({"clientInfo": {"client": {"version": GV, "countryCode": "ja"}, "os": {"type": "android", "version": "13"}, "device": {"model": "SM-S918B"}}, "pin": self.pin, "nonce": secrets.token_hex(16)}, separators=(",", ":"))
        try:
            r = self.s.post(f"https://nyanko-save.ponosgames.com/v2/transfers/{self.tc}/reception", headers={"Content-Type": "application/json"}, data=b, timeout=15)
            if r.status_code == 200:
                self.sf = core.SaveFile(core.Data(r.content), cc=core.CountryCode("jp"))
                self.pw = r.headers.get("Nyanko-Password", "")
                return True
                
            self.err = r.text
        except Exception as e: self.err = str(e)
        return False

    def up(self):
        if not self.sf: return None, None
        iq = getattr(self.sf, "inquiry_code", "0")
        try:
            b1 = json.dumps({"accountCode": iq, "password": self.pw, "clientInfo": {"client": {"version": GV, "countryCode": "ja"}, "os": {"type": "android", "version": "9"}, "device": {"model": "SM-G955F"}}, "nonce": secrets.token_hex(16)}, separators=(",", ":"))
            r1 = self.s.post("https://nyanko-auth.ponosgames.com/v1/tokens", headers=self.hdrs(iq, b1), data=b1, timeout=15)
            if r1.status_code != 200: return None, None
            tk = r1.json()["payload"]["token"]
            h2 = self.hdrs(iq, ""); h2["Authorization"] = f"Bearer {tk}"
            r2 = self.s.get(f"https://nyanko-save.ponosgames.com/v2/save/key?nonce={secrets.token_hex(16)}", headers=h2, timeout=15)
            if r2.status_code != 200: return None, None
            aw = r2.json()["payload"]
            requests.post(aw["url"], data={k: v for k, v in aw.items() if k != "url"}, files={"file": ("f.sav", self.sf.to_data().to_bytes(), "application/octet-stream")}, timeout=20)
            rk = self.sf.calculate_user_rank() if hasattr(self.sf, 'calculate_user_rank') else 6000
            bm = json.dumps({"managedItemDetails": [], "nonce": secrets.token_hex(16), "playTime": getattr(self.sf.officer_pass, "play_time", 0), "rank": rk, "receiptLogIds": [], "saveKey": aw["key"], "signature_v1": NSig(iq, "[]").g2()}, separators=(",", ":"))
            h4 = self.hdrs(iq, bm); h4["Authorization"] = f"Bearer {tk}"
            r4 = self.s.post("https://nyanko-save.ponosgames.com/v2/transfers", headers=h4, data=bm, timeout=15)
            if r4.status_code == 200: return r4.json()["payload"].get("transferCode"), r4.json()["payload"].get("pin")
        except: pass
        return None, None

def gl(o):
    if isinstance(o, (list, tuple)): return o
    if isinstance(o, dict): return list(o.values())
    return []

def am(s: core.SaveFile, opts: list[str], amounts: dict):
    lg = []
    core.StoryChapters.clear_tutorial(s)
    s.unlock_equip_menu()
    
    limits = {
        "xp": 99999999, "np": 9999, "catfood": 50000, "leadership": 999,
        "normal_ticket": 999, "rare_ticket": 999, "platinum_tickets": 29, "legend_tickets": 29, "battle_items": 9999, "catseyes": 999, "matatabi": 998
    }
    
    def get_val(k):
        val = amounts.get(k)
        if val is None or val == "": return limits.get(k, 1)
        try: return min(int(val), limits.get(k, 1))
        except: return limits.get(k, 1)

    try:
        eoc3_cleared = False
        if hasattr(s, "story"):
            if hasattr(s.story, "itf") and hasattr(s.story.itf, "chapters"):
                if len(s.story.itf.chapters) > 0:
                    itf_ch1 = s.story.itf.chapters[0]
                    if getattr(itf_ch1, "clear_progress", 0) > 0 or getattr(itf_ch1, "chapter_progress", 0) > 0:
                        eoc3_cleared = True

            if not eoc3_cleared and hasattr(s.story, "eoc") and hasattr(s.story.eoc, "chapters"):
                if len(s.story.eoc.chapters) > 2:
                    ch3 = s.story.eoc.chapters[2]
                    if getattr(ch3, "clear_progress", 0) >= 48 or getattr(ch3, "chapter_progress", 0) >= 48:
                        eoc3_cleared = True

        if not eoc3_cleared:
            chapters = getattr(s.story, "get_real_chapters", lambda: getattr(s.story, "chapters", []))()
            if len(chapters) > 2:
                ch3 = chapters[2]
                progress = getattr(ch3, "clear_progress", getattr(ch3, "chapter_progress", 0))
                try:
                    if int(progress) >= 48:
                        eoc3_cleared = True
                except: pass
                
                if not eoc3_cleared and hasattr(ch3, "stages") and len(ch3.stages) >= 48:
                    try:
                        amt = getattr(ch3.stages[47], "clear_amount", getattr(ch3.stages[47], "clear_times", 0))
                        if int(amt) > 0:
                            eoc3_cleared = True
                    except: pass

            if not eoc3_cleared and len(chapters) > 3:
                for i in range(3, len(chapters)):
                    try:
                        p = getattr(chapters[i], "clear_progress", getattr(chapters[i], "chapter_progress", 0))
                        if int(p) > 0:
                            eoc3_cleared = True
                            break
                    except: pass
    except:
        eoc3_cleared = False

    user_rank = s.calculate_user_rank() if hasattr(s, 'calculate_user_rank') else 0
        
    
    if "xp" in opts: s.xp = get_val("xp"); lg.append(f"â XP {s.xp}")
    if "np" in opts: s.np = get_val("np"); lg.append(f"â NP {s.np}")
    if "catfood" in opts: s.catfood = get_val("catfood"); lg.append(f"â ç«ç¼¶ {s.catfood}")
    if "leadership" in opts: s.leadership = get_val("leadership"); lg.append(f"â çµ±çå {s.leadership}")
        
    if "normal_ticket" in opts: s.normal_tickets = get_val("normal_ticket"); lg.append(f"â ã«ãããã± {s.normal_tickets}")
    if "rare_ticket" in opts: s.rare_tickets = get_val("rare_ticket"); lg.append(f"â ã¬ã¢ãã± {s.rare_tickets}")
    if "platinum_tickets" in opts: s.platinum_tickets = get_val("platinum_tickets"); lg.append(f"â ãã©ãã± {s.platinum_tickets}")
    if "legend_tickets" in opts: s.legend_tickets = get_val("legend_tickets"); lg.append(f"â ã¬ã¸ã§ãã± {s.legend_tickets}")

    
    if "main_stages" in opts and hasattr(s, "story"):
        for ch in s.story.get_real_chapters():
            ch.apply_progress(48, [1]*48)
            for i in range(48):
                ch.set_treasure(i, 3)
                if i < len(ch.stages): ch.stages[i].itf_timed_score = 9999
        for attr in ["tutorial_cleared", "filibuster_stage_cleared", "filibuster_cleared", "aku_unlocked", "is_filibuster_cleared"]:
            if hasattr(s, attr): setattr(s, attr, True)
            if hasattr(s, "story") and hasattr(s.story, attr): setattr(s.story, attr, True)
        if hasattr(s, "filibuster_stage_enabled"): s.filibuster_stage_enabled = False
        if hasattr(s, "invasions"):
            for inv in s.invasions:
                if hasattr(inv, "cleared"): inv.cleared = True
        lg.append("â ã¡ã¤ã³å¨ã¯ãªã¢+48åéãå®")
        eoc3_cleared = True
        
    if "battle_items" in opts:
        v = get_val("battle_items")
        for i in gl(getattr(s.battle_items, "items", [])): i.amount = v
        lg.append(f"â ããã«ã¢ã¤ãã å¨ç¨® {v}")

    if "catseyes" in opts:
        v = get_val("catseyes")
        if eoc3_cleared and user_rank >= 1600:
            updated = False
            if hasattr(s, "catseyes") and isinstance(s.catseyes, list) and (len(s.catseyes) == 0 or isinstance(s.catseyes[0], int)):
                for i in range(len(s.catseyes)):
                    safe = (i <= 4) or (i == 5 and (user_rank >= 9000 or s.catseyes[i] > 0)) or (s.catseyes[i] > 0)
                    if safe: s.catseyes[i] = v
                updated = True
            else:
                ce_arr = gl(getattr(s.catseyes, "catseyes", []))
                if ce_arr:
                    for i, e in enumerate(ce_arr):
                        amt = getattr(e, "amount", 0)
                        safe = (i <= 4) or (i == 5 and (user_rank >= 9000 or amt > 0)) or (amt > 0)
                        if safe: e.amount = v
                    updated = True
                    
            if updated: lg.append(f"â ã­ã£ããã¢ã¤å¨ç¨® {v} (é²è¡åº¦ã«åããã¦èª¿æ´)")
            else: lg.append("â ï¸ ã­ã£ããã¢ã¤ (ãã¼ã¿æªè§£æ¾)")
        else:
            lg.append("â ï¸ ã­ã£ããã¢ã¤ (è§£æ¾æ¡ä»¶æªéæã®ããã¹ã­ãã)")

    if "matatabi" in opts:
        v = get_val("matatabi")
        if eoc3_cleared:
            updated = False
            is_aku_unlocked = getattr(s, "aku_unlocked", False) or getattr(s.story, "aku_unlocked", False)
            
            if hasattr(s, "catfruit") and isinstance(s.catfruit, list) and (len(s.catfruit) == 0 or isinstance(s.catfruit[0], int)):
                for i in range(len(s.catfruit)):
                    safe = (i <= 10) or (i in [13, 14] and is_aku_unlocked) or (s.catfruit[i] > 0)
                    if safe: s.catfruit[i] = v
                updated = True
            else:
                for attr in ["matatabi", "catfruits", "catfruit"]:
                    obj = getattr(s, attr, None)
                    if obj is not None:
                        arr = obj if isinstance(obj, list) else getattr(obj, "matatabi", getattr(obj, "catfruits", []))
                        if arr:
                            for i, f in enumerate(gl(arr)):
                                amt = getattr(f, "amount", 0) if hasattr(f, "amount") else f
                                safe = (i <= 10) or (i in [13, 14] and is_aku_unlocked) or (amt > 0)
                                if safe and hasattr(f, "amount"): f.amount = v
                            updated = True
                            break
                            
            if updated: lg.append(f"â ãã¿ã¿ãå¨ç¨® {v} (è§£æ¾æ¸ã¿ã®ç¯å²ã§èª¿æ´)")
            else: lg.append("â ï¸ ãã¿ã¿ã (ãã¼ã¿æªè§£æ¾)")
        else:
            lg.append("â ï¸ ãã¿ã¿ã (æ¥æ¬ç·¨ç¬¬3ç« æªã¯ãªã¢ã®ããã¹ã­ãã)")

    for f in ["ban_flag", "is_banned", "cheat_flag", "hacked", "show_ban_message", "fraud_flag", "suspicious"]:
        if hasattr(s, f): setattr(s, f, False)
        
    return lg


ITEMS = [
    ("xp", "XP"),
    ("np", "NP"),
    ("catfood", "ç«ç¼¶"),
    ("leadership", "ãªã¼ãã¼ã·ãã"),
    ("normal_ticket", "ã«ãããã±"),
    ("rare_ticket", "ã¬ã¢ãã±"),
    ("platinum_tickets", "ãã©ãã±"),
    ("legend_tickets", "ã¬ã¸ã§ãã±"),
    ("battle_items", "ããã«ã¢ã¤ãã å¨ç¨®"),
    ("catseyes", "ã­ã£ããã¢ã¤å¨ç¨®"),
    ("matatabi", "ãã¿ã¿ãå¨ç¨®"),
    ("main_stages", "ã¡ã¤ã³å¨ã¯ãªã¢ï¼éãå®")
]

class ExModal(ui.Modal):
    def __init__(self, vs):
        super().__init__(title="ã­ã°ã¤ã³æå ±å¥å")
        self.opts = vs
        self.add_item(ui.TextInput(label="å¼ç¶ãã³ã¼ã", required=True))
        self.add_item(ui.TextInput(label="PIN (4æ¡)", min_length=4, max_length=4, required=True))
        
        item_names = [next(l for k, l in ITEMS if k == opt) for opt in vs]
        desc = "ã".join(item_names)
        
        self.add_item(ui.TextInput(
            label="åæ°æå® (é¸æããé ã«ã«ã³ãåºåã)",
            placeholder=f"å¯¾è±¡: {desc[:40]}...",
            required=False
        ))

    async def on_submit(self, i: discord.Interaction):
        await i.response.defer(ephemeral=True)
        
        tc = self.children[0].value
        pin = self.children[1].value
        amt_str = self.children[2].value
        
        amts = {}
        amt_list = [x.strip() for x in amt_str.split(",")] if amt_str else []
        
        for idx, opt in enumerate(self.opts):
            val = None
            if idx < len(amt_list) and amt_list[idx] != "":
                val = amt_list[idx]
            amts[opt] = val

        ed = CEd(tc, pin)
        if not await asyncio.to_thread(ed.dl):
            return await i.followup.send(f"â ã­ã°ã¤ã³ã«å¤±æãã¾ãã: {ed.err}", ephemeral=True)
            
        try:
            lgs = am(ed.sf, self.opts, amts)
        except Exception as e:
            return await i.followup.send(f"â ä»£è¡å¦çã¨ã©ã¼: {e}", ephemeral=True)

        t, p = await asyncio.to_thread(ed.up)
        if t:
            embed = discord.Embed(
                title="âï¸å®äº",
                description=f"**å¼ãç¶ãã³ã¼ã:** `{t}`\n**PIN:** `{p}`\n\n**ãé©å¿ãããåå®¹ã**\n" + "\n".join(lgs),
                color=0x00ff00
            )
            await i.followup.send(embed=embed, ephemeral=True)
            try:
                await i.user.send(embed=embed)
            except discord.Forbidden:
                await i.followup.send("â ï¸ DMè¨­å®ããªãã«ãªã£ã¦ãããããDMã¸æ§ããéä¿¡ã§ãã¾ããã§ãããã³ã¼ãã¯å¿ãã¡ã¢ãã¦ãã ããã", ephemeral=True)
        else:
            await i.followup.send("â ãµã¼ãã¼ã¸ã®ä¿å­ã«å¤±æãã¾ããã", ephemeral=True)

class PSel(ui.Select):
    def __init__(self):
        o = [discord.SelectOption(label=l, value=k) for k, l in ITEMS]
        super().__init__(placeholder="ä»£è¡åå®¹ãé¸æ (è¤æ°é¸æå¯è½)", min_values=1, max_values=len(o), options=o, custom_id="free_nyanko_select")
        
    async def callback(self, i: discord.Interaction):
        await i.response.send_modal(ExModal(self.values))

class PView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(PSel())


import threading, http.server, socketserver 

class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        
    async def setup_hook(self):
        self.add_view(PView())
        await self.tree.sync()

bot = Bot()

@bot.event
async def on_ready():
    print(f"â READY - {bot.user.name} ãèµ·åãã¾ãã")

@bot.tree.command(name="panel", description="ã«ãããä»£è¡ããã«ãè¨­ç½®ãã¾ã")
async def pnl(i: discord.Interaction):
    if i.user.id != MY_USER_ID:
        return await i.response.send_message("â ãã®ã³ãã³ããå®è¡ããæ¨©éãããã¾ããã", ephemeral=True)

    embed = discord.Embed(
        title="ä»£è¡ããã«",
        description="ä¸ã®ã»ã¬ã¯ãã¡ãã¥ã¼ãããç²å¾ãããã¢ã¤ãã ãé¸æãã¦ãã ããï¼è¤æ°é¸æå¯ï¼ã\n\n"
                    "**ãåæ°æå®ã®ã«ã¼ã«ã**\n"
                    "1. é¸æå¾ã®ç»é¢ã§ãæ°å¤ã**é¸æããã¢ã¤ãã ã®é çªã«ã«ã³ãåºåã**ã§å¥åãã¦ãã ããã\n"
                    "   *(ä¾: XPã¨ç«ç¼¶ãé¸ãã å ´å â¡ï¸ `5000000, 1000`)*\n"
                    "2. **ä½ãå¥åããã«æ±ºå®**ãæ¼ããå ´åãé¸æãããã¹ã¦ã®ã¢ã¤ãã ãèªåçã«**ã«ã³ã¹ãå¤**ã«ãªãã¾ãã\n"
                    "*(â»ãã¡ã¤ã³å¨ã¯ãªã¢ï¼éãå®ãã«åæ°æå®ã¯ä¸è¦ã§ãããæå®ãã¦ãç¡è¦ãããã ããªã®ã§åé¡ããã¾ãã)*",
        color=0x00aaff
    )
    await i.channel.send(embed=embed, view=PView())
    await i.response.send_message("â ããã«ãè¨­ç½®ãã¾ããã", ephemeral=True)

def run_server():
    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(s): s.send_response(200); s.end_headers(); s.wfile.write(b"OK")
        def log_message(s,*a): pass
    threading.Thread(target=socketserver.TCPServer(("", int(os.environ.get("PORT", 8080))), H).serve_forever, daemon=True).start()

if __name__ == "__main__":
    run_server()
    bot.run(TKN)
