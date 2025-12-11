#!/usr/bin/env python3
"""
Script para aplicar medidas de seguridad al repositorio PlayerGold
Elimina información sensible como IPs privadas, configuraciones específicas, etc.
"""

import os
import shutil
import re
from pathlib import Path
import json
import yaml

def print_header(titulo):
    """Imprimir encabezado de sección"""
    print(f"\n{'='*60}")
    print(f"🔒 {titulo}")
    print(f"{'='*60}")

def print_action(accion, resultado=True):
    """Imprimir resultado de acción"""
    icono = "✅" if resultado else "❌"
    print(f"{icono} {accion}")

def actualizar_gitignore():
    """Actualizar .gitignore con archivos sensibles"""
    print_header("ACTUALIZANDO .GITIGNORE")
    
    gitignore_path = Path(".gitignore")
    
    # Leer .gitignore actual
    if gitignore_path.exists():
        with open(gitignore_path, 'r', encoding='utf-8') as f:
            content = f.read()
    else:
        content = ""
    
    # Nuevas reglas de seguridad
    security_rules = """
# PlayerGold Security - Información Sensible
# ==========================================

# Configuraciones específicas de testnet con IPs privadas
config/testnet/node*.yaml
config/testnet/testnet.yaml
!config/testnet/*.example.yaml

# Wallets de validadores con información específica
wallets/testnet/validator-*.json
!wallets/testnet/*.example.json

# Datos de blockchain específicos
data/testnet/
data/mainnet/
!data/testnet/.gitkeep
!data/mainnet/.gitkeep

# Logs que pueden contener IPs
logs/
*.log

# Archivos de configuración local
.env.local
config.local.yaml
testnet.local.yaml

# Certificados y claves
*.pem
*.key
*.crt
*.p12
*.pfx

# Backups que pueden contener información sensible
*.backup
*.bak
backup/

# Archivos temporales de desarrollo
temp/
tmp/
.temp/
"""
    
    # Verificar si ya están las reglas
    if "# PlayerGold Security" not in content:
        content += security_rules
        
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print_action("Reglas de seguridad agregadas a .gitignore")
    else:
        print_action("Reglas de seguridad ya existen en .gitignore")

