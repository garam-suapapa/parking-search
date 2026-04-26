import os
import platform
import subprocess
import psutil
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

MY_USER_ID = 8779556365
TOKEN = '8790335480:AAH_lEn_WON_gFottxbIWmUuNDUTR3Q7zOA'


def auth(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id != MY_USER_ID:
            return
        await func(update, context)
    return wrapper


@auth
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "PC 원격 제어 봇 가동 완료!\n\n"
        "/status - PC 상태\n"
        "/cpu - CPU 사용률\n"
        "/ram - 메모리 사용량\n"
        "/battery - 배터리 잔량\n"
        "/screenshot - 화면 캡처\n"
        "/lock - 화면 잠금\n"
        "/shutdown - PC 종료\n"
        "/restart - PC 재시작\n"
        "/run <명령어> - 터미널 명령 실행\n"
        "/open <앱이름> - 프로그램 실행\n"
        "/ag <명령어> - Antigravity 에이전트 실행"
    )
    await update.message.reply_text(msg)


@auth
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    os_info = platform.system() + " " + platform.release()
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    ram_used = ram.used // (1024 ** 2)
    ram_total = ram.total // (1024 ** 2)
    msg = (
        f"PC 상태\n"
        f"OS: {os_info}\n"
        f"CPU: {cpu}%\n"
        f"RAM: {ram_used}MB / {ram_total}MB ({ram.percent}%)"
    )
    await update.message.reply_text(msg)


@auth
async def cpu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    usage = psutil.cpu_percent(interval=1)
    cores = psutil.cpu_count()
    await update.message.reply_text(f"CPU 사용률: {usage}%\n코어 수: {cores}")


@auth
async def ram(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mem = psutil.virtual_memory()
    used = mem.used // (1024 ** 2)
    total = mem.total // (1024 ** 2)
    available = mem.available // (1024 ** 2)
    await update.message.reply_text(
        f"메모리 사용량\n"
        f"사용 중: {used}MB\n"
        f"전체: {total}MB\n"
        f"여유: {available}MB\n"
        f"사용률: {mem.percent}%"
    )


@auth
async def battery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bat = psutil.sensors_battery()
    if bat is None:
        await update.message.reply_text("배터리 정보를 가져올 수 없습니다. (데스크탑일 수 있음)")
        return
    status_str = "충전 중" if bat.power_plugged else "배터리 사용 중"
    secs = bat.secsleft
    if secs == psutil.POWER_TIME_UNLIMITED:
        time_str = "완충 상태"
    elif secs == psutil.POWER_TIME_UNKNOWN:
        time_str = "알 수 없음"
    else:
        h, m = divmod(secs // 60, 60)
        time_str = f"약 {h}시간 {m}분 남음"
    await update.message.reply_text(
        f"배터리: {bat.percent:.0f}%\n"
        f"상태: {status_str}\n"
        f"잔여 시간: {time_str}"
    )


@auth
async def screenshot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        import PIL.ImageGrab
        img = PIL.ImageGrab.grab()
        path = "screenshot_temp.png"
        img.save(path)
        with open(path, "rb") as f:
            await update.message.reply_photo(f, caption="현재 화면 캡처")
        os.remove(path)
    except ImportError:
        await update.message.reply_text("Pillow 라이브러리가 필요합니다: pip install Pillow")
    except Exception as e:
        await update.message.reply_text(f"캡처 실패: {e}")


@auth
async def lock(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
    await update.message.reply_text("화면이 잠겼습니다.")


@auth
async def shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("30초 후 PC가 종료됩니다. 취소하려면 /cancel_shutdown")
    subprocess.run(["shutdown", "/s", "/t", "30"])


@auth
async def cancel_shutdown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subprocess.run(["shutdown", "/a"])
    await update.message.reply_text("종료가 취소되었습니다.")


@auth
async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("30초 후 PC가 재시작됩니다. 취소하려면 /cancel_shutdown")
    subprocess.run(["shutdown", "/r", "/t", "30"])


@auth
async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /run <명령어>")
        return
    cmd = " ".join(context.args)
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=10,
            encoding="cp949", errors="replace"
        )
        output = result.stdout or result.stderr or "(출력 없음)"
        if len(output) > 3000:
            output = output[:3000] + "\n...(생략)"
        await update.message.reply_text(f"$ {cmd}\n\n{output}")
    except subprocess.TimeoutExpired:
        await update.message.reply_text("명령 실행 시간 초과 (10초)")
    except Exception as e:
        await update.message.reply_text(f"오류: {e}")


@auth
async def run_antigravity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /ag <명령어>\n예시: /ag plan \"새로운 기능 추가\"")
        return
    
    user_id = update.effective_user.id
    print(f"[LOG] User ({user_id}) called /ag with args: {' '.join(context.args)}", flush=True)

    # 실제 환경의 안티그래비티 실행 명령어에 맞게 수정하세요 (예: ag, antigravity 등)
    ag_command = "antigravity " + " ".join(context.args)
    
    try:
        await update.message.reply_text(f"Antigravity 에이전트를 실행합니다...\n$ {ag_command}")
        print(f"[LOG] Executing command: {ag_command}", flush=True)

        result = subprocess.run(
            ag_command, shell=True, capture_output=True, text=True, timeout=60, # AI 실행 시간을 고려해 타임아웃 60초 설정
            encoding="cp949", errors="replace"
        )

        output = result.stdout or result.stderr or "(출력 없음)"
        print(f"[LOG] Command finished. stdout length: {len(result.stdout)}, stderr length: {len(result.stderr)}", flush=True)

        if len(output) > 3000:
            output = output[:3000] + "\n...(생략)"
        await update.message.reply_text(f"[Antigravity 실행 결과]\n\n{output}")
        
        # 실행 결과를 텍스트 파일로 저장 ('a' 모드를 사용해 계속 누적해서 기록)
        with open("ag_output_log.txt", "a", encoding="utf-8") as f:
            f.write(f"=== 실행 명령어: {ag_command} ===\n")
            f.write((result.stdout or "") + (result.stderr or "") + "\n\n")
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Command timed out: {ag_command}", flush=True)
        await update.message.reply_text("Antigravity 명령 실행 시간 초과 (60초)")
    except Exception as e:
        print(f"[ERROR] Exception during command execution: {e}", flush=True)
        await update.message.reply_text(f"Antigravity 실행 오류: {e}")


@auth
async def open_app(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("사용법: /open <앱이름>\n예: /open notepad")
        return
    app = " ".join(context.args)
    try:
        subprocess.Popen(app, shell=True)
        await update.message.reply_text(f"{app} 실행했습니다.")
    except Exception as e:
        await update.message.reply_text(f"실행 실패: {e}")


if __name__ == '__main__':
    print("텔레그램 원격 봇을 기동합니다...", flush=True)
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("cpu", cpu))
    app.add_handler(CommandHandler("ram", ram))
    app.add_handler(CommandHandler("battery", battery))
    app.add_handler(CommandHandler("screenshot", screenshot))
    app.add_handler(CommandHandler("lock", lock))
    app.add_handler(CommandHandler("shutdown", shutdown))
    app.add_handler(CommandHandler("cancel_shutdown", cancel_shutdown))
    app.add_handler(CommandHandler("restart", restart))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("ag", run_antigravity))
    app.add_handler(CommandHandler("open", open_app))

    print("봇이 텔레그램 메시지를 수신 대기 중입니다. (Ctrl+C로 종료)", flush=True)
    app.run_polling()
