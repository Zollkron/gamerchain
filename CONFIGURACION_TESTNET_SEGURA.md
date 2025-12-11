# 🔒 Configuración Segura de Testnet PlayerGold

## 🎯 Configuración de Red Distribuida con IAs

Esta guía te ayudará a configurar una red testnet PlayerGold con dos nodos IA sin exponer información sensible en el repositorio.

## 📋 Requisitos Previos

- 2 máquinas con Windows 11 y RTX 4070 (o similar)
- Red local (192.168.1.x recomendado)
- Python 3.11+ instalado en ambas máquinas
- Permisos de administrador para configurar firewall

## 🔧 Configuración Paso a Paso

### 1. Preparar Variables de Entorno

```bash
# Copiar template de configuración
cp .env.example .env.local

# Editar con tus valores específicos
# Ejemplo para red 192.168.1.x:
NODE1_IP=192.168.1.XXX  # IP de tu máquina principal
NODE2_IP=192.168.1.YYY  # IP de tu portátil/segunda máquina
```

### 2. Generar Configuración de Genesis

```bash
# Ejecutar script de configuración con tus IPs
python scripts/setup_testnet_genesis.py --node1-ip TU_IP_NODO1 --node2-ip TU_IP_NODO2

# Esto generará:
# - config/testnet/node1.yaml
# - config/testnet/node2.yaml  
# - config/testnet/testnet.yaml
# - wallets/testnet/validator-*.json
# - data/testnet/genesis.json
```

### 3. Configurar Firewall (AMBAS MÁQUINAS)

```bash
# Ejecutar como Administrador en ambas máquinas:
scripts\configurar_firewall_testnet.bat
```

### 4. Iniciar Nodos

#### En la Máquina Principal:
```bash
# Opción A: Script completo (recomendado)
scripts\iniciar_red_testnet_completa.bat

# Opción B: Manual
scripts\start_node1_testnet.bat
```

#### En la Segunda Máquina:
```bash
# Copiar todo el proyecto a la segunda máquina
# Luego ejecutar:
scripts\iniciar_nodo2_portatil.bat

# O manual:
scripts\start_node2_testnet.bat
```

### 5. Verificar Conexión

```bash
# Cargar variables de entorno desde .env.local
python scripts\diagnostico_red_testnet.py
```

## 🎮 Configurar Minería IA

### 1. Abrir Wallets (AMBAS MÁQUINAS)
```bash
cd wallet
.\clear-cache-and-start.bat
```

### 2. Configurar Minería en el Wallet
1. **Ir a pestaña "Minería"**
2. **Descargar modelo IA** (recomendado: Gemma 3 4B)
3. **Seleccionar modelo** descargado
4. **Hacer clic "🚀 Iniciar Minería"**

## 🔍 Verificación de Funcionamiento

### Logs de Nodos Esperados:
```
✅ P2P network started successfully on port 18333
✅ Attempting to connect to 2 bootstrap nodes...
✅ Connected to bootstrap node [IP_OCULTA]:18333
✅ Successfully connected to 1 bootstrap nodes
✅ Stats: 1 peers, 1 connections
```

### En el Wallet:
```
🟢 Red: Conectado (2 peers)
🟢 Minería: Activa con Gemma 3 4B
🟢 Challenges procesados: 25
🟢 Bloques validados: 3
🟢 Recompensas: 45.5 PRGLD
```

## 🔒 Medidas de Seguridad Implementadas

### ✅ Archivos Protegidos (NO se commitean):
- `config/testnet/node*.yaml` - Configuraciones con IPs reales
- `config/testnet/testnet.yaml` - Bootstrap nodes con IPs reales
- `wallets/testnet/validator-*.json` - Wallets con información específica
- `.env.local` - Variables de entorno locales

### ✅ Templates Seguros (SÍ se commitean):
- `config/testnet/*.example.yaml` - Templates con variables
- `wallets/testnet/*.example.json` - Templates de wallets
- `.env.example` - Template de variables de entorno

### ✅ Scripts Seguros:
- Scripts usan variables de entorno en lugar de IPs hardcodeadas
- Documentación sin información sensible específica
- .gitignore actualizado para proteger archivos sensibles

## 🛠️ Troubleshooting

### Si los nodos no se conectan:

1. **Verificar firewall**:
   ```bash
   netsh advfirewall firewall show rule name="PlayerGold Testnet - Entrada"
   ```

2. **Test de conectividad**:
   ```bash
   # Usar las IPs de tu .env.local
   telnet TU_IP_NODO1 18333
   telnet TU_IP_NODO2 18333
   ```

3. **Verificar variables de entorno**:
   ```bash
   # Asegurar que .env.local tiene las IPs correctas
   cat .env.local
   ```

## 🎉 Resultado Final

Con esta configuración segura tendrás:
- ✅ **Red testnet funcional** sin exponer IPs en el repositorio
- ✅ **Configuración reproducible** usando templates y variables
- ✅ **Consenso PoAIP activo** con IAs procesando challenges
- ✅ **Repositorio seguro** sin información sensible

¡Tu red PlayerGold testnet estará lista para pruebas completas de minería IA de forma segura! 🎮⛏️🔒