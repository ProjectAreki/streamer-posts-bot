# 🚀 Quick Start Guide for New User

## 🎯 Essential Info

**Server IP:** `142.93.227.232`  
**Username:** `root`  
**Bot Directory:** `/root/streamer-posts-bot`

---

## 🔑 Connect to Server

```bash
ssh root@142.93.227.232
```

*(You'll need the SSH private key or password)*

---

## ⚡ Quick Commands

```bash
# Check if bot is running
systemctl status streamer-posts-bot.service

# View live logs
tail -f /root/streamer-posts-bot/logs/bot.log

# Restart bot
systemctl restart streamer-posts-bot.service

# Stop bot
systemctl stop streamer-posts-bot.service

# Start bot
systemctl start streamer-posts-bot.service
```

---

## 🤖 Bot Details

**Telegram Bot Token:**
```
8487084787:AAEkJ1ftz4hTor_3CT7G--0VQfMe0ptXFkk
```

**OpenRouter API Key:**
```
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
```

**API ID & Hash:**
```
API_ID=21791384
API_HASH=7535dfe3bfd5734054465b99e64d1476
```

---

## 📂 Important Files

```
/root/streamer-posts-bot/.env          # Configuration
/root/streamer-posts-bot/logs/bot.log  # Main logs
/root/streamer-posts-bot/bot.py        # Main file
```

---

## 🔄 Update Bot

```bash
ssh root@142.93.227.232
cd /root/streamer-posts-bot
git pull origin main
systemctl restart streamer-posts-bot.service
```

---

## 📦 GitHub

**Repository:** https://github.com/ProjectAreki/streamer-posts-bot

*(Request collaborator access from repository owner)*

---

## 🆘 Troubleshooting

**Bot not responding?**
```bash
systemctl status streamer-posts-bot.service
tail -50 /root/streamer-posts-bot/logs/error.log
```

**View all running bots:**
```bash
ps aux | grep python | grep bot
```

**Restart after code changes:**
```bash
systemctl restart streamer-posts-bot.service
```

---

## 📞 Need Help?

Full documentation: `SERVER_ACCESS_INFO.md`

**Quick check:**
1. Is server accessible? → `ssh root@142.93.227.232`
2. Is bot running? → `systemctl status streamer-posts-bot.service`
3. Any errors? → `tail -50 /root/streamer-posts-bot/logs/error.log`
