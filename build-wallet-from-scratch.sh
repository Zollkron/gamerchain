#!/bin/bash
# PlayerGold Wallet - Build Complete desde Cero
# Este script genera la wallet completa desde cero en cualquier equipo
# Actualizado para usar la estructura dist/ moderna

echo "========================================"
echo "PlayerGold Wallet - Build desde Cero"
echo "========================================"
echo ""
echo "Este script construye la wallet completa desde cero:"
echo "• Instala dependencias"
echo "• Construye la aplicación React"
echo "• Empaqueta con Electron"
echo "• Genera ejecutables listos para usar"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "wallet/package.json" ]; then
    echo "❌ ERROR: No se encuentra wallet/package.json"
    echo "   Ejecuta este script desde la raíz del proyecto PlayerGold"
    exit 1
fi

echo "🔍 Verificando requisitos del sistema..."

# Verificar Node.js
if ! command -v node &> /dev/null; then
    echo "❌ ERROR: Node.js no está instalado"
    echo "   Instala Node.js desde: https://nodejs.org/"
    exit 1
fi

# Verificar npm
if ! command -v npm &> /dev/null; then
    echo "❌ ERROR: npm no está disponible"
    exit 1
fi

echo "✅ Node.js y npm detectados correctamente"
echo "   Node.js version: $(node --version)"
echo "   npm version: $(npm --version)"

# Cambiar al directorio de la wallet
cd wallet

echo ""
echo "🧹 Limpiando builds anteriores..."
rm -rf build dist node_modules/.cache

echo ""
echo "📦 Instalando dependencias de npm..."
echo "   Esto puede tomar varios minutos..."
npm install
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló la instalación de dependencias"
    echo "   Intenta ejecutar: npm install --force"
    exit 1
fi

echo ""
echo "✅ Dependencias instaladas correctamente"

echo ""
echo "🔧 Construyendo aplicación React..."
npm run build
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló la construcción de React"
    echo "   Revisa los errores anteriores"
    exit 1
fi

echo ""
echo "✅ Aplicación React construida correctamente"

echo ""
echo "📱 Empaquetando con Electron Builder..."
echo "   Esto puede tomar varios minutos..."
npm run electron-build
if [ $? -ne 0 ]; then
    echo "❌ ERROR: Falló el empaquetado con Electron"
    echo "   Revisa los errores anteriores"
    exit 1
fi

echo ""
echo "✅ Empaquetado completado exitosamente"

# Volver al directorio raíz
cd ..

echo ""
echo "🔍 Verificando archivos generados..."

# Detectar sistema operativo y verificar archivos correspondientes
OS=$(uname -s)
case $OS in
    "Darwin")
        if [ -d "wallet/dist/mac/PlayerGold Wallet.app" ]; then
            echo "✅ Aplicación macOS: wallet/dist/mac/PlayerGold Wallet.app"
        else
            echo "❌ No se encontró la aplicación para macOS"
        fi
        ;;
    "Linux")
        if [ -f "wallet/dist/PlayerGold-Wallet-1.0.0.AppImage" ]; then
            echo "✅ AppImage Linux: wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        else
            echo "❌ No se encontró el AppImage para Linux"
        fi
        ;;
    *)
        echo "⚠️ Sistema operativo no reconocido: $OS"
        ;;
esac

echo ""
echo "========================================"
echo "✅ BUILD COMPLETADO EXITOSAMENTE"
echo "========================================"

echo ""
echo "📋 Archivos generados:"
echo ""

case $OS in
    "Darwin")
        echo "🚀 APLICACIÓN macOS:"
        echo "   📁 wallet/dist/mac/PlayerGold Wallet.app"
        echo "   • Ejecutar haciendo doble clic"
        echo "   • Puede requerir permisos de seguridad"
        ;;
    "Linux")
        echo "🚀 APPIMAGE LINUX:"
        echo "   📁 wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        echo "   • Hacer ejecutable: chmod +x wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        echo "   • Ejecutar: ./wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        ;;
esac

echo ""
echo "🔐 CERTIFICADO AES:"
if [ -f "wallet/.AES_certificate/master_key.bin" ]; then
    echo "   ✅ Certificado AES encontrado: wallet/.AES_certificate/"
    echo "   • La wallet puede conectar al coordinador"
    echo "   • Comunicación cifrada habilitada"
else
    echo "   ❌ Certificado AES NO encontrado"
    echo "   • Para habilitar comunicación con coordinador:"
    echo "   • 1. Ejecutar en servidor: sudo python3 scripts/setup_coordinator_aes_certificate.py"
    echo "   • 2. Descargar paquete del servidor"
    echo "   • 3. Ejecutar: python3 scripts/install_wallet_aes_certificate.py [paquete]"
fi

echo ""
echo "💡 PRÓXIMOS PASOS:"
echo ""

case $OS in
    "Darwin")
        echo "1. PARA EJECUTAR:"
        echo "   • Abrir: wallet/dist/mac/PlayerGold Wallet.app"
        echo "   • Si aparece advertencia de seguridad:"
        echo "     - Ir a Preferencias del Sistema > Seguridad y Privacidad"
        echo "     - Permitir la aplicación"
        ;;
    "Linux")
        echo "1. PARA EJECUTAR:"
        echo "   • chmod +x wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        echo "   • ./wallet/dist/PlayerGold-Wallet-1.0.0.AppImage"
        ;;
esac

echo ""
echo "2. PARA HABILITAR COORDINADOR (Opcional):"
echo "   • Copiar certificado AES desde otro equipo"
echo "   • O generar nuevo certificado en servidor"
echo ""

echo "🎯 FUNCIONALIDADES INCLUIDAS:"
echo "   • Gestión completa de wallets"
echo "   • Transacciones seguras"
echo "   • Integración con blockchain"
echo "   • Conexión automática al coordinador (con certificado)"
echo "   • Descubrimiento automático de peers"
echo "   • Interfaz moderna y fácil de usar"
echo ""

echo "✅ ¡Wallet lista para usar!"
echo ""