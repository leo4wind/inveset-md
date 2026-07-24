@echo off
rem 在本地启动静态服务器，使 HTML 能自动 fetch 同目录的 JSON
rem 用法：双击本文件，然后在浏览器打开 http://localhost:8000/金融投资知识体系_可视化.html
"C:\Users\admin\.workbuddy\binaries\python\versions\3.13.12\python.exe" -m http.server 8000
