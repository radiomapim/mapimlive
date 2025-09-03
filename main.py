import os
import subprocess
import time
import threading
from flask import Flask

app = Flask(__name__)

# ================= CONFIGURAÇÕES =================
# 🔑 YOUTUBE
RESTREAM_SERVER = "rtmp://saopaulo.restream.io/live"
RESTREAM_KEY = "re_5298008_eventea30e103693c438bb9b12ac963aba8c7"

# 🔑 FACEBOOK
KWAI_SERVER = "rtmp://overseas-tx-sp-push.itotio.com:8100/livecloud"
KWAI_KEY = "kszt_KLyos3I50GY?sign=d17ca40a-a15240d7f5848ad0deda4099039f24ab&ks_fix_ts&ks_ctx=dHRwOlBVTEw7dGZiOjE7cGR0OktXQUk7dmVyOjg0MztwZHk6MDt2cXQ6VU5LTk9XTjtpc1Y6ZmFsc2U7YWlkOjE1MDAwMDIwNDE4NjQxMDtjdHA6UFVTSDtjaWQ6VEhJUkRfVVBEQVRFX1RTQw%3D%3D"

# 🔑 TELEGRAM (via RTMP - normalmente requer servidor intermediário)
TELEGRAM_SERVER = "rtmps://dc1-1.rtmp.t.me/s/"  # Substitua pelo servidor correto
TELEGRAM_KEY = "2177126950:4ucz8KYhQ5GrW7ckhKdPSA"  # Substitua pela sua chave

# 🖼️ URL do seu GIF
IMAGE_URL = "https://mapimhome.wordpress.com/wp-content/uploads/2025/07/vinheta-video-introducao-contagem-regressiva-youtube-1.gif"

# 🔊 URL do áudio da rádio
AUDIO_URL = "https://stream.zeno.fm/7wbprc3ce4qvv?//;stream.mp3?//;stream.pls?//;stream.m3u"

# ================= CONFIGURAÇÕES DE VIDEO/AUDIO =================
VIDEO_WIDTH = 1280
VIDEO_HEIGHT = 780
VIDEO_FPS = 30
AUDIO_BITRATE = "128k"
VIDEO_BITRATE = "1500k"

# ================= FUNÇÃO DE OVERLAY =================
def get_overlay_filter(plataforma):
    """
    Cria textos sobrepostos no vídeo para cada plataforma
    """
    if plataforma == "restream":
        return (
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "text='MAPIM AO VIVO':fontsize=30:fontcolor=white:borderw=2:bordercolor=black@0.8:"
            "x=(w-text_w)/2:y=30:box=1:boxcolor=black@0.5,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            "text='Sintonize! @mapimvg':fontsize=20:fontcolor=white:"
            "x=(w-text_w)/2:y=70"
        )
    elif plataforma == "kawai":
        return (
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "text='MAPIM AO VIVO':fontsize=30:fontcolor=white:borderw=2:bordercolor=black@0.8:"
            "x=(w-text_w)/2:y=30:box=1:boxcolor=black@0.5,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            "text='Sintonize! @mapimvg':fontsize=20:fontcolor=white:"
            "x=(w-text_w)/2:y=70"
        )
    else:
        return (
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "text='MAPIM AO VIVO':fontsize=30:fontcolor=white:borderw=2:bordercolor=black@0.8:"
            "x=(w-text_w)/2:y=30:box=1:boxcolor=black@0.5,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf:"
            "text='Sintonize! @mapimvg':fontsize=20:fontcolor=white:"
            "x=(w-text_w)/2:y=70"
        )

# ================= WEBSERVER =================
@app.route('/')
def status():
    return "📻 Transmissão Rádio MAPIM Online (Multiplataforma)! Status: OK", 400

@app.route('/health')
def health_check():
    return "✅ Servidor operacional", 400

# ================= FUNÇÕES DE TRANSMISSÃO =================
def start_stream(platform_name, server, key):
    """Inicia a transmissão para uma plataforma específica"""
    cmd = [
        "ffmpeg",
        "-loglevel", "warning",
        "-re",
        "-stream_loop", "-1",
        "-i", IMAGE_URL,
        "-i", AUDIO_URL,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-tune", "stillimage",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT},fps={VIDEO_FPS},{get_overlay_filter(platform_name.lower())}",
        "-c:a", "aac",
        "-b:a", AUDIO_BITRATE,
        "-ar", "44100",
        "-f", "flv",
        f"{server}/{key}"
    ]

    print(f"🔄 Iniciando transmissão para {platform_name}...")
    stream_loop(cmd, platform_name)

def stream_loop(cmd, platform_name):
    """Loop de transmissão com reconexão automática"""
    while True:
        try:
            print(f"🎥 Iniciando {platform_name} stream...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Monitorar o processo
            for line in process.stderr:
                if "frame=" in line.lower():
                    print(f"📈 {platform_name}: {line.strip()}")
                elif "error" in line.lower():
                    print(f"❌ ERRO {platform_name}: {line.strip()}")

            
            # Se chegou aqui, o processo terminou
            print(f"⚠️ {platform_name}: FFmpeg parou. Reiniciando em 5 segundos...")
            time.sleep(5)

        except Exception as e:
            print(f"❌ Erro crítico {platform_name}: {e}")
            print(f"🔄 Reiniciando {platform_name} em 10 segundos...")
            time.sleep(10)

# ================= TRANSMISSÃO MULTIPLATAFORMA =================
def start_multi_stream():
    """Inicia transmissão simultânea para todas as plataformas"""
    platforms = [
        ("Restream", RESTREAM_SERVER, RESTREAM_KEY),
        ("Kwai", KWAI_SERVER, KWAI_KEY),
        ("Telegram", TELEGRAM_SERVER, TELEGRAM_KEY),
        
    ]

    print("🎬 Iniciando transmissão multiplataforma")

    # Criar threads para cada plataforma
    threads = []
    for name, server, key in platforms:
        # Verificar se a plataforma está configurada
        if server and key and not server.endswith("your.server.here"):
            thread = threading.Thread(target=start_stream, args=(name, server, key))
            thread.daemon = True
            threads.append(thread)
            thread.start()
            print(f"📡 Iniciando transmissão para {name}")
        else:
            print(f"⏭️  Pulando {name} - não configurado")

    # Manter as threads rodando
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("🛑 Transmissão interrompida pelo usuário")

# ================= EXECUÇÃO =================
if __name__ == "__main__":
    print("🎥 Iniciando servidor de transmissão Rádio MAPIM")
    print("🌐 Health check disponível em: http://localhost:8080/health")
    print("📡 Transmitindo para: YouTube, Facebook, Kick, Instagram, Telegram, Kwai")

    # Iniciar webserver em thread separada
    server_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False, use_reloader=False))
    server_thread.daemon = True
    server_thread.start()

    # Iniciar transmissão multiplataforma
    start_multi_stream()
