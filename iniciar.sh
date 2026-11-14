#!/bin/bash
# ============================================================
#  LicoMart — Arranque completo con un solo comando
#  Uso:  ./iniciar.sh          (datos existentes)
#         ./iniciar.sh --seed   (borra y recarga datos demo)
# ============================================================
set -e

SEED_FLAG="false"
if [ "${1:-}" = "--seed" ]; then
  SEED_FLAG="true"
  echo ""
  echo "⚠  Se borrarán TODOS los datos y se cargarán datos de demostración."
  echo ""
fi

echo "🚀 Construyendo e iniciando LicoMart..."
echo ""

SEED_ON_START="$SEED_FLAG" docker compose up --build -d

echo ""
echo "⏳ Esperando a que los servicios estén listos..."

# Esperar al backend
RETRIES=30
until curl -sf http://localhost:5173/ > /dev/null 2>&1; do
  RETRIES=$((RETRIES-1))
  if [ "$RETRIES" -le 0 ]; then
    echo "❌ Timeout esperando los servicios. Revisa: docker compose logs"
    exit 1
  fi
  sleep 3
done

echo ""
echo "========================================================"
echo "  ✅  LicoMart está corriendo"
echo "========================================================"
echo ""
echo "  🌐 URL:  http://localhost:5173"
echo ""

if [ "$SEED_FLAG" = "true" ]; then
  echo "  📋 CREDENCIALES:"
  echo "  ────────────────────────────────────────"
  echo "  Rol: admin       Usuario: admin       Clave: Admin2026!"
  echo "  Rol: usuario     Usuario: usuario     Clave: Usuario2026!"
  echo "  ────────────────────────────────────────"
else
  echo "  💡 Para cargar datos demo: ./iniciar.sh --seed"
fi

echo ""
echo "  📖 Logs:   docker compose logs -f"
echo "  🛑 Parar:  docker compose down"
echo "========================================================"
echo ""
