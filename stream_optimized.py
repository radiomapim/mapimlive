import os
import subprocess
import time
import requests
from flask import Flask

app = Flask(__name__)

# Configurações das variáveis de ambiente
YOUTUBE_KEY = os.getenv('YOUTUBE_KEY', 'sua_chave_youtube')
FACEBOOK_KEY = os.getenv('FACEBOOK_KEY', 'sua_chave_facebook')
IMAGE_URL = os.getenv('IMAGE_URL', 'https://mapimhome.wordpress.com/wp-content/uploads/2025/04/gaitnew.gif')
AUDIO_URL = os.getenv('AUDIO_URL', 'https://stream.zeno.fm/7wbprc3ce4qvv')

# Configurações otimizadas
CONFIG = {
    'video_width': 640,
    'video_height': 360,
    'fps': 15,
    'audio_bitrate': '96k',
    'timeout': 21600  # 6 horas em segundos
}

def get_overlay_filter(platform):
    """Gera overlay otimizado para cada plataforma"""
    text_color = 'white'
    bg_color = 'black@0.5'
    
    if platform == "youtube":
        return (
            f"drawtext=text='RÁDIO MAPIM AO VIVO':fontsize=20:fontcolor={text_color}:"
            f"x=10:y=10:box=1:boxcolor={bg_color},"
            f"drawtext=text='YouTube.com/@radiomapim':fontsize=14:fontcolor={text_color}:"
            f"x=10:y=40"
        )
    else:
        return (
            f"drawtext=text='RÁDIO MAPIM AO VIVO':fontsize=20:fontcolor={text_color}:"
            f"x=10:y=10:box=1:boxcolor={bg_color},"
            f"drawtext=text='Facebook.com/RádioMapim':fontsize=14:fontcolor={text_color}:"
            f"x=10:y=40"
        )

def test_stream_url(url, platform):
    """Testa se a URL de stream está acessível"""
    try:
        if platform == "audio":
            response = requests.head(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            return response.status_code == 200
        else:
            # Para imagens, verificar se a URL existe
            response = requests.head(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            return response.status_code == 200
    except:
        return False

def create_stream_command(platform):
    """Cria comando FFmpeg otimizado para cada plataforma"""
    base_cmd = [
        "ffmpeg",
        "-loglevel", "warning",
        "-re",
        "-stream_loop", "-1",
        "-i", IMAGE_URL,
        "-i", AUDIO_URL,
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-vf", f"scale={CONFIG['video_width']}:{CONFIG['video_height']},fps={CONFIG['fps']},{get_overlay_filter(platform)}",
        "-c:a", "aac",
        "-b:a", CONFIG['audio_bitrate'],
        "-ar", "44100",
        "-f", "flv"
    ]
    
    if platform == "youtube":
        base_cmd.append(f"rtmp://a.rtmp.youtube.com/live2/{YOUTUBE_KEY}")
    else:
        base_cmd.append(f"rtmp://live-api-s.facebook.com:443/rtmp/{FACEBOOK_KEY}")
    
    return base_cmd

def run_stream(platform):
    """Executa o stream com reconexão automática"""
    print(f"🎬 Iniciando {platform.upper()}...")
    
    start_time = time.time()
    error_count = 0
    
    while time.time() - start_time < CONFIG['timeout']:
        try:
            # Testar URLs antes de iniciar
            if not test_stream_url(AUDIO_URL, "audio"):
                print(f"❌ Áudio indisponível, aguardando...")
                time.sleep(60)
                continue
                
            if not test_stream_url(IMAGE_URL, "image"):
                print(f"❌ Imagem indisponível, usando fallback...")
                # Usar fallback preto
                cmd = create_stream_command(platform)
                cmd[cmd.index("-i")] = "-f"
                cmd[cmd.index(IMAGE_URL)] = "lavfi"
                cmd[cmd.index("-i")] = "-i"
                cmd[cmd.index(AUDIO_URL)] = f"color=c=black:s={CONFIG['video_width']}x{CONFIG['video_height']}:r={CONFIG['fps']}"
            else:
                cmd = create_stream_command(platform)
            
            print(f"🔄 Conectando {platform.upper()}...")
            
            # Executar stream
            process = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minutos de timeout
            )
            
            if process.returncode == 0:
                print(f"✅ {platform.upper()} concluído")
                break
            else:
                error_count += 1
                print(f"❌ Erro {platform.upper()}: {process.stderr[:200]}")
                
                if error_count > 3:
                    print(f"⛔ Muitos erros no {platform.upper()}, parando...")
                    break
                    
                time.sleep(30)
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout {platform.upper()}, reiniciando...")
            continue
        except Exception as e:
            print(f"❌ Erro inesperado {platform.upper()}: {e}")
            time.sleep(60)
    
    print(f"🏁 Finalizado {platform.upper()} após {int((time.time() - start_time)/60)} minutos")

@app.route('/')
def home():
    return "📻 Rádio MAPIM Online - Status: OK", 200

@app.route('/health')
def health():
    return {"status": "online", "timestamp": time.time()}, 200

if __name__ == "__main__":
    print("🚀 Iniciando Rádio MAPIM Multiplataforma")
    print("📍 GitHub Actions + Replit + Render")
    
    # Iniciar servidor web em thread
    from threading import Thread
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False)).start()
    
    # Executar streams sequencialmente (evita sobrecarga)
    try:
        run_stream("youtube")
        time.sleep(10)
        run_stream("facebook")
    except KeyboardInterrupt:
        print("🛑 Interrompido pelo usuário")
    
    print("🎉 Transmissão concluída")
