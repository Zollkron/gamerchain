# 🔧 Configuración de Testnet PlayerGold

## 📋 Configuración Inicial

### 1. Variables de Entorno
```bash
# Copiar template de variables
cp .env.example .env.local

# Editar con tus valores específicos
nano .env.local
```

### 2. Configuración de Nodos
```bash
# Copiar templates de configuración
cp config/testnet/node1.example.yaml config/testnet/node1.yaml
cp config/testnet/node2.example.yaml config/testnet/node2.yaml
cp config/testnet/testnet.example.yaml config/testnet/testnet.yaml

# Editar archivos con tus IPs específicas
```

### 3. Generar Genesis y Validadores
```bash
# Ejecutar script de configuración
python scripts/setup_testnet_genesis.py --node1-ip TU_IP_NODO1 --node2-ip TU_IP_NODO2
```

### 4. Iniciar Nodos
```bash
# Nodo 1
scripts/start_node1_testnet.bat

# Nodo 2 (en otra máquina)
scripts/start_node2_testnet.bat
```

## 🔒 Seguridad

- ❌ **NUNCA** commitear archivos con IPs reales
- ✅ **SIEMPRE** usar templates y variables de entorno
- ✅ **VERIFICAR** .gitignore antes de commit
- ✅ **USAR** .env.local para configuración específica

## 📁 Estructura de Archivos

```
config/testnet/
├── *.example.yaml     # Templates seguros (commitear)
├── *.yaml            # Configuración real (NO commitear)
└── README.md         # Esta documentación

wallets/testnet/
├── *.example.json    # Templates seguros (commitear)  
├── *.json           # Wallets reales (NO commitear)
└── README.md        # Documentación de wallets
```
