#!/bin/bash

# Script para probar y diagnosticar el servidor Flask
# Uso: ./test_server.sh

SERVER_IP="34.59.115.171"
SERVER_PORT="5000"
APP_DIR="/home/lenderfinanzas/dev/cobros"

echo "=== Diagnóstico del Servidor Flask ==="
echo "Servidor: $SERVER_IP:$SERVER_PORT"
echo "Directorio: $APP_DIR"
echo ""

# 1. Verificar que la aplicación esté corriendo
echo "1. Verificando procesos Python..."
ps aux | grep python | grep -v grep
echo ""

# 2. Verificar puertos abiertos
echo "2. Verificando puerto 5000..."
sudo netstat -tlnp | grep :5000
echo ""

# 3. Verificar conectividad local
echo "3. Prueba de conectividad local..."
curl -s -o /dev/null -w "Código HTTP: %{http_code}\nTiempo: %{time_total}s\n" http://localhost:5000/ || echo "Error conectando localmente"
echo ""

# 4. Verificar firewall (iptables)
echo "4. Reglas de firewall iptables..."
sudo iptables -L INPUT | head -10
echo ""

# 5. Verificar reglas de iptables
echo "5. Reglas de iptables para puerto 5000..."
sudo iptables -L | grep 5000 || echo "No hay reglas específicas para puerto 5000"
echo ""

# 6. Información de red
echo "6. Interfaces de red..."
ip addr show | grep -E "inet.*global" | head -5
echo ""

# 7. Verificar si la aplicación está escuchando en todas las interfaces
echo "7. Verificando en qué interfaces escucha el puerto 5000..."
sudo ss -tlnp | grep :5000
echo ""

echo "=== Comandos útiles ==="
echo "Para iniciar el servidor manualmente:"
echo "cd $APP_DIR && source venv/bin/activate && python3 run.py servidor"
echo ""
echo "Para probar localmente:"
echo "curl http://localhost:5000/"
echo ""
echo "Para probar desde fuera:"
echo "curl http://$SERVER_IP:$SERVER_PORT/"
echo ""
echo "Para ver logs en tiempo real:"
echo "tail -f $APP_DIR/logs/app.log"