def crear_templates_configuracion():
    """Crear archivos template para configuraciones sensibles"""
    print_header("CREANDO TEMPLATES DE CONFIGURACIÓN")
    
    templates = {
        'config/testnet/node1.example.yaml': {
            'consensus': {
                'min_validators': 2,
                'quorum_percentage': 0.66,
                'type': 'PoAIP'
            },
            'genesis_file': '../genesis.json',
            'network': {
                'bootstrap_nodes': [
                    '${NODE1_IP}:18333',
                    '${NODE2_IP}:18333'
                ],
                'external_ip': '${NODE1_IP}',
                'listen_ip': '0.0.0.0',
                'listen_port': 18333,
                'network_id': 'playergold-testnet-genesis',
                'network_type': 'testnet'
            },
            'node': {
                'data_dir': './data/testnet/node1',
                'is_validator': True,
                'node_id': 'validator-node-1',
                'validator_address': '${NODE1_VALIDATOR_ADDRESS}'
            }
        },
        
        'config/testnet/node2.example.yaml': {
            'consensus': {
                'min_validators': 2,
                'quorum_percentage': 0.66,
                'type': 'PoAIP'
            },
            'genesis_file': '../genesis.json',
            'network': {
                'bootstrap_nodes': [
                    '${NODE1_IP}:18333',
                    '${NODE2_IP}:18333'
                ],
                'external_ip': '${NODE2_IP}',
                'listen_ip': '0.0.0.0',
                'listen_port': 18333,
                'network_id': 'playergold-testnet-genesis',
                'network_type': 'testnet'
            },
            'node': {
                'data_dir': './data/testnet/node2',
                'is_validator': True,
                'node_id': 'validator-node-2',
                'validator_address': '${NODE2_VALIDATOR_ADDRESS}'
            }
        },
        
        'config/testnet/testnet.example.yaml': {
            'block_time': 10,
            'consensus': {
                'min_validators': 2,
                'quorum_percentage': 0.66,
                'type': 'PoAIP'
            },
            'faucet_amount': 1000,
            'genesis_time': '${GENESIS_TIME}',
            'initial_supply': 1000000,
            'initial_validators': [
                {
                    'address': '${NODE1_VALIDATOR_ADDRESS}',
                    'created_at': '${GENESIS_TIME}',
                    'ip_address': '${NODE1_IP}',
                    'is_genesis_validator': True,
                    'node_name': 'validator-node-1',
                    'port': 18333,
                    'public_key': '${NODE1_PUBLIC_KEY}',
                    'stake': 100000
                },
                {
                    'address': '${NODE2_VALIDATOR_ADDRESS}',
                    'created_at': '${GENESIS_TIME}',
                    'ip_address': '${NODE2_IP}',
                    'is_genesis_validator': True,
                    'node_name': 'validator-node-2',
                    'port': 18333,
                    'public_key': '${NODE2_PUBLIC_KEY}',
                    'stake': 100000
                }
            ],
            'network_id': 'playergold-testnet-genesis',
            'bootstrap_nodes': [
                '${NODE1_IP}:18333',
                '${NODE2_IP}:18333'
            ]
        }
    }
    
    # Crear templates
    for template_path, template_content in templates.items():
        template_file = Path(template_path)
        template_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(template_file, 'w', encoding='utf-8') as f:
            yaml.dump(template_content, f, default_flow_style=False, allow_unicode=True)
        
        print_action(f"Template creado: {template_path}")
    
    # Crear template de wallet
    wallet_template = {
        "created_at": "${CREATION_TIME}",
        "node_name": "${NODE_NAME}",
        "address": "${VALIDATOR_ADDRESS}",
        "ip_address": "${NODE_IP}",
        "port": 18333,
        "stake": 100000,
        "public_key": "${PUBLIC_KEY}",
        "private_key_encrypted": "${ENCRYPTED_PRIVATE_KEY}",
        "is_genesis_validator": True
    }
    
    wallet_template_path = Path("wallets/testnet/validator-node.example.json")
    wallet_template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(wallet_template_path, 'w', encoding='utf-8') as f:
        json.dump(wallet_template, f, indent=2)
    
    print_action("Template de wallet creado: wallets/testnet/validator-node.example.json")

