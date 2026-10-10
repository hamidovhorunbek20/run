"""
KRYSEC Cyber Academy - bitta fayl: Telegram bot + veb-sayt (WebApp)

O'rnatish:   pip install "python-telegram-bot>=20"
Ishga tushirish:
    export BOT_TOKEN="YANGI_TOKEN"            # BotFather'dan (eskisini revoke qiling!)
    export WEBAPP_URL="https://sizning-domen" # sayt tashqaridan ko'rinadigan HTTPS manzil
    export ADMIN_ID="8539937553"              # arizalar keladigan Telegram ID
    python krysec_bot.py

Eslatma: Telegram WebApp faqat HTTPS bilan ishlaydi. Render/Railway/Fly.io kabi
hostingda ishga tushirsangiz HTTPS avtomatik beriladi (yoki ngrok/cloudflared ishlating).
Logo kerak bo'lsa, image_12ae76.jpg faylini shu fayl yoniga qo'ying.
"""
import os
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8539937553"))
WEBAPP_URL = os.environ.get("WEBAPP_URL") or os.environ.get("RENDER_EXTERNAL_URL", "https://SIZNING-DOMEN")
PORT = int(os.environ.get("PORT", "8080"))
HERE = os.path.dirname(os.path.abspath(__file__))

# ----------------------------------------------------------------------------
# SAYT (HTML)
# ----------------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="uz" class="dark">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
    <title>KRYSEC // Elite Cyber Defense & Threat Intelligence Academy</title>
    <meta name="theme-color" content="#010309">
    <link rel="icon" href="image_12ae76.jpg">
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;800;900&family=Rajdhani:wght@500;600;700&family=JetBrains+Mono:wght@400;600;800&display=swap" rel="stylesheet">
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        deepBg: '#010309',
                        cyberCyan: '#00f0ff',
                        cyberGreen: '#00ff88',
                        cyberPurple: '#b000ff',
                        cyberRed: '#ff0055',
                        cyberYellow: '#ffcc00'
                    },
                    fontFamily: {
                        orb: ['Orbitron', 'sans-serif'],
                        raj: ['Rajdhani', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace']
                    }
                }
            }
        }
    </script>
    <style>
        body {
            background-color: #010309;
            color: #c5d8ff;
            font-family: 'Rajdhani', sans-serif;
            overflow-x: hidden;
        }

        ::-webkit-scrollbar { width: 6px; }
        ::-webkit-scrollbar-track { background: #010309; }
        ::-webkit-scrollbar-thumb { background: #00f0ff; border-radius: 4px; }

        .glass-panel {
            background: rgba(3, 9, 26, 0.85);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(0, 240, 255, 0.18);
            box-shadow: 0 0 40px rgba(0, 0, 0, 0.8);
        }

        @keyframes glowPulse {
            0%, 100% { box-shadow: 0 0 15px rgba(0, 240, 255, 0.2); }
            50% { box-shadow: 0 0 35px rgba(0, 240, 255, 0.6); }
        }
        .anim-glow { animation: glowPulse 3s infinite ease-in-out; }

        @keyframes floatCard {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
        .anim-float { animation: floatCard 4s infinite ease-in-out; }

        @keyframes borderRotate {
            0% { border-color: #00f0ff; }
            33% { border-color: #b000ff; }
            66% { border-color: #00ff88; }
            100% { border-color: #00f0ff; }
        }
        .anim-border { animation: borderRotate 6s infinite linear; }

        @keyframes scanline {
            0% { transform: translateY(-100%); }
            100% { transform: translateY(1000%); }
        }
        .scanner-line {
            position: absolute; top: 0; left: 0; right: 0; height: 2px;
            background: linear-gradient(90deg, transparent, #00f0ff, transparent);
            animation: scanline 5s linear infinite; opacity: 0.7; pointer-events: none;
        }

        @keyframes radarSweep { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
        .radar-spinner { animation: radarSweep 8s linear infinite; }

        @keyframes neonFlicker {
            0%, 19%, 21%, 23%, 25%, 54%, 56%, 100% { opacity: 1; }
            20%, 24%, 55% { opacity: 0.4; }
        }
        .anim-flicker { animation: neonFlicker 4s infinite; }

        .glow-card { transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
        .glow-card:hover {
            box-shadow: 0 0 45px rgba(0, 240, 255, 0.5);
            border-color: rgba(0, 240, 255, 0.9);
            transform: translateY(-8px) scale(1.01);
        }

        .neon-glow {
            text-shadow: 0 0 10px rgba(0, 240, 255, 0.7), 0 0 30px rgba(0, 240, 255, 0.4), 0 0 60px rgba(0, 240, 255, 0.2);
        }

        #matrix-canvas {
            position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: -2;
        }

        .grid-bg {
            background-image: linear-gradient(rgba(0, 240, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px; position: fixed; inset: 0; pointer-events: none; z-index: -1;
        }

        .logo-img {
            box-shadow: 0 0 12px rgba(0, 212, 255, 0.5);
            transition: all 0.3s ease;
        }
        .logo-img:hover {
            box-shadow: 0 0 25px rgba(0, 240, 255, 0.9);
            transform: scale(1.08) rotate(3deg);
        }
    </style>
</head>

<body class="relative min-h-screen selection:bg-cyberCyan selection:text-black">

    <canvas id="matrix-canvas"></canvas>
    <div class="grid-bg"></div>

    <!-- HEADER -->
    <header class="fixed top-0 left-0 right-0 z-50 glass-panel border-b border-cyan-500/20 px-6 lg:px-16 py-4">
        <div class="max-w-7xl mx-auto flex items-center justify-between">
            <a href="#" class="flex items-center space-x-3 group">
                <div class="p-0.5 rounded-full bg-cyberCyan/20 border border-cyberCyan/50 overflow-hidden">
                    <img src="image_12ae76.jpg" alt="KRYSEC Logo" class="w-10 h-10 object-cover rounded-full logo-img">
                </div>
                <div>
                    <span class="font-orb font-black text-xl tracking-wider text-white">KRYSEC</span>
                    <span class="block text-[9px] font-mono text-cyberCyan tracking-widest uppercase">Cyber Intelligence Academy</span>
                </div>
            </a>

            <nav class="hidden lg:flex items-center space-x-6 text-xs font-mono tracking-wider">
                <a href="#about-cyber" class="text-slate-300 hover:text-cyberCyan transition-colors">Kiber-Ma'lumot</a>
                <a href="#modules" class="text-slate-300 hover:text-cyberCyan transition-colors">Modullar</a>
                <a href="#tools" class="text-slate-300 hover:text-cyberCyan transition-colors">Simulyator</a>
                <a href="#standards" class="text-slate-300 hover:text-cyberCyan transition-colors">Standartlar</a>
                <a href="#mentors" class="text-slate-300 hover:text-cyberCyan transition-colors">Mentorlar</a>
            </nav>

            <div class="flex items-center space-x-3">
                <a href="https://t.me/+z-qYlhIJyHhkNGQy" target="_blank"
                    class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-cyberCyan hover:border-cyberCyan text-xs font-mono transition-all anim-glow">
                    TG Kanal
                </a>
                <a href="https://www.instagram.com/krysec.uz?vrfl=NW44a21xNXE1c3V" target="_blank"
                    class="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-pink-400 hover:border-pink-500 text-xs font-mono transition-all">
                    Instagram
                </a>
                <a href="#register" class="px-4 py-2 rounded-xl bg-gradient-to-r from-cyberCyan to-blue-600 text-black font-orb font-bold text-xs tracking-wider uppercase hover:shadow-[0_0_20px_rgba(0,240,255,0.6)] transition-all">Qabul</a>
            </div>
        </div>
    </header>

    <!-- HERO -->
    <section class="relative pt-36 pb-24 md:pt-48 md:pb-36 px-6">
        <div class="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div class="lg:col-span-7 space-y-6">
                <div class="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-cyberCyan/10 border border-cyberCyan/30 text-cyberCyan text-xs font-mono anim-flicker">
                    <span class="w-2 h-2 rounded-full bg-cyberCyan animate-ping"></span>
                    <span>2026-YIL STRATEGIK KIBER O'QUV DASTURI OCHIQ</span>
                </div>
                <h1 class="text-4xl sm:text-6xl font-black font-orb tracking-tight text-white leading-tight">
                    DAVLAT VA KORPORATIV <br>
                    <span class="text-transparent bg-clip-text bg-gradient-to-r from-cyberCyan via-blue-400 to-cyberPurple neon-glow">KIBERXAVFSIZLIK STANDARTI</span>
                </h1>
                <p class="text-slate-300 text-base sm:text-lg font-sans max-w-2xl leading-relaxed">
                    Offensive Security (Red Team), Defensive Operations (Blue Team), SOC tahlili va bulutli arxitekturalar himoyasini real laboratoriya muhitida mukammal o'rganing.
                </p>
                <div class="grid grid-cols-2 sm:grid-cols-3 gap-4 pt-2 font-mono text-xs">
                    <div class="glass-panel p-3 rounded-xl border border-slate-800 flex items-center gap-2 anim-float"><span class="text-cyberGreen font-bold">✓</span> <span>Real CTF Lablar</span></div>
                    <div class="glass-panel p-3 rounded-xl border border-slate-800 flex items-center gap-2 anim-float" style="animation-delay: 0.5s;"><span class="text-cyberCyan font-bold">✓</span> <span>Xalqaro Mentorlar</span></div>
                    <div class="glass-panel p-3 rounded-xl border border-slate-800 flex items-center gap-2 anim-float" style="animation-delay: 1s;"><span class="text-cyberPurple font-bold">✓</span> <span>Karyera Kafolati</span></div>
                </div>
                <div class="flex flex-wrap gap-4 pt-4">
                    <a href="#register" class="px-8 py-4 rounded-xl bg-cyberCyan text-black font-orb font-extrabold text-sm tracking-wider uppercase shadow-[0_0_35px_rgba(0,240,255,0.4)] hover:bg-white transition-all">Hoziroq Qo'shilish</a>
                    <a href="https://t.me/+z-qYlhIJyHhkNGQy" target="_blank" class="px-8 py-4 rounded-xl glass-panel text-cyan-400 border-cyan-500/40 font-orb font-bold text-sm tracking-wider uppercase hover:border-cyberCyan transition-all flex items-center gap-2"><span>Telegram Kanalga O'tish</span> ➔</a>
                </div>
            </div>

            <div class="lg:col-span-5 flex justify-center">
                <div class="w-full max-w-[440px] aspect-square glass-panel rounded-3xl p-6 relative flex flex-col justify-between border border-cyan-500/30 overflow-hidden shadow-[0_0_60px_rgba(0,240,255,0.2)] anim-border">
                    <div class="scanner-line"></div>
                    <div class="flex justify-between items-center font-mono text-xs text-slate-400 border-b border-slate-800 pb-3 z-10">
                        <span class="text-cyberGreen font-bold flex items-center gap-2"><span class="w-2.5 h-2.5 rounded-full bg-cyberGreen animate-pulse"></span>LIVE GLOBAL ATTACK RADAR</span>
                        <span id="live-target-country" class="text-cyberRed font-bold animate-pulse">US / EU / UZ TARGETED</span>
                    </div>
                    <div id="globe-container" class="w-full h-64 flex items-center justify-center relative cursor-grab active:cursor-grabbing"></div>
                    <div class="border-t border-slate-800 pt-3 flex justify-between font-mono text-[11px] text-slate-400 z-10">
                        <span id="orbit-status">ORBIT: 4 SATEL & COMETS ACTIVE</span>
                        <span class="text-cyberCyan">DEFENSE: ENGAGED</span>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- KNOWLEDGE BASE -->
    <section id="about-cyber" class="py-24 px-6 border-t border-slate-800 bg-slate-950/40">
        <div class="max-w-7xl mx-auto space-y-16">
            <div class="text-center max-w-3xl mx-auto space-y-4">
                <span class="text-cyberCyan font-mono text-xs tracking-widest uppercase">// KIBERXAVFSIZLIK ASOSLARI VA BILIMLAR</span>
                <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Nima Uchun Kiberxavfsizlik Muhim?</h2>
                <p class="text-slate-400 text-sm sm:text-base">Zamonaviy raqamli olamda har soniyada minglab kiberhujumlar sodir bo'ladi. Davlat idoralari, moliya sektorlari va yirik korporatsiyalar o'z ma'lumotlarini himoya qilish uchun kuchli mutaxassislarga muhtoj.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800 glow-card">
                    <div class="text-cyberCyan font-mono font-bold text-sm">// RED TEAM (Hujumchi tomon)</div>
                    <h3 class="text-xl font-bold font-orb text-white">Etik Xaking va Pentesting</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Tizimdagi zaifliklarni qaroqchilardan oldin topish va ularni bartaraf etish usullari. Penetratsiya testlari orqali tarmoqning mustahkamligi tekshiriladi.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800 glow-card">
                    <div class="text-cyberGreen font-mono font-bold text-sm">// BLUE TEAM (Himoyachi tomon)</div>
                    <h3 class="text-xl font-bold font-orb text-white">SOC va Hodisalarga Reaksiya</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Xavfsizlik markazlarida (SOC) trafiglarni real vaqtda kuzatish, shubhali harakatlarni aniqlash va kiberhujumlarni zudlik bilan bloklash.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800 glow-card">
                    <div class="text-cyberPurple font-mono font-bold text-sm">// THREAT INTEL (Tahdidlar tahlili)</div>
                    <h3 class="text-xl font-bold font-orb text-white">Kiber Kriminalistika</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Sodir etilgan kiberjinoyatlarning izlarini topish, zararli kodlarni (Malware) disassembler qilish va dalillarni yig'ish san'ati.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- LIVE SOC & TOOLS -->
    <section id="tools" class="py-24 px-6 border-t border-slate-800 bg-slate-950/50 relative">
        <div class="max-w-7xl mx-auto space-y-12">
            <div class="flex flex-col md:flex-row md:items-end justify-between gap-6">
                <div>
                    <span class="text-cyberGreen font-mono text-xs tracking-widest uppercase">// LIVE SOC & TOOLKIT</span>
                    <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Hujumlar va Himoya Monitori</h2>
                </div>
                <div class="font-mono text-xs text-cyberGreen flex items-center gap-2 bg-slate-900 px-4 py-2.5 rounded-xl border border-slate-800">
                    <span class="w-2.5 h-2.5 rounded-full bg-cyberGreen animate-ping"></span>
                    SOC ENGINE: ONLINE
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div class="lg:col-span-8 glass-panel rounded-3xl p-6 font-mono text-xs flex flex-col h-[400px] border border-cyan-500/20 relative overflow-hidden">
                    <div class="flex items-center justify-between pb-4 border-b border-slate-800 text-slate-400">
                        <div class="flex items-center space-x-2">
                            <span class="w-3 h-3 rounded-full bg-red-500"></span>
                            <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
                            <span class="w-3 h-3 rounded-full bg-green-500"></span>
                            <span class="ml-2 text-slate-300">krysec-secops-node@soc:~# tail -f /var/sys/threats.log</span>
                        </div>
                        <span class="text-cyberCyan">STREAMING</span>
                    </div>
                    <div id="terminal-logs" class="flex-1 overflow-y-auto pt-4 space-y-2.5 pr-2"></div>
                </div>

                <div class="lg:col-span-4 glass-panel rounded-3xl p-6 flex flex-col justify-between border border-cyan-500/20 space-y-6">
                    <div class="space-y-4">
                        <div class="flex items-center justify-between">
                            <h3 class="font-orb font-bold text-white text-sm">Parol Shifri Analizatori</h3>
                            <span class="text-[10px] font-mono text-cyberCyan px-2 py-0.5 rounded bg-cyan-950">TOOLKIT</span>
                        </div>
                        <p class="text-slate-400 text-xs">Parolingiz qanchalik xavfsiz ekanligini real vaqtda sinovdan o'tkazing.</p>

                        <div class="space-y-2">
                            <input type="password" id="pass-input" placeholder="Parolni kiriting..." class="w-full bg-slate-900 border border-slate-700 focus:border-cyberCyan rounded-xl px-4 py-3 text-xs text-white outline-none transition-all">
                            <div class="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                                <div id="pass-strength-bar" class="w-0 h-full bg-cyberRed transition-all duration-300"></div>
                            </div>
                            <div class="flex justify-between font-mono text-[11px]">
                                <span class="text-slate-400">Xavfsizlik darajasi:</span>
                                <span id="pass-strength-text" class="text-cyberRed font-bold">Zaif</span>
                            </div>
                        </div>
                    </div>

                    <div class="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 space-y-2 font-mono text-xs">
                        <div class="flex justify-between text-slate-400"><span>Bloklangan IP:</span> <span class="text-cyberGreen font-bold">42,891</span></div>
                        <div class="flex justify-between text-slate-400"><span>CVE Bazasi:</span> <span class="text-cyberCyan font-bold">224,102</span></div>
                    </div>
                </div>
            </div>
        </div>
    </section>

    <!-- MODULES -->
    <section id="modules" class="py-24 px-6 border-t border-slate-800 bg-slate-950/80">
        <div class="max-w-7xl mx-auto space-y-16">
            <div class="text-center max-w-3xl mx-auto space-y-4">
                <span class="text-cyberCyan font-mono text-xs tracking-widest uppercase">// O'QUV DASTURI VA MODULLAR</span>
                <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Mukammal 6 ta Ta'lim Moduli</h2>
                <p class="text-slate-400 text-sm sm:text-base">Har bir modul xalqaro mukofotli va amaliy keyslarga asoslangan holda tuzilgan.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyberCyan/5 rounded-full blur-2xl group-hover:bg-cyberCyan/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyberCyan font-bold">MODUL 01</span>
                    <h3 class="text-2xl font-bold font-orb text-white">Network & OS Security</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">TCP/IP protokollari, Linux/Windows operatsion tizimlarini chuqur tahlil qilish va tarmoq trafigini kuzatish (Wireshark, Nmap).</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyberCyan">✓ Linux Administration & Hardening</li>
                        <li class="flex items-center gap-2 text-cyberCyan">✓ Packet Analysis & Routing</li>
                    </ul>
                </div>

                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyberRed/5 rounded-full blur-2xl group-hover:bg-cyberRed/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyberRed font-bold">MODUL 02</span>
                    <h3 class="text-2xl font-bold font-orb text-white">Offensive Pentesting</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Web ilovalar va API xavfsizligi, OWASP Top 10 zaifliklari, SQL Injection, XSS, CSRF va ularni ekspluatatsiya qilish.</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyberRed">✓ Burp Suite Professional</li>
                        <li class="flex items-center gap-2 text-cyberRed">✓ Web Vulnerabilities Exploitation</li>
                    </ul>
                </div>

                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyberGreen/5 rounded-full blur-2xl group-hover:bg-cyberGreen/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyberGreen font-bold">MODUL 03</span>
                    <h3 class="text-2xl font-bold font-orb text-white">SOC & Incident Response</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Xavfsizlik hodisalarini monitoring qilish, SIEM tizimlari (Splunk, ELK Stack) bilan ishlash va hujumlarga qarshi tezkor choralar.</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyberGreen">✓ SIEM Log Analysis</li>
                        <li class="flex items-center gap-2 text-cyberGreen">✓ Threat Intelligence & Triage</li>
                    </ul>
                </div>

                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyberPurple/5 rounded-full blur-2xl group-hover:bg-cyberPurple/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyberPurple font-bold">MODUL 04</span>
                    <h3 class="text-2xl font-bold font-orb text-white">Reverse Engineering</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Zararli dasturlarni (Malware) tahlil qilish, Assembly tilini o'rganish, disassembler va debuggerlar bilan ishlash sirlari.</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyberPurple">✓ IDA Pro & Ghidra</li>
                        <li class="flex items-center gap-2 text-cyberPurple">✓ Malware Sandboxing</li>
                    </ul>
                </div>

                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyberYellow/5 rounded-full blur-2xl group-hover:bg-cyberYellow/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyberYellow font-bold">MODUL 05</span>
                    <h3 class="text-2xl font-bold font-orb text-white">Cloud & DevSecOps</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">AWS, Azure va Kubernetes infratuzilmalari xavfsizligi, CI/CD quvurlarida avtomatlashtirilgan xavfsizlik auditlari.</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyberYellow">✓ Cloud Security Posture Management</li>
                        <li class="flex items-center gap-2 text-cyberYellow">✓ Container Security</li>
                    </ul>
                </div>

                <div class="glass-panel glow-card rounded-3xl p-8 space-y-4 relative overflow-hidden group">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-cyan-400/5 rounded-full blur-2xl group-hover:bg-cyan-400/15 transition-all"></div>
                    <span class="text-xs font-mono text-cyan-400 font-bold">MODUL 06</span>
                    <h3 class="text-2xl font-bold font-orb text-white">Digital Forensics</h3>
                    <p class="text-slate-400 text-xs sm:text-sm leading-relaxed">Raqamli kriminalistika, xotira dump tahlillari (Memory Forensics) va sud ekspertizasi uchun dalillarni yig'ish.</p>
                    <ul class="space-y-2 font-mono text-xs text-slate-300 pt-2 border-t border-slate-800">
                        <li class="flex items-center gap-2 text-cyan-400">✓ Volatility Framework</li>
                        <li class="flex items-center gap-2 text-cyan-400">✓ Disk Image Analysis</li>
                    </ul>
                </div>
            </div>
        </div>
    </section>

    <!-- STANDARDS -->
    <section id="standards" class="py-24 px-6 border-t border-slate-800 bg-slate-950/60">
        <div class="max-w-7xl mx-auto space-y-16">
            <div class="text-center max-w-3xl mx-auto space-y-4">
                <span class="text-cyberGreen font-mono text-xs tracking-widest uppercase">// GLOBAL FRAMEWORKS</span>
                <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Xalqaro Xavfsizlik Standartlari</h2>
                <p class="text-slate-400 text-sm">Akademiyada o'qitiladigan asosiy mezonlar va freymvorklar to'plami.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8 font-mono">
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800">
                    <div class="text-cyberCyan font-bold text-lg">NIST Cybersecurity Framework</div>
                    <p class="text-xs text-slate-400 font-sans leading-relaxed">Identify, Protect, Detect, Respond va Recover funksiyalari bo'yicha korporativ xavfsizlikni boshqarish.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800">
                    <div class="text-cyberGreen font-bold text-lg">MITRE ATT&CK Matrix</div>
                    <p class="text-xs text-slate-400 font-sans leading-relaxed">Hujumchilarning real taktika va texnikalarini tahlil qilish hamda tahdidlarga qarshi kurashish.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl space-y-4 border border-slate-800">
                    <div class="text-cyberPurple font-bold text-lg">Zero Trust Architecture</div>
                    <p class="text-xs text-slate-400 font-sans leading-relaxed">"Hech qachon ishonma, doimo tekshir" tamoyiliga asoslangan zamonaviy tarmoq arxitekturasi.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- CERTIFICATIONS -->
    <section id="certifications" class="py-24 px-6 border-t border-slate-800 bg-slate-950/40">
        <div class="max-w-7xl mx-auto space-y-16">
            <div class="text-center max-w-3xl mx-auto space-y-4">
                <span class="text-cyberPurple font-mono text-xs tracking-widest uppercase">// GLOBAL CERTIFICATES</span>
                <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Xalqaro Imtihonlarga Tayyorgarlik</h2>
                <p class="text-slate-400 text-sm">Akademiya bitiruvchilari dunyo tan olgan nufuzli xalqaro sertifikatlarni qo'lga kiritishadi.</p>
            </div>

            <div class="grid grid-cols-2 md:grid-cols-4 gap-6 font-mono">
                <div class="glass-panel p-6 rounded-3xl text-center space-y-3 border border-slate-800">
                    <div class="text-2xl font-black font-orb text-cyberCyan">OSCP</div>
                    <div class="text-xs text-slate-400">Offensive Security Certified Professional</div>
                </div>
                <div class="glass-panel p-6 rounded-3xl text-center space-y-3 border border-slate-800">
                    <div class="text-2xl font-black font-orb text-cyberGreen">CEH</div>
                    <div class="text-xs text-slate-400">Certified Ethical Hacker</div>
                </div>
                <div class="glass-panel p-6 rounded-3xl text-center space-y-3 border border-slate-800">
                    <div class="text-2xl font-black font-orb text-cyberPurple">CISSP</div>
                    <div class="text-xs text-slate-400">Certified Information Systems Security</div>
                </div>
                <div class="glass-panel p-6 rounded-3xl text-center space-y-3 border border-slate-800">
                    <div class="text-2xl font-black font-orb text-cyberYellow">CompTIA</div>
                    <div class="text-xs text-slate-400">Security+ & CySA+</div>
                </div>
            </div>
        </div>
    </section>

    <!-- MENTORS -->
    <section id="mentors" class="py-24 px-6 border-t border-slate-800 bg-slate-950/70">
        <div class="max-w-7xl mx-auto space-y-16">
            <div class="text-center max-w-3xl mx-auto space-y-4">
                <span class="text-cyberGreen font-mono text-xs tracking-widest uppercase">// ELITE MENTORING</span>
                <h2 class="text-3xl sm:text-5xl font-extrabold font-orb text-white">Amaliyotchi Mutaxassis Ustozlar</h2>
                <p class="text-slate-400 text-sm">Katta banklar, davlat idoralari va xalqaro kiberxavfsizlik kompaniyalari yetakchi mutaxassislari.</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div class="glass-panel p-8 rounded-3xl text-center space-y-4 border border-slate-800">
                    <div class="w-24 h-24 rounded-2xl bg-gradient-to-tr from-cyberCyan to-blue-600 mx-auto flex items-center justify-center text-black font-orb font-black text-2xl shadow-[0_0_20px_rgba(0,240,255,0.4)]">OSCP</div>
                    <h3 class="font-orb font-bold text-lg text-white">Javohir Turg'unov</h3>
                    <p class="text-xs font-mono text-cyberCyan">Lead Red Team Engineer</p>
                    <p class="text-slate-400 text-xs">7+ yillik pentesting va korporativ xavfsizlik auditi tajribasi.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl text-center space-y-4 border border-slate-800">
                    <div class="w-24 h-24 rounded-2xl bg-gradient-to-tr from-cyberPurple to-pink-600 mx-auto flex items-center justify-center text-white font-orb font-black text-2xl shadow-[0_0_20px_rgba(176,0,255,0.4)]">CISSP</div>
                    <h3 class="font-orb font-bold text-lg text-white">Sardor Rahimov</h3>
                    <p class="text-xs font-mono text-cyberPurple">SOC & Incident Expert</p>
                    <p class="text-slate-400 text-xs">Xalqaro moliya tizimlari axborot xavfsizligi arxitektori.</p>
                </div>
                <div class="glass-panel p-8 rounded-3xl text-center space-y-4 border border-slate-800">
                    <div class="w-24 h-24 rounded-2xl bg-gradient-to-tr from-cyberGreen to-emerald-600 mx-auto flex items-center justify-center text-black font-orb font-black text-2xl shadow-[0_0_20px_rgba(0,255,136,0.4)]">CEH</div>
                    <h3 class="font-orb font-bold text-lg text-white">Azizbek Mahmudov</h3>
                    <p class="text-xs font-mono text-cyberGreen">Cloud & Web Security</p>
                    <p class="text-slate-400 text-xs">Veb-ilovalar zaifliklarini qidirish va kod auditi bo'yicha ekspert.</p>
                </div>
            </div>
        </div>
    </section>

    <!-- REGISTRATION -->
    <section id="register" class="py-24 px-6 border-t border-slate-800 bg-slate-950">
        <div class="max-w-3xl mx-auto">
            <div class="glass-panel rounded-3xl p-8 md:p-12 border border-cyberCyan/40 shadow-[0_0_60px_rgba(0,240,255,0.2)] space-y-8 relative overflow-hidden">
                <div class="absolute top-0 right-0 w-64 h-64 bg-cyberCyan/10 rounded-full blur-3xl pointer-events-none"></div>

                <div class="text-center space-y-3">
                    <span class="text-cyberCyan font-mono text-xs uppercase tracking-widest">// ONLINE ANKETA & QABUL</span>
                    <h2 class="text-3xl font-extrabold font-orb text-white">KRYSEC Akademiyasiga Yozilish</h2>
                    <p class="text-slate-400 text-xs sm:text-sm">Ma'lumotlaringizni qoldiring va ariza muvaffaqiyatli yuborilsin.</p>
                </div>

                <form id="registration-form" class="space-y-6">
                    <div>
                        <label class="block text-xs font-mono text-slate-300 mb-2">ISM VA FAMILIYA *</label>
                        <input type="text" id="input-fullname" required placeholder="Alisher Valiyev" class="w-full bg-slate-900 border border-slate-700 focus:border-cyberCyan rounded-xl px-4 py-3.5 text-sm text-white outline-none transition-all">
                    </div>

                    <div>
                        <label class="block text-xs font-mono text-slate-300 mb-2">TELEFON RAQAM *</label>
                        <input type="tel" id="input-phone" required placeholder="+998 90 123 45 67" class="w-full bg-slate-900 border border-slate-700 focus:border-cyberCyan rounded-xl px-4 py-3.5 text-sm text-white outline-none transition-all">
                    </div>

                    <div>
                        <label class="block text-xs font-mono text-slate-300 mb-2">DARSLAR KUNLARI *</label>
                        <div class="grid grid-cols-2 gap-3">
                            <label class="cursor-pointer">
                                <input type="radio" name="class-days" value="Juft kunlar (Sesh / Pay / Shan)" checked class="peer sr-only">
                                <div class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 peer-checked:border-cyberCyan peer-checked:bg-cyberCyan/10 peer-checked:text-cyberCyan text-center transition-all text-xs font-mono">
                                    Juft kunlar <span class="block text-[10px] text-slate-400">(Sesh / Pay / Shan)</span>
                                </div>
                            </label>
                            <label class="cursor-pointer">
                                <input type="radio" name="class-days" value="Toq kunlar (Dush / Chor / Jum)" class="peer sr-only">
                                <div class="p-3.5 rounded-xl bg-slate-900 border border-slate-800 peer-checked:border-cyberCyan peer-checked:bg-cyberCyan/10 peer-checked:text-cyberCyan text-center transition-all text-xs font-mono">
                                    Toq kunlar <span class="block text-[10px] text-slate-400">(Dush / Chor / Jum)</span>
                                </div>
                            </label>
                        </div>
                    </div>

                    <div>
                        <label class="block text-xs font-mono text-slate-300 mb-2">QULAY DARSLAR VAQTI *</label>
                        <div class="grid grid-cols-3 gap-3">
                            <label class="cursor-pointer">
                                <input type="radio" name="class-time" value="09:00" checked class="peer sr-only">
                                <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 peer-checked:border-cyberCyan peer-checked:bg-cyberCyan/10 peer-checked:text-cyberCyan text-center transition-all text-xs font-mono">09:00 (Ertalab)</div>
                            </label>
                            <label class="cursor-pointer">
                                <input type="radio" name="class-time" value="15:00" class="peer sr-only">
                                <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 peer-checked:border-cyberCyan peer-checked:bg-cyberCyan/10 peer-checked:text-cyberCyan text-center transition-all text-xs font-mono">15:00 (Kunduz)</div>
                            </label>
                            <label class="cursor-pointer">
                                <input type="radio" name="class-time" value="19:00" class="peer sr-only">
                                <div class="p-3 rounded-xl bg-slate-900 border border-slate-800 peer-checked:border-cyberCyan peer-checked:bg-cyberCyan/10 peer-checked:text-cyberCyan text-center transition-all text-xs font-mono">19:00 (Kechki)</div>
                            </label>
                        </div>
                    </div>

                    <div id="form-status" class="hidden p-4 rounded-xl text-xs font-mono text-center"></div>

                    <button type="submit" class="w-full py-4 rounded-xl bg-gradient-to-r from-cyberCyan to-blue-600 text-black font-orb font-extrabold text-sm tracking-wider uppercase hover:opacity-95 shadow-[0_0_30px_rgba(0,240,255,0.4)] transition-all">
                        Ariza Yuborish
                    </button>
                </form>
            </div>
        </div>
    </section>

    <!-- FOOTER -->
    <footer class="border-t border-slate-800 bg-[#010206] py-12 px-6 text-xs font-mono text-slate-400">
        <div class="max-w-7xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
            <div class="flex items-center space-x-3">
                <span class="text-cyberCyan font-orb font-bold">KRYSEC CYBER ACADEMY</span>
                <span>&copy; 2026. Barcha huquqlar himoyalangan.</span>
            </div>
            <div class="flex items-center space-x-6">
                <a href="https://t.me/+z-qYlhIJyHhkNGQy" target="_blank" class="hover:text-cyberCyan transition-colors flex items-center gap-1.5">Telegram Kanal</a>
                <a href="https://www.instagram.com/krysec.uz?vrfl=NW44a21xNXE1c3V" target="_blank" class="hover:text-pink-400 transition-colors flex items-center gap-1.5">Instagram</a>
            </div>
        </div>
    </footer>

    <script>
        const tg = window.Telegram?.WebApp;
        if (tg) { tg.ready(); tg.expand(); }

        // Matrix Rain Effect
        const canvas = document.getElementById('matrix-canvas');
        const ctx = canvas.getContext('2d');
        function resizeMatrix() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resizeMatrix();
        window.addEventListener('resize', resizeMatrix);

        const matrixChars = '01ABCDEFXYZ#$@&%<>\\/';
        const fontSize = 14;
        const columns = Math.floor(canvas.width / fontSize);
        const drops = Array(columns).fill(1);

        function drawMatrix() {
            ctx.fillStyle = 'rgba(1, 3, 9, 0.15)';
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            ctx.fillStyle = '#00f0ff';
            ctx.font = fontSize + 'px monospace';
            for (let i = 0; i < drops.length; i++) {
                const text = matrixChars.charAt(Math.floor(Math.random() * matrixChars.length));
                ctx.fillText(text, i * fontSize, drops[i] * fontSize);
                if (drops[i] * fontSize > canvas.height && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            }
            requestAnimationFrame(drawMatrix);
        }
        requestAnimationFrame(drawMatrix);

        // Three.js Globe + Comets
        const container = document.getElementById('globe-container');
        if (container) {
            const scene = new THREE.Scene();
            const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
            camera.position.z = 210;
            const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
            renderer.setSize(240, 240);
            container.appendChild(renderer.domElement);

            const earthGeo = new THREE.SphereGeometry(68, 32, 32);
            const earthMat = new THREE.MeshBasicMaterial({ color: 0x0055ff, wireframe: true, transparent: true, opacity: 0.6 });
            const earth = new THREE.Mesh(earthGeo, earthMat);
            scene.add(earth);

            const atmosGeo = new THREE.SphereGeometry(73, 32, 32);
            const atmosMat = new THREE.MeshBasicMaterial({ color: 0x00f0ff, wireframe: true, transparent: true, opacity: 0.15 });
            const atmosphere = new THREE.Mesh(atmosGeo, atmosMat);
            scene.add(atmosphere);

            const cometCount = 6;
            const comets = [];
            for (let i = 0; i < cometCount; i++) {
                const cometGeo = new THREE.SphereGeometry(2.2, 8, 8);
                const cometMat = new THREE.MeshBasicMaterial({ color: i % 2 === 0 ? 0xff0055 : 0x00ff88 });
                const comet = new THREE.Mesh(cometGeo, cometMat);
                comet.userData = {
                    orbitRadius: 85 + i * 8,
                    speed: 0.01 + i * 0.003,
                    angle: Math.random() * Math.PI * 2,
                    yOff: (Math.random() - 0.5) * 40
                };
                scene.add(comet);
                comets.push(comet);
            }

            function animateGlobe() {
                requestAnimationFrame(animateGlobe);
                earth.rotation.y += 0.005;
                atmosphere.rotation.y -= 0.003;
                atmosphere.rotation.x += 0.001;

                comets.forEach(c => {
                    c.userData.angle += c.userData.speed;
                    c.position.x = Math.cos(c.userData.angle) * c.userData.orbitRadius;
                    c.position.z = Math.sin(c.userData.angle) * c.userData.orbitRadius;
                    c.position.y = c.userData.yOff + Math.sin(c.userData.angle * 2) * 10;
                });

                renderer.render(scene, camera);
            }
            animateGlobe();
        }

        // Live Threat Terminal Stream
        const terminalLogs = document.getElementById('terminal-logs');
        const attackList = ['SYN_FLOOD_ATTACK', 'SQL_INJECTION_QUERY', 'XSS_PAYLOAD_DETECTED', 'BRUTE_FORCE_BLOCKED', 'RANSOMWARE_ISOLATED', 'PORT_SCAN_PROBE', 'DDOS_MITIGATED'];
        const countries = ['USA (Targeted)', 'GERMANY (Blocked)', 'UZBEKISTAN (Protected)', 'UK (Defended)', 'SOUTH KOREA (Secure)'];

        function appendLog() {
            if (!terminalLogs) return;
            const time = new Date().toTimeString().split(' ')[0];
            const attack = attackList[Math.floor(Math.random() * attackList.length)];
            const country = countries[Math.floor(Math.random() * countries.length)];
            const isBlocked = Math.random() > 0.15;
            const color = isBlocked ? 'text-cyberGreen' : 'text-cyberRed';
            const status = isBlocked ? 'BLOCKED' : 'ALERT';

            const row = document.createElement('div');
            row.className = 'flex justify-between items-center text-[11px] border-b border-slate-900 pb-1 font-mono';
            row.innerHTML = `<span class="text-slate-500">[${time}]</span> <span class="text-slate-300 font-bold">${attack}</span> <span class="text-cyberCyan">${country}</span> <span class="${color} font-bold px-1.5 rounded bg-slate-900">${status}</span>`;

            terminalLogs.prepend(row);
            if (terminalLogs.children.length > 18) terminalLogs.removeChild(terminalLogs.lastChild);
        }
        setInterval(appendLog, 1200);

        // Password Strength Checker
        const passInput = document.getElementById('pass-input');
        const passBar = document.getElementById('pass-strength-bar');
        const passText = document.getElementById('pass-strength-text');

        if (passInput) {
            passInput.addEventListener('input', (e) => {
                const val = e.target.value;
                let score = 0;
                if (val.length > 5) score++;
                if (val.length > 9) score++;
                if (/[A-Z]/.test(val)) score++;
                if (/[0-9]/.test(val)) score++;
                if (/[\W]/.test(val)) score++;

                if (score <= 2) {
                    passBar.style.width = '33%';
                    passBar.className = 'w-full h-full bg-cyberRed transition-all duration-300';
                    passText.className = 'text-cyberRed font-bold';
                    passText.textContent = 'Zaif';
                } else if (score <= 4) {
                    passBar.style.width = '66%';
                    passBar.className = 'w-full h-full bg-cyberYellow transition-all duration-300';
                    passText.className = 'text-cyberYellow font-bold';
                    passText.textContent = 'O\'rta';
                } else {
                    passBar.style.width = '100%';
                    passBar.className = 'w-full h-full bg-cyberGreen transition-all duration-300';
                    passText.className = 'text-cyberGreen font-bold';
                    passText.textContent = 'Juda Kuchli';
                }
            });
        }

        // Registration -> Telegram bot (sendData)
        const form = document.getElementById('registration-form');
        const statusDiv = document.getElementById('form-status');

        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();

                const fullname = document.getElementById('input-fullname').value.trim();
                const phone = document.getElementById('input-phone').value.trim();
                const classDays = document.querySelector('input[name="class-days"]:checked')?.value;
                const classTime = document.querySelector('input[name="class-time"]:checked')?.value;

                statusDiv.classList.remove('hidden', 'bg-red-500/20', 'text-red-400', 'border-red-500/40', 'bg-cyberGreen/20', 'text-cyberGreen', 'border-cyberGreen/40');

                if (!fullname || !phone || !classDays || !classTime) {
                    statusDiv.classList.add('bg-red-500/20', 'text-red-400', 'border', 'border-red-500/40');
                    statusDiv.textContent = `❌ Xatolik yuz berdi: Barcha maydonlarni to'liq to'ldiring!`;
                    statusDiv.classList.remove('hidden');
                    return;
                }

                if (!tg || !tg.initData) {
                    statusDiv.classList.add('bg-red-500/20', 'text-red-400', 'border', 'border-red-500/40');
                    statusDiv.textContent = `❌ Ariza yuborish uchun saytni Telegram bot orqali oching (/start).`;
                    statusDiv.classList.remove('hidden');
                    return;
                }

                try {
                    tg.sendData(JSON.stringify({
                        type: 'ACADEMY_REGISTRATION',
                        fullname: fullname,
                        phone: phone,
                        class_days: classDays,
                        class_time: classTime
                    }));

                    statusDiv.classList.add('bg-cyberGreen/20', 'text-cyberGreen', 'border', 'border-cyberGreen/40');
                    statusDiv.textContent = `✅ Arizangiz muvaffaqiyatli yuborildi, ${fullname}! Tez orada siz bilan bog'lanamiz.`;
                    statusDiv.classList.remove('hidden');
                    form.reset();
                } catch (err) {
                    statusDiv.classList.add('bg-red-500/20', 'text-red-400', 'border', 'border-red-500/40');
                    statusDiv.textContent = `❌ Arizani yuborishda xatolik yuz berdi. Qayta urinib ko'ring!`;
                    statusDiv.classList.remove('hidden');
                }
            });
        }
    </script>
</body>

</html>
"""


# ----------------------------------------------------------------------------
# VEB-SERVER (saytni taqdim etadi)
# ----------------------------------------------------------------------------
class SiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif path == "/image_12ae76.jpg" and os.path.exists(os.path.join(HERE, "image_12ae76.jpg")):
            with open(os.path.join(HERE, "image_12ae76.jpg"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass


def start_web_server():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), SiteHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logging.info("Sayt http://0.0.0.0:%s da ishlayapti (tashqi manzil: %s)", PORT, WEBAPP_URL)


# ----------------------------------------------------------------------------
# BOT
# ----------------------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # sendData faqat KEYBOARD tugma orqali ochilgan WebApp'da ishlaydi
    kb = ReplyKeyboardMarkup(
        [[KeyboardButton("🛡 KRYSEC Akademiyasiga yozilish", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True,
    )
    await update.message.reply_text(
        "KRYSEC Cyber Academy'ga xush kelibsiz! Quyidagi tugmani bosing 👇",
        reply_markup=kb,
    )


async def web_app_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw = update.effective_message.web_app_data.data
    try:
        d = json.loads(raw)
    except json.JSONDecodeError:
        return
    if d.get("type") != "ACADEMY_REGISTRATION":
        return

    user = update.effective_user
    text = (
        "📥 Yangi ariza\n\n"
        f"👤 Ism: {d.get('fullname')}\n"
        f"📞 Telefon: {d.get('phone')}\n"
        f"📅 Kunlar: {d.get('class_days')}\n"
        f"🕐 Vaqt: {d.get('class_time')}\n\n"
        f"Telegram: @{user.username or '-'} (ID: {user.id})"
    )
    await context.bot.send_message(chat_id=ADMIN_ID, text=text)
    await update.effective_message.reply_text("✅ Arizangiz qabul qilindi! Tez orada bog'lanamiz.")


def main():
    start_web_server()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data))
    app.run_polling()


if __name__ == "__main__":
    main()
