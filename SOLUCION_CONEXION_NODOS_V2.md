# 🔧 Solución Completa: Conexión de Nodos Testnet PlayerGold

## 📋 Situación Actual

Tienes dos nodos testnet ejecutándose pero mostrando "0 peers, 0 connections". Esto indica que:

✅ **Los nodos están iniciando correctamente**
✅ **Están escuchando en puerto 18333**
❌ **No se están conectando entre sí**

## 🎯 Causa del Problema

Los nodos no se conectan porque:
1. **Configuración de bootstrap nodes**: Necesitan las IPs locales correctas
2. **Timing de conexión**: Los nodos intentan conectarse antes de estar completamente listos
3. **Firewall**: Puede estar bloqueando las conexiones entre máquinas

## 🛠️ Solución Paso a Paso

### **PASO 1: Configurar Variables de Entorno Seguras**

**En ambas máquinas**, genera el archivo de configuración local:
```bash
python scripts\generar_env_local.py
```

Este script:
- ✅ Detecta automáticamente tu IP local
- ✅ Te permite configurar las IPs de ambos nodos
- ✅ Genera un archivo `.env.local` seguro (no se commitea)
- ✅ Configura automáticamente qué nodo es cada máquina

### **PASO 2: Verificar Estado Actual**

En **ambas máquinas**, ejecuta:
```bash
python scripts\verificar_estado_red.py
```

Esto te dirá exactamente qué está funcionando y qué no.

### **PASO 3: Configurar Firewall (AMBAS MÁQUINAS)**

**⚠️ IMPORTANTE: Ejecutar como Administrador**

```bash
# En ambas máquinas (como Administrador):
scripts\configurar_firewall_testnet.bat
```

### **PASO 4: Iniciar Nodos con Configuración Segura**

**En ambas máquinas:**
```bash
# Como Administrador:
scripts\iniciar_red_testnet_completa.bat
```

El script usará las variables de entorno de `.env.local` (sin exponer IPs en el código).

### **PASO 4: Verificar Conexión**

Después de 1-2 minutos, deberías ver en los logs:

```
✅ P2P network started successfully on port 18333
✅ Attempting to connect to 2 bootstrap nodes...
✅ Connected to bootstrap node 192.168.1.XXX:18333
✅ Successfully connected to 1 bootstrap nodes
📊 Current network status: 1 peers, 1 connections
```

## 🔍 Diagnóstico de Problemas

### Si los nodos siguen sin conectarse:

**1. Verificar conectividad básica:**
```bash
# Desde cada máquina, probar la otra:
ping 192.168.1.129
ping 192.168.1.132
```

**2. Diagnóstico completo:**
```bash
python scripts\diagnosticar_conexion_nodos.py
```

**3. Verificar puertos:**
```bash
python scripts\diagnosticar_puerto_ocupado.py
```

## 🎮 Una Vez Conectados: Configurar Minería IA

### **PASO 1: Abrir Wallets (AMBAS MÁQUINAS)**
```bash
cd wallet
.\clear-cache-and-start.bat
```

### **PASO 2: Configurar Minería en Cada Wallet**

1. **Ir a pestaña "Minería"**
2. **Descargar modelo IA** (recomendado: Gemma 3 4B)
3. **Esperar descarga completa** (2.4 GB)
4. **Seleccionar modelo** descargado
5. **Hacer clic "🚀 Iniciar Minería"**

### **PASO 3: Verificar Minería Activa**

Deberías ver:
```
🟢 Red: Conectado (1 peer)
🟢 Minería: Activa con Gemma 3 4B
🟢 Challenges procesados: X
🟢 Bloques validados: X
🟢 Recompensas: X.X PRGLD
```

## 📊 Monitoreo Continuo

### **Verificar Estado de Red:**
```bash
python scripts\verificar_estado_red.py
```

### **Monitoreo Detallado:**
```bash
python scripts\diagnostico_red_testnet.py
```

## 🚨 Troubleshooting Común

### **Problema: "Puerto ocupado"**
```bash
scripts\liberar_puerto_18333.bat
```

### **Problema: "Firewall bloqueando"**
```bash
# Como Administrador:
scripts\configurar_firewall_testnet.bat
```

### **Problema: "Nodos no se ven"**
1. Verificar que ambos nodos estén en la misma red (192.168.1.x)
2. Reiniciar router si es necesario
3. Verificar que no hay VPN activa

### **Problema: "Wallet no conecta"**
1. Verificar que los nodos estén conectados primero
2. Reiniciar wallet: `.\clear-cache-and-start.bat`
3. Esperar 30 segundos para sincronización

## 🎯 Resultado Esperado

**Nodos conectados:**
```
2025-12-11 06:15:28,186 - __main__ - INFO - Stats: 1 peers, 1 connections
✅ Connected to bootstrap node 192.168.1.XXX:18333
📊 Current network status: 1 peers, 1 connections
```

**Minería activa:**
```
🟢 Red: Conectado (1 peer)
🟢 Minería: Activa con Gemma 3 4B
🟢 Challenges procesados: 25+
🟢 Recompensas ganadas: 45.5+ PRGLD
```

## 📞 Si Necesitas Ayuda

1. **Ejecutar diagnóstico:** `python scripts\diagnosticar_conexion_nodos.py`
2. **Copiar output completo** del diagnóstico
3. **Incluir logs** de ambos nodos
4. **Especificar** en qué paso tienes problemas

---

## 🎉 ¡Una vez funcionando!

Con ambos nodos conectados y minería activa, tendrás:
- ✅ **Red testnet distribuida** con 2 nodos IA
- ✅ **Consenso PoAIP funcionando** con challenges reales
- ✅ **Minería IA activa** generando recompensas
- ✅ **Sistema completo** listo para pruebas

¡Tu red PlayerGold testnet estará completamente operativa! 🎮⛏️🚀