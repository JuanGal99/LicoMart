#!/bin/bash
# ============================================================
#  LicoMart — Arranque completo con un solo comando
#  Uso:  ./iniciar.sh              (carga datos demo por defecto)
#        ./iniciar.sh --no-seed    (conserva datos existentes)
# ============================================================
set -e

SEED_FLAG="true"
if [ "${1:-}" = "--no-seed" ]; then
  SEED_FLAG="false"
  echo ""
  echo "⚠  Se conservarán los datos existentes (sin recarga demo)."
  echo ""
fi

echo "🚀 Construyendo e iniciando LicoMart..."
echo ""

SEED_ON_START="$SEED_FLAG" docker compose up --build -d

echo ""
echo "⏳ Esperando a que los servicios estén listos..."

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
echo "  📋 CREDENCIALES:"
echo "  ────────────────────────────────────────"
echo "  Rol: admin       Usuario: admin       Clave: Admin2026!"
echo "  Rol: usuario     Usuario: usuario     Clave: Usuario2026!"
echo "  ────────────────────────────────────────"
echo ""
echo "  📖 Logs:   docker compose logs -f"
echo "  🛑 Parar:  docker compose down"
echo "========================================================"
echo ""