def limpiar_scripts_desarrollo():
    """Limpiar scripts de desarrollo reemplazando IPs por variables"""
    print_header("LIMPIANDO SCRIPTS DE DESARROLLO")
    
    scripts_a_limpiar = [
        'scripts/diagnostico_red_testnet.py',
        'scripts/verificar_conexion_nodos.py'
    ]
    
    for script_path in scripts_a_limpiar:
        if Path(script_path).exists():
            with open(script_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Reemplazar IPs específicas por variables de entorno
            content = re.sub(r"'ip': '192\.168\.1\.129'", "'ip': os.getenv('NODE1_IP', '192.168.1.100')", content)
            content = re.sub(r"'ip': '192\.168\.1\.132'", "'ip': os.getenv('NODE2_IP', '192.168.1.101')", content)
            content = re.sub(r'"192\.168\.1\.129"', 'os.getenv("NODE1_IP", "192.168.1.100")', content)
            content = re.sub(r'"192\.168\.1\.132"', 'os.getenv("NODE2_IP", "192.168.1.101")', content)
            
            # Agregar import os si no existe
            if 'import os' not in content and 'os.getenv' in content:
                content = 'import os\n' + content
            
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print_action(f"Script limpiado: {script_path}")

def crear_archivo_env_example():
    """Crear archivo .env.example con variables de configuración"""
    print_header("CREANDO ARCHIVO DE VARIABLES DE ENTORNO")
    
    env_example_content = """# PlayerGold Testnet Configuration
# Copia este archivo a .env.local y configura tus valores específicos

# IPs de los nodos (ajustar según tu red local)
NODE1_IP=192.168.1.100
NODE2_IP=192.168.1.101

# Direcciones de validadores (generar con setup_testnet_genesis.py)
NODE1_VALIDATOR_ADDRESS=PGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NODE2_VALIDATOR_ADDRESS=PGxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Claves públicas de validadores
NODE1_PUBLIC_KEY=pub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NODE2_PUBLIC_KEY=pub_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Configuración de red
NETWORK_ID=playergold-testnet-genesis
P2P_PORT=18333
API_PORT=18080

# Configuración de genesis
GENESIS_TIME=2025-01-01T00:00:00.000000
INITIAL_SUPPLY=1000000
VALIDATOR_STAKE=100000

# Configuración de minería
CHALLENGE_TIMEOUT=0.3
MIN_VALIDATORS=2
"""
    
    with open('.env.example', 'w', encoding='utf-8') as f:
        f.write(env_example_content)
    
    print_action("Archivo .env.example creado")

def crear_documentacion_segura():
    """Crear documentación sin información sensible"""
    print_header("CREANDO DOCUMENTACIÓN SEGURA")
    
    # Crear README de configuración
    config_readme = """# 🔧 Configuración de Testnet PlayerGold

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
"""
    
    config_readme_path = Path("config/testnet/README.md")
    config_readme_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_readme_path, 'w', encoding='utf-8') as f:
        f.write(config_readme)
    
    print_action("README de configuración creado: config/testnet/README.md")

def crear_gitkeep_files():
    """Crear archivos .gitkeep para mantener estructura de directorios"""
    print_header("CREANDO ARCHIVOS .GITKEEP")
    
    directories = [
        'data/testnet',
        'data/mainnet',
        'logs',
        'wallets/testnet',
        'wallets/mainnet'
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = dir_path / '.gitkeep'
        gitkeep_path.touch()
        
        print_action(f".gitkeep creado en: {directory}")

def main():
    """Función principal"""
    print_header("APLICANDO SEGURIDAD AL REPOSITORIO PLAYERGOLD")
    print("⚠️  Este script eliminará información sensible del repositorio")
    print("📋 Creará templates y configuraciones seguras")
    print()
    
    respuesta = input("¿Continuar? (s/N): ").lower().strip()
    if respuesta != 's':
        print("❌ Operación cancelada")
        return
    
    try:
        # 1. Actualizar .gitignore
        actualizar_gitignore()
        
        # 2. Crear templates
        crear_templates_configuracion()
        
        # 3. Limpiar scripts
        limpiar_scripts_desarrollo()
        
        # 4. Crear .env.example
        crear_archivo_env_example()
        
        # 5. Crear documentación segura
        crear_documentacion_segura()
        
        # 6. Crear .gitkeep files
        crear_gitkeep_files()
        
        print_header("RESUMEN DE SEGURIDAD")
        print("✅ .gitignore actualizado con reglas de seguridad")
        print("✅ Templates de configuración creados")
        print("✅ Scripts limpiados (IPs → variables de entorno)")
        print("✅ .env.example creado")
        print("✅ Documentación segura generada")
        print("✅ Estructura de directorios preservada")
        
        print("\n🔒 PRÓXIMOS PASOS:")
        print("1. Revisar archivos modificados")
        print("2. Configurar .env.local con tus valores específicos")
        print("3. Generar configuraciones reales desde templates")
        print("4. Verificar que archivos sensibles no se commiteen")
        
        print("\n⚠️  IMPORTANTE:")
        print("- Los archivos con información sensible seguirán existiendo localmente")
        print("- Pero ahora están en .gitignore y no se commitearán")
        print("- Usa los templates para generar nuevas configuraciones")
        
    except Exception as e:
        print(f"❌ Error aplicando seguridad: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)