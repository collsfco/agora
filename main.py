import sys
import asyncio
from app.agents.supervisor import run_principal_turn
from app.api.telegram_ingress import start_telegram_bot_service
from app.core.config import settings

async def cli_interactive_mode(principal_id: str = "principal_a"):
    print("=" * 70)
    print(f"🏛️  ÁGORA CLI INTERACTIVE CONSOLE — Perfil: [{principal_id.upper()}]")
    print("   Escribe 'salir' para terminar o 'switch' para cambiar de Principal.")
    print("=" * 70)
    
    current_p = principal_id
    history = []
    
    while True:
        try:
            prompt = input(f"\n👤 [{current_p.upper()}]: ").strip()
            if not prompt:
                continue
            if prompt.lower() in ("salir", "exit", "quit"):
                break
            if prompt.lower() == "switch":
                current_p = "principal_b" if current_p == "principal_a" else "principal_a"
                history = []
                print(f"🔄 Cambiado a perfil: [{current_p.upper()}]")
                continue

            print("⏳ Ágora razonando en GPU...")
            response = await run_principal_turn(
                user_message=prompt,
                principal_id=current_p,
                conversation_history=history[-6:]
            )
            print(f"\n🤖 Ágora ({current_p.upper()}):\n{response}")
            
            history.append({"role": "user", "content": prompt})
            history.append({"role": "assistant", "content": response})
        except (KeyboardInterrupt, EOFError):
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        p_target = sys.argv[2] if len(sys.argv) > 2 else "principal_a"
        asyncio.run(cli_interactive_mode(p_target))
    elif settings.telegram_bot_token_principal_a or settings.telegram_bot_token_principal_b:
        start_telegram_bot_service()
    else:
        print("ℹ️ TELEGRAM_BOT_TOKEN no detectado en .env. Iniciando modo interactivo por consola CLI...")
        asyncio.run(cli_interactive_mode("principal_a"))
